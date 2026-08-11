"""
EduFlow Review(间隔重复复习)路由

业务逻辑：
- 练习完成后自动为「模块主题 + 薄弱点」生成/更新复习项，调用 Engine 计算下次复习时间(FSRS 启发式)。
- 引擎不可用时降级为内置简单排期，保证功能不中断。
- 用户可在复习页按 due_at 排期完成复习，每完成一次按得分更新掌握度并重新排期。
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.deps import get_current_user
from models.user import User
from models.learning import ReviewItem

router = APIRouter(prefix="/api/review", tags=["review"])

ENGINE_TIMEOUT = 10.0


# ---------------------------------------------------------------------------
# 请求模型
# ---------------------------------------------------------------------------

class ReviewSubmit(BaseModel):
    score: float  # 0-100


class ReviewItemOut(BaseModel):
    id: int
    module_id: Optional[int] = None
    topic: str
    mastery_level: float
    review_count: int
    last_score: Optional[float] = None
    stability: float
    difficulty: float
    due_at: Optional[str] = None
    last_reviewed_at: Optional[str] = None
    status: str = "due"  # due / upcoming / reviewed


# ---------------------------------------------------------------------------
# Engine 排期(带降级)
# ---------------------------------------------------------------------------

def _iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


def _as_aware_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """将存储的 datetime 统一为 UTC-aware(处理 SQLite 返回的 naive 值)。"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


async def _engine_next_review(
    topic: str,
    mastery: float,
    review_count: int,
    last_score: Optional[float],
    hours_since_last: float,
) -> dict:
    """调用 Engine 计算下一次复习；失败时返回内置简单排期。"""
    payload = {
        "knowledge_state": {
            "topic": topic,
            "mastery_level": mastery,
            "review_count": review_count,
            "last_review_score": last_score,
            "time_since_last_review_hours": hours_since_last,
        },
        "desired_retention": 0.9,
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.ENGINE_SERVICE_URL}/api/engine/next-review",
                json=payload,
                timeout=ENGINE_TIMEOUT,
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "next_review_hours": float(data.get("next_review_hours", 24)),
                    "stability": float(data.get("stability", 1.0)),
                    "difficulty": float(data.get("difficulty", 0.5)),
                }
    except (httpx.ConnectError, httpx.TimeoutException):
        pass
    # 降级：简单间隔重复
    hours = min(24 * 90, max(2, (review_count + 1) * 24 * 1.5))
    stability = max(1.0, (review_count + 1) * 1.5)
    return {"next_review_hours": hours, "stability": stability, "difficulty": 1.0 - mastery}


def _update_mastery(current: float, score: float, is_strong: bool = False) -> float:
    """按最近得分更新掌握度(0-1)。答对上升、答错下降。"""
    normalized = score / 100.0
    if is_strong:
        return min(1.0, max(0.0, current + 0.15 + normalized * 0.05))
    if normalized >= 0.6:  # 及格视为掌握
        return min(1.0, max(0.0, current + 0.1 * normalized))
    # 未及格：显著下降
    return max(0.0, current - 0.15)


async def _upsert_review(
    db: AsyncSession,
    user_id: int,
    topic: str,
    module_id: Optional[int],
    score: float,
    is_strong: bool = False,
) -> ReviewItem:
    """按 (user_id, topic) 创建或更新复习项。"""
    result = await db.execute(
        select(ReviewItem).where(ReviewItem.user_id == user_id, ReviewItem.topic == topic)
    )
    item = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    is_new = item is None

    if item is None:
        item = ReviewItem(
            user_id=user_id,
            module_id=module_id,
            topic=topic,
            mastery_level=_update_mastery(0.0, score, is_strong),
            review_count=0,
            last_score=score,
            stability=1.0,
            difficulty=0.5,
            due_at=now,
            last_reviewed_at=now,
        )
        db.add(item)
        await db.flush()

    # 计算距上次复习的小时数(用于 engine 的记忆衰减)
    hours_since = 0.0
    last_ts = _as_aware_utc(item.last_reviewed_at)
    if last_ts:
        hours_since = max(0.0, (now - last_ts).total_seconds() / 3600.0)

    item.mastery_level = _update_mastery(item.mastery_level or 0.0, score, is_strong)
    if not is_new:
        # 仅「重复练习同一主题」时累加复习次数；首次创建不计入
        item.review_count = (item.review_count or 0) + 1
    item.last_score = score
    item.last_reviewed_at = now

    sched = await _engine_next_review(
        topic,
        item.mastery_level,
        item.review_count,
        score,
        hours_since,
    )
    item.stability = sched["stability"]
    item.difficulty = sched["difficulty"]
    item.due_at = now + timedelta(hours=sched["next_review_hours"])

    await db.flush()
    return item


