"""
EduFlow Engine 网关路由

将学习引擎(FSRS 知识追踪 / 间隔重复 / 时长估算)暴露为带鉴权的 API，
使前端与其它服务能够通过统一入口调用，不再与引擎服务隔离。
引擎不可用时返回 503，调用方应优雅降级。
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import httpx

from core.config import settings
from core.deps import get_current_user
from models.user import User

router = APIRouter(prefix="/api/engine", tags=["engine"])

ENGINE_TIMEOUT = 30.0


class KnowledgeState(BaseModel):
    topic: str
    mastery_level: float = 0.0
    review_count: int = 0
    last_review_score: Optional[float] = None
    time_since_last_review_hours: float = 0.0


class ReviewRequest(BaseModel):
    knowledge_state: KnowledgeState
    desired_retention: float = 0.9


class ReviewBatchRequest(BaseModel):
    states: List[KnowledgeState]
    desired_retention: float = 0.9


class DurationRequest(BaseModel):
    topic: str
    difficulty: str = "medium"
    depth: str = "standard"


async def _proxy_engine(path: str, payload: dict) -> dict:
    """向引擎服务转发请求，处理超时与连接错误。"""
    url = f"{settings.ENGINE_SERVICE_URL}{path}"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, timeout=ENGINE_TIMEOUT)
        except httpx.ConnectError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Engine service unavailable",
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Engine service request timed out",
            )

    if resp.status_code >= 400:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Engine service error: {resp.text}",
        )
    try:
        return resp.json()
    except Exception:
        return {"raw": resp.text}


@router.post("/next-review")
async def next_review(
    req: ReviewRequest,
    current_user: User = Depends(get_current_user),
):
    """计算单个知识点下一次最优复习时间（FSRS 启发式）。"""
    payload = req.model_dump()
    payload["user_id"] = current_user.id
    return await _proxy_engine("/api/engine/next-review", payload)


@router.post("/knowledge-tracing")
async def knowledge_tracing(
    req: ReviewBatchRequest,
    current_user: User = Depends(get_current_user),
):
    """批量分析多个知识点的掌握状态，识别薄弱点。"""
    payload = req.model_dump()
    payload["user_id"] = current_user.id
    return await _proxy_engine("/api/engine/knowledge-tracing", payload)


@router.post("/estimate-duration")
async def estimate_duration(
    req: DurationRequest,
    current_user: User = Depends(get_current_user),
):
    """估算知识点学习时长。"""
    return await _proxy_engine(
        "/api/engine/estimate-duration",
        req.model_dump(),
    )
