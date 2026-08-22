"""对话路由（SSE 流式）— Agent 核心入口

v0.3.0：
- 真流式：LangGraph custom stream 增量转发 LLM token（不再切块模拟）
- 判题闭环：加载上一轮待作答的 quiz / review，判分后回写并按结果重排 FSRS 卡片
- 学习卡片去重：同一概念只建一张复习卡

集成开源组件：
- LangGraph Checkpointer：自动管理对话历史
- fsrs 包：间隔重复，按作答质量（正确→3 / 错误→1）调度下次复习时间
- E2B：代码沙箱执行学生代码
- Qdrant：知识库 RAG 检索
- Mem0：长期记忆存储和检索
"""
import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select

from app.database import get_db, async_session
from app.deps import get_current_user
from app.models import User, Session, Message, StudentProfile, ReviewItem
from app.agents import graph as graph_module
from app.config import settings
from app.ratelimit import SlidingWindowLimiter, build_limiter
from app.tools.tracing import new_trace_id, session_id_var, trace_id_var

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])

# 每用户限流：默认 20 次/分钟（REDIS_URL 配置时为跨 worker 分布式计数）
chat_limiter = build_limiter(
    max_events=settings.RATE_LIMIT_CHAT_PER_MIN, window_seconds=60.0,
)


