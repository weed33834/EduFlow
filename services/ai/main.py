"""
EduFlow AI Service - 主程序

提供 AI 智能体相关的 HTTP 接口，包括：
- 智能问答（导师 / 学习伙伴）
- 概念解释
- 话题讨论
- 题目生成
- 答案评估
- 学习路径规划
- 学习计划调整

当未配置 OPENAI_API_KEY 时，各接口返回智能降级回复，保证服务可用。
对于无效的 agent_type，返回 HTTP 400 错误而非静默降级。
"""
from datetime import datetime, timezone
from typing import Any, Optional, Union

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.config import settings
from core.llm import is_llm_available
from agents import (
    tutor_chat,
    explain_concept,
    buddy_chat,
    discuss_topic,
    generate_questions,
    evaluate_answer,
    generate_learning_path,
    adjust_plan,
)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="EduFlow AI 智能体服务，提供辅导、出题、评估与学习规划能力。",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 可用的聊天 agent 类型
SUPPORTED_CHAT_AGENTS = ("tutor", "buddy")


# ---------------------------------------------------------------------------
# 请求模型（字段与后端 API 代理保持一致）
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    agent_type: str = "tutor"
    context: dict = Field(default_factory=dict)


class ExplainRequest(BaseModel):
    concept: str
    context: Optional[dict] = None
    level: str = "beginner"


class DiscussRequest(BaseModel):
    topic: str
    context: Optional[dict] = None


class GenerateQuestionsRequest(BaseModel):
    topic: str
    difficulty: str = "medium"
    count: int = 5
    context: Union[str, dict, None] = ""


class EvaluateRequest(BaseModel):
    question: str
    user_answer: str
    context: Union[str, dict, None] = None


class PlanRequest(BaseModel):
    goal: str
    level: str = "beginner"
    duration_weeks: int = 12
    preferences: Union[list, dict, str, None] = None


class AdjustPlanRequest(BaseModel):
    feedback: str
    current_plan: dict = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# 健康检查
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health():
    """健康检查：返回服务状态、配置信息和可用 agent 列表。"""
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "llm_available": is_llm_available(),
        "config": {
            "llm_provider": settings.LLM_PROVIDER,
            "llm_model": settings.LLM_MODEL,
            "api_port": settings.API_PORT,
            "debug": settings.DEBUG,
        },
        "agents": [
            {"name": "tutor", "type": "chat", "description": "苏格拉底式智能导师"},
            {"name": "buddy", "type": "chat", "description": "学习伙伴式对话"},
            {"name": "examiner", "type": "tool", "description": "出题与答案评估"},
            {"name": "planner", "type": "tool", "description": "学习路径规划与调整"},
        ],
        "endpoints": [
            "POST /api/agents/chat",
            "POST /api/agents/explain",
            "POST /api/agents/discuss",
            "POST /api/agents/generate-questions",
            "POST /api/agents/evaluate",
            "POST /api/agents/plan",
            "POST /api/agents/adjust-plan",
        ],
    }


# ---------------------------------------------------------------------------
# 聊天（导师 / 学习伙伴）
# ---------------------------------------------------------------------------

@app.post("/api/agents/chat")
async def agent_chat(req: ChatRequest):
    """智能聊天。支持 tutor 和 buddy 两种 agent 类型。

    无效的 agent_type 返回 HTTP 400 错误，而非静默降级。
    """
    if req.agent_type not in SUPPORTED_CHAT_AGENTS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid agent_type: {req.agent_type}. "
                f"Supported types: {', '.join(SUPPORTED_CHAT_AGENTS)}"
            ),
        )

    if req.agent_type == "tutor":
        result = await tutor_chat(req.message, req.context)
    else:
        result = await buddy_chat(req.message, req.context)

    return {
        "response": result,
        "agent_type": req.agent_type,
        "llm_available": is_llm_available(),
    }


# ---------------------------------------------------------------------------
# 概念解释
# ---------------------------------------------------------------------------

@app.post("/api/agents/explain")
async def agent_explain(req: ExplainRequest):
    """概念解释：用与学习者水平匹配的方式解释指定概念。"""
    result = await explain_concept(req.concept, req.level, req.context)
    return {
        "response": result,
        "concept": req.concept,
        "level": req.level,
        "llm_available": is_llm_available(),
    }


# ---------------------------------------------------------------------------
# 话题讨论
# ---------------------------------------------------------------------------

@app.post("/api/agents/discuss")
async def agent_discuss(req: DiscussRequest):
    """话题讨论：围绕指定话题发起学习伙伴式讨论。"""
    result = await discuss_topic(req.topic)
    return {
        "response": result,
        "topic": req.topic,
        "llm_available": is_llm_available(),
    }


# ---------------------------------------------------------------------------
# 题目生成
# ---------------------------------------------------------------------------

@app.post("/api/agents/generate-questions")
async def agent_generate_questions(req: GenerateQuestionsRequest):
    """生成练习题：根据主题、难度和数量生成结构化题目。"""
    questions = await generate_questions(
        req.topic, req.difficulty, req.count, req.context
    )
    return {
        "questions": questions,
        "count": len(questions),
        "topic": req.topic,
        "difficulty": req.difficulty,
        "llm_available": is_llm_available(),
    }


# ---------------------------------------------------------------------------
# 答案评估
# ---------------------------------------------------------------------------

@app.post("/api/agents/evaluate")
async def agent_evaluate(req: EvaluateRequest):
    """评估答案：对学生的作答进行评分和反馈。"""
    result = await evaluate_answer(req.question, req.user_answer, req.context)
    return {
        "is_correct": result.get("is_correct", False),
        "score": result.get("score", 0),
        "feedback": result.get("feedback", ""),
        "hint": result.get("hint", ""),
        "llm_available": is_llm_available(),
    }


# ---------------------------------------------------------------------------
# 学习路径规划
# ---------------------------------------------------------------------------

@app.post("/api/agents/plan")
async def agent_plan(req: PlanRequest):
    """学习规划：根据目标、水平、时长和偏好生成学习路径。"""
    plan = await generate_learning_path(
        req.goal, req.level, req.duration_weeks, req.preferences
    )
    return {
        "plan": plan,
        "goal": req.goal,
        "level": req.level,
        "llm_available": is_llm_available(),
    }


# ---------------------------------------------------------------------------
# 学习计划调整
# ---------------------------------------------------------------------------

@app.post("/api/agents/adjust-plan")
async def agent_adjust_plan(req: AdjustPlanRequest):
    """调整计划：根据反馈调整现有学习计划。"""
    adjusted = await adjust_plan(req.feedback, req.current_plan)
    return {
        "plan": adjusted,
        "feedback": req.feedback,
        "llm_available": is_llm_available(),
    }


# ---------------------------------------------------------------------------
# 启动入口
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
