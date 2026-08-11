from typing import Optional, Union

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
import httpx

from core.config import settings
from core.deps import get_current_user
from models.user import User

router = APIRouter(prefix="/api/ai", tags=["ai"])

AI_TIMEOUT = 60.0


class ChatRequest(BaseModel):
    message: str
    context: dict = {}
    agent_type: str = "tutor"
    history: list = Field(default_factory=list)


class GenerateQuestionsRequest(BaseModel):
    topic: str
    difficulty: str = "medium"
    count: int = 5
    context: Union[str, dict, None] = None


class ExplainRequest(BaseModel):
    concept: str
    context: Optional[dict] = None
    # 前端传入的字段名为 detail_level，AI 服务期望 level；
    # 通过 alias 接收 detail_level，模型字段名仍为 level，与 AI 服务保持一致。
    # model_dump() 默认按字段名序列化，输出 {concept, context, level}。
    level: str = Field(default="beginner", alias="detail_level")

    model_config = {"populate_by_name": True}


class EvaluateRequest(BaseModel):
    question: str
    user_answer: str
    correct_answer: str = ""
    # AI 服务的 EvaluateRequest 接受 {question, user_answer, context}，
    # correct_answer 会在 handler 中合并进 context 再转发。
    context: Union[str, dict, None] = None


class PlanRequest(BaseModel):
    goal: str
    level: str = "beginner"
    duration_weeks: int = 12
    # 以下两个字段由前端传入，AI 服务的 PlanRequest 不直接接受，
    # 需在 handler 中映射到 preferences。
    difficulty: str = "medium"
    context: Optional[dict] = None
    # 允许调用方直接传入 preferences；未传时由 difficulty + context 推导。
    preferences: Union[list, dict, str, None] = None


async def _proxy_to_ai(path: str, payload: dict) -> dict:
    """Unified proxy function to forward requests to the AI service.
    Handles timeouts and connection errors.
    """
    url = f"{settings.AI_SERVICE_URL}{path}"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, timeout=AI_TIMEOUT)
        except httpx.ConnectError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service unavailable",
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="AI service request timed out",
            )

    if resp.status_code >= 400:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"AI service error: {resp.text}",
        )

    try:
        return resp.json()
    except Exception:
        return {"raw": resp.text}


@router.post("/chat")
async def ai_chat(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    payload = req.model_dump()
    payload["user_id"] = current_user.id
    return await _proxy_to_ai("/api/agents/chat", payload)


@router.post("/generate-questions")
async def generate_questions(
    req: GenerateQuestionsRequest,
    current_user: User = Depends(get_current_user),
):
    payload = req.model_dump()
    payload["user_id"] = current_user.id
    return await _proxy_to_ai("/api/agents/generate-questions", payload)


@router.post("/explain")
async def explain_concept(
    req: ExplainRequest,
    current_user: User = Depends(get_current_user),
):
    # model_dump() 默认按字段名输出 -> {concept, context, level}，与 AI 服务一致
    payload = req.model_dump()
    payload["user_id"] = current_user.id
    return await _proxy_to_ai("/api/agents/explain", payload)


@router.post("/evaluate")
async def evaluate_answer(
    req: EvaluateRequest,
    current_user: User = Depends(get_current_user),
):
    # AI 服务期望 {question, user_answer, context}，
    # correct_answer 需合并进 context 再转发，供 AI 评估时参考。
    if isinstance(req.context, dict):
        ctx = dict(req.context)
    elif isinstance(req.context, str) and req.context:
        ctx = {"extra": req.context}
    else:
        ctx = {}
    if req.correct_answer:
        ctx["correct_answer"] = req.correct_answer

    payload = {
        "question": req.question,
        "user_answer": req.user_answer,
        "context": ctx if ctx else None,
    }
    payload["user_id"] = current_user.id
    return await _proxy_to_ai("/api/agents/evaluate", payload)


@router.post("/plan")
async def learning_plan(
    req: PlanRequest,
    current_user: User = Depends(get_current_user),
):
    # 前端传入 {goal, level, duration_weeks, difficulty, context}，
    # AI 服务 PlanRequest 只接受 {goal, level, duration_weeks, preferences}。
    # 这里把 difficulty 与 context 映射到 preferences，做好前后端字段映射。
    if req.preferences is None:
        preferences = {}
        if req.difficulty:
            preferences["difficulty"] = req.difficulty
        if req.context:
            preferences["context"] = req.context
        if not preferences:
            preferences = None
    else:
        preferences = req.preferences

    payload = {
        "goal": req.goal,
        "level": req.level,
        "duration_weeks": req.duration_weeks,
        "preferences": preferences,
    }
    payload["user_id"] = current_user.id
    return await _proxy_to_ai("/api/agents/plan", payload)