class ChatRequest(BaseModel):
    message: str
    session_id: int | None = None
    # 幂等键：客户端为每次发送生成唯一 ID；同键重复请求不重复入库、直接回放上次回复
    request_id: str | None = None


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post("/chat")
async def chat(
    req: ChatRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """SSE 流式对话

    对话历史由 LangGraph Checkpointer 管理；LLM 输出通过 custom stream 实时增量推送。
    """
    # 限流（按用户）
    if not await chat_limiter.allow(f"user:{user.id}"):
        retry_after = await chat_limiter.retry_after_seconds(f"user:{user.id}")
        raise HTTPException(
            status_code=429,
            detail="请求过于频繁，请稍后再试",
            headers={"Retry-After": str(int(retry_after) + 1)},
        )

    # 获取或创建会话
    if req.session_id:
        result = await db.execute(
            select(Session).where(Session.id == req.session_id, Session.user_id == user.id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")

        # 幂等检查：同 request_id 的重复请求直接回放上次回复，不再入库/再跑 Agent
        if req.request_id:
            replay = await find_duplicate_request(db, session.id, req.request_id)
            if replay is not None:
                return replay_response(session.id, replay)
    else:
        # 首条消息截断作为会话标题（ChatGPT 式自动命名）
        auto_title = " ".join(req.message.split())[:30]
        session = Session(user_id=user.id, summary=auto_title or None)
        db.add(session)
        await db.flush()

    # 保存用户消息（给前端展示用，Agent 历史由 checkpointer 管）
    user_metadata = {"request_id": req.request_id} if req.request_id else {}
    db.add(Message(
        session_id=session.id,
        role="user",
        content=req.message,
        metadata_=user_metadata,
    ))
    await db.commit()

    # 获取学生画像
    profile_result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user.id)
    )
    profile = profile_result.scalar_one_or_none()
    profile_dict = {
        "current_level": profile.current_level if profile else "beginner",
        "learning_goal": profile.learning_goal or "" if profile else "",
    }

    # 查询到期的 FSRS 复习项
    now = datetime.now()
    review_result = await db.execute(
        select(ReviewItem)
        .where(ReviewItem.user_id == user.id, ReviewItem.due <= now)
        .order_by(ReviewItem.due)
        .limit(3)
    )
    review_items = [
        {"concept": r.concept, "card_data": r.card_data, "id": r.id}
        for r in review_result.scalars().all()
    ]

    # 加载上一轮留下的待作答内容（判题闭环的入口）
    pending_quiz, pending_review = await load_pending_context(db, session.id)

    initial_state = {
        "user_message": req.message,
        "user_id": user.id,
        "session_id": session.id,
        "student_profile": profile_dict,
        "review_items": review_items,
        "pending_quiz": pending_quiz,
        "pending_review": pending_review,
    }
    config = {"configurable": {"thread_id": str(session.id)}}

    # 追踪上下文：本次请求的所有 LLM span 关联到同一 trace
    trace_id_var.set(new_trace_id())
    session_id_var.set(session.id)

    async def event_stream():
        # 发送状态提示
        yield _sse({"type": "status", "content": "Agent 正在思考..."})

        final_state: dict = {}
        try:
            # 真流式：custom channel 推增量 token，updates channel 汇总各节点产出
            async for mode, payload in graph_module.agent_graph.astream(
                initial_state,
                config=config,
                stream_mode=["custom", "updates"],
            ):
                if mode == "custom":
                    if isinstance(payload, str) and payload:
                        yield _sse({"type": "stream", "content": payload})
                elif mode == "updates" and isinstance(payload, dict):
                    for delta in payload.values():
                        if isinstance(delta, dict):
                            final_state.update(delta)
        except Exception:
            logger.exception("Agent 执行失败 session=%s", session.id)

        reply_chunks = final_state.get("response_chunks") or []
        reply_text = "".join(reply_chunks) or "抱歉，我暂时无法回复，请稍后重试。"

        judged_summary: dict | None = None
        quiz_payload = final_state.get("quiz_question")
        code_payload = final_state.get("code_result")
        judge_result = final_state.get("judge_result") or {}
        review_item_id = final_state.get("review_item_id")

        # 判题 / 记忆卡重排 / 新卡片创建 — 全部落库后再发 complete
        async with async_session() as db2:
            metadata: dict = {
                "intent": final_state.get("intent"),
                "action_plan": final_state.get("action_plan"),
            }
            if quiz_payload:
                metadata["quiz"] = {
                    **quiz_payload,
                    "answered": False,
                    "concept": req.message[:100],
                }
            if code_payload:
                metadata["code_result"] = code_payload
            if judge_result.get("mode"):
                judged_payload: dict = {
                    "mode": judge_result.get("mode"),
                    "correct": bool(judge_result.get("correct")),
                }
                if judge_result.get("mode") == "quiz":
                    # 选择题带上所选与正确索引，前端回显对错高亮
                    judged_payload["selected"] = judge_result.get("selected")
                    judged_payload["answer"] = judge_result.get("answer")
                metadata["judged"] = judged_payload
                judged_summary = dict(judged_payload)
                judge_concept = (
                    (pending_review or {}).get("concept")
                    or (pending_quiz or {}).get("concept")
                    or ""
                )
                await update_profile_on_judge(
                    db2, user.id, bool(judge_result.get("correct")), judge_concept
                )
            if review_item_id:
                metadata["review_item_id"] = review_item_id
                metadata["review_concept"] = next(
                    (r["concept"] for r in review_items if r.get("id") == review_item_id),
                    "",
                )
                metadata["review_answered"] = False

            db2.add(Message(
                session_id=session.id,
                role="assistant",
                content=reply_text,
                metadata_=metadata,
            ))

            # 判题发生时：把上一轮待作答消息标记为已作答，并按质量重排 FSRS 卡片
            prev_message_id = (
                (pending_quiz or {}).get("_message_id")
                or (pending_review or {}).get("message_id")
            )
            if judge_result.get("mode") and prev_message_id:
                prev_result = await db2.execute(
                    select(Message).where(Message.id == prev_message_id)
                )
                prev_msg = prev_result.scalar_one_or_none()
                if prev_msg and prev_msg.metadata_:
                    updated = dict(prev_msg.metadata_)
                    updated["answered"] = True
                    updated["review_answered"] = True
                    prev_msg.metadata_ = updated

            await apply_fsrs_reschedule(db2, user.id, judge_result)

            # 学生学了新概念 → 创建复习卡（同一概念只建一张）
            if (final_state.get("intent") == "learn_concept"
                    and final_state.get("teach_content")):
                await create_review_card_once(
                    db2, user.id, req.message[:200]
                )

            fresh_session = await db2.get(Session, session.id)
            if fresh_session is not None:
                fresh_session.ended_at = datetime.now()
                # 旧会话无标题时用首条消息补齐（重命名过的不动）
                if not fresh_session.summary:
                    fresh_session.summary = " ".join(req.message.split())[:30] or None
            await db2.commit()

        # 发送完整数据（包含 quiz/code/judged 等结构化数据）
        complete_data: dict = {
            "type": "complete",
            "content": reply_text,
            "session_id": session.id,
        }
        if quiz_payload:
            complete_data["quiz"] = quiz_payload
        if code_payload:
            complete_data["code_result"] = code_payload
        if judged_summary:
            complete_data["judged"] = judged_summary
        yield _sse(complete_data)
        yield "data: [done]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Session-Id": str(session.id),
        },
    )


# ── 辅助函数 ──────────────────────────────────────────────