async def schedule_reviews_after_practice(
    db: AsyncSession,
    user_id: int,
    module_title: Optional[str],
    module_id: Optional[int],
    score: float,
    weak_points: Optional[List[str]] = None,
) -> List[ReviewItem]:
    """练习完成后调用：为主题 + 薄弱点生成/更新复习项(尽力而为，不抛异常)。"""
    items: List[ReviewItem] = []
    try:
        if module_title:
            passed = score >= settings.PASS_SCORE_THRESHOLD
            items.append(
                await _upsert_review(db, user_id, module_title, module_id, score, is_strong=passed)
            )
        for wp in weak_points or []:
            wp = (wp or "").strip()
            if wp:
                items.append(await _upsert_review(db, user_id, wp, module_id, score, is_strong=False))
        await db.flush()
    except Exception:
        # 复习排期是增强功能，失败不应影响主流程
        await db.rollback()
        return []
    return items


# ---------------------------------------------------------------------------
# 端点
# ---------------------------------------------------------------------------

def _to_out(item: ReviewItem, now: datetime) -> ReviewItemOut:
    due = _as_aware_utc(item.due_at)
    if due is None:
        status_label = "due"
    elif due <= now:
        status_label = "due"
    else:
        status_label = "upcoming"
    return ReviewItemOut(
        id=item.id,
        module_id=item.module_id,
        topic=item.topic,
        mastery_level=round(item.mastery_level or 0.0, 2),
        review_count=item.review_count or 0,
        last_score=item.last_score,
        stability=round(item.stability or 1.0, 2),
        difficulty=round(item.difficulty or 0.5, 2),
        due_at=_iso(item.due_at),
        last_reviewed_at=_iso(item.last_reviewed_at),
        status=status_label,
    )


@router.get("/due")
async def list_due(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """待复习列表：due_at <= now 的复习项 + 今日/总览统计。"""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(ReviewItem).where(ReviewItem.user_id == current_user.id).order_by(ReviewItem.due_at)
    )
    items = result.scalars().all()
    due = [i for i in items if _as_aware_utc(i.due_at) is not None and _as_aware_utc(i.due_at) <= now]
    upcoming = [i for i in items if _as_aware_utc(i.due_at) is not None and _as_aware_utc(i.due_at) > now]
    return {
        "due_count": len(due),
        "upcoming_count": len(upcoming),
        "total": len(items),
        "due_items": [_to_out(i, now) for i in due],
        "upcoming_items": [_to_out(i, now) for i in upcoming[:10]],
    }


@router.get("/")
async def list_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(ReviewItem).where(ReviewItem.user_id == current_user.id).order_by(ReviewItem.due_at)
    )
    items = result.scalars().all()
    return {"items": [_to_out(i, now) for i in items]}


@router.post("/{review_id}/review")
async def submit_review(
    review_id: int,
    req: ReviewSubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """完成一次复习：按得分更新掌握度并重新排期。"""
    if not (0 <= req.score <= 100):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="得分需在 0-100 之间")
    result = await db.execute(
        select(ReviewItem).where(ReviewItem.id == review_id, ReviewItem.user_id == current_user.id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="复习项不存在")

    now = datetime.now(timezone.utc)
    hours_since = 0.0
    last_ts = _as_aware_utc(item.last_reviewed_at)
    if last_ts:
        hours_since = max(0.0, (now - last_ts).total_seconds() / 3600.0)

    item.mastery_level = _update_mastery(item.mastery_level or 0.0, req.score)
    item.review_count = (item.review_count or 0) + 1
    item.last_score = req.score
    item.last_reviewed_at = now

    sched = await _engine_next_review(
        item.topic, item.mastery_level, item.review_count, req.score, hours_since
    )
    item.stability = sched["stability"]
    item.difficulty = sched["difficulty"]
    item.due_at = now + timedelta(hours=sched["next_review_hours"])

    await db.commit()
    await db.refresh(item)
    return _to_out(item, now)