async def find_duplicate_request(db, session_id: int, request_id: str) -> str | None:
    """按幂等键查重：返回上次回复内容（无重复则 None）"""
    result = await db.execute(
        select(Message)
        .where(
            Message.session_id == session_id,
            Message.role == "user",
            Message.metadata_["request_id"].as_string() == request_id,
        )
        .limit(1)
    )
    user_msg = result.scalar_one_or_none()
    if not user_msg:
        return None

    reply_result = await db.execute(
        select(Message)
        .where(
            Message.session_id == session_id,
            Message.role == "assistant",
            Message.id > user_msg.id,
        )
        .order_by(Message.id.asc())
        .limit(1)
    )
    reply = reply_result.scalar_one_or_none()
    return reply.content if reply else ""


def replay_response(session_id: int, content: str) -> StreamingResponse:
    """幂等命中：回放上次回复，不产生任何新数据"""

    async def replay_stream():
        yield _sse({"type": "status", "content": "重复请求，已回放上次回复"})
        yield _sse({
            "type": "complete",
            "content": content,
            "session_id": session_id,
            "duplicate": True,
        })
        yield "data: [done]\n\n"

    return StreamingResponse(
        replay_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Session-Id": str(session_id)},
    )


async def load_pending_context(db, session_id: int) -> tuple[dict, dict]:
    """读取该会话最后一条助手消息，还原待作答的 quiz / review。

    返回 (pending_quiz, pending_review)，两者互斥、最多一个生效。
    """
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id, Message.role == "assistant")
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(1)
    )
    last_msg = result.scalar_one_or_none()
    if not last_msg or not last_msg.metadata_:
        return {}, {}

    md = last_msg.metadata_
    quiz = md.get("quiz")
    if isinstance(quiz, dict) and quiz.get("question") and not md.get("answered"):
        return {**quiz, "_message_id": last_msg.id}, {}

    if md.get("review_item_id") and not md.get("review_answered"):
        return {}, {
            "item_id": md["review_item_id"],
            "concept": md.get("review_concept", ""),
            "message_id": last_msg.id,
        }
    return {}, {}


async def update_profile_on_judge(db, user_id: int, correct: bool, concept: str) -> None:
    """判题结果回写学生画像：掌握的概念进 strengths，薄弱概念进 weaknesses（各留最近 20 条）"""
    if not concept:
        return

    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        return

    field = "strengths" if correct else "weaknesses"
    items = list(getattr(profile, field) or [])
    if concept in items:
        return
    items.append(concept)
    setattr(profile, field, items[-20:])


def _naive_due(card_due) -> datetime:
    """fsrs 返回的 due 可能带时区；入库统一剥离为 naive datetime"""
    if hasattr(card_due, "tzinfo") and card_due.tzinfo:
        return card_due.replace(tzinfo=None)
    return card_due


async def apply_fsrs_reschedule(db, user_id: int, judge_result: dict) -> None:
    """按判题结果重排 FSRS 卡片的下次到期时间"""
    item_id = judge_result.get("item_id")
    rating = judge_result.get("rating")
    if not item_id or rating not in (1, 3):
        return

    result = await db.execute(
        select(ReviewItem)
        .where(ReviewItem.id == int(item_id), ReviewItem.user_id == user_id)
    )
    item = result.scalar_one_or_none()
    if not item or not item.card_data:
        return

    try:
        from fsrs import Card, Scheduler

        scheduler = Scheduler()
        card = Card.from_dict(item.card_data)
        card, _ = scheduler.review_card(card, rating=int(rating))
        item.card_data = card.to_dict()
        item.due = _naive_due(card.due)
    except Exception:
        logger.warning("FSRS 卡片重排失败 item=%s", item_id, exc_info=True)


async def create_review_card_once(db, user_id: int, concept: str) -> None:
    """为新学的概念创建间隔重复卡片；已有同名概念时跳过"""
    existing = await db.execute(
        select(ReviewItem)
        .where(ReviewItem.user_id == user_id, ReviewItem.concept == concept)
        .limit(1)
    )
    if existing.scalar_one_or_none() is not None:
        return

    try:
        from fsrs import Card, Scheduler

        scheduler = Scheduler()
        card = Card()
        card, _ = scheduler.review_card(card, rating=3)

        db.add(ReviewItem(
            user_id=user_id,
            concept=concept,
            card_data=card.to_dict(),
            due=_naive_due(card.due),
        ))
    except Exception:
        logger.warning("复习卡片创建失败 concept=%s", concept, exc_info=True)
