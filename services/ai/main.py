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
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from core.config import settings
from core.llm import is_llm_available
from core.safety import check_input_safety
from core.capabilities import detect_capabilities, build_availability_hint
from core import media, model_config
from agents import (
    tutor_chat,
    explain_concept,
    buddy_chat,
    generate_questions,
    evaluate_answer,
    generate_learning_path,
    tutor_chat_stream,
    buddy_chat_stream,
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
    # 多轮会话历史：[{"role": "user"|"assistant", "content": "..."}]
    history: list = Field(default_factory=list)


class ExplainRequest(BaseModel):
    concept: str
    context: Optional[dict] = None
    level: str = "beginner"


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


class KnowledgeRequest(BaseModel):
    query: str
    topic: str = ""
    include_prerequisites: bool = False


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
            "POST /api/agents/generate-questions",
            "POST /api/agents/evaluate",
            "POST /api/agents/plan",
            "POST /api/agents/knowledge",
            "POST /api/agents/presentation",
            "POST /api/agents/tts",
            "POST /api/agents/image",
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

    # 输入安全检查
    blocked = check_input_safety(req.message)
    if blocked:
        return {"response": blocked, "agent_type": req.agent_type, "llm_available": is_llm_available()}

    if req.agent_type == "tutor":
        result = await tutor_chat(req.message, req.context, req.history)
    else:
        result = await buddy_chat(req.message, req.context, req.history)

    return {
        "response": result,
        "agent_type": req.agent_type,
        "llm_available": is_llm_available(),
    }


# ---------------------------------------------------------------------------
# 聊天（流式）
# ---------------------------------------------------------------------------

async def _stream_chat_events(message: str, agent_type: str, context: dict, history: list):
    """按 SSE 格式产出流式对话事件。"""
    try:
        if agent_type == "tutor":
            stream = tutor_chat_stream(message, context, history)
        else:
            stream = buddy_chat_stream(message, context, history)
        async for chunk in stream:
            yield f"data: {chunk}\n\n"
    except Exception as e:  # noqa: BLE001
        yield f"data: [error] {e}\n\n"
    yield "data: [done]\n\n"


@app.post("/api/agents/chat/stream")
async def agent_chat_stream(req: ChatRequest):
    """流式智能聊天（SSE）。支持 tutor 与 buddy，返回增量内容。"""
    if req.agent_type not in SUPPORTED_CHAT_AGENTS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid agent_type: {req.agent_type}. "
                f"Supported types: {', '.join(SUPPORTED_CHAT_AGENTS)}"
            ),
        )

    blocked = check_input_safety(req.message)
    if blocked:
        async def _blocked_stream():
            yield f"data: {blocked}\n\n"
            yield "data: [done]\n\n"
        return StreamingResponse(
            _blocked_stream(), media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return StreamingResponse(
        _stream_chat_events(req.message, req.agent_type, req.context, req.history),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


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
# 知识库检索（工具）
# ---------------------------------------------------------------------------

@app.post("/api/agents/knowledge")
async def agent_knowledge(req: KnowledgeRequest):
    """知识库检索工具：根据查询返回相关知识条目与可选的前置知识。"""
    from core.rag import build_knowledge_context, build_prerequisite_context

    results = await build_knowledge_context(req.query, req.topic, max_items=8)
    prereqs = await build_prerequisite_context(req.query) if req.include_prerequisites else ""
    return {
        "knowledge": results,
        "prerequisites": prereqs,
        "has_results": bool(results),
    }


# ---------------------------------------------------------------------------
# 多模态能力探测
# ---------------------------------------------------------------------------

class CapabilityRequest(BaseModel):
    pass


@app.get("/api/agents/capabilities")
async def agent_capabilities():
    """探测当前接入模型端点的能力，返回各产品功能可用性与缺失提示。"""
    cfg = model_config.get_config()
    if not cfg.get("base_url"):
        return {"configured": False, "message": "未配置模型端点(OPENAI_BASE_URL)，请先在设置中接入模型。"}
    caps = await detect_capabilities(cfg["base_url"], cfg.get("api_key") or "")
    return {"configured": True, **caps}


class ModelConfigRequest(BaseModel):
    api_key: str = ""
    base_url: str = ""
    llm_model: str = ""
    tts_model: str = ""
    asr_model: str = ""
    image_model: str = ""
    video_model: str = ""
    tts_voice: str = ""


@app.get("/api/agents/model-config")
async def get_model_config():
    """返回当前模型配置（api_key 脱敏）。"""
    return {"configured": True, "config": model_config.masked_config()}


@app.put("/api/agents/model-config")
async def update_model_config(req: ModelConfigRequest):
    """保存模型配置。"""
    patch = {k: v.strip() if isinstance(v, str) else v for k, v in req.model_dump().items()}
    # 若 api_key 传的是掩码(****)，保持不变
    if patch.get("api_key", "").endswith("****") or patch.get("api_key") == "":
        patch.pop("api_key", None)
    cfg = model_config.save_config(patch)
    return {"configured": True, "config": model_config.masked_config()}


# ---------------------------------------------------------------------------
# AI 讲解视频（PPT + 讲解稿 + 配音 + 合成）
# ---------------------------------------------------------------------------

class PresentationRequest(BaseModel):
    topic: str
    level: str = "beginner"


@app.post("/api/agents/presentation")
async def agent_presentation(req: PresentationRequest):
    """生成讲解视频：幻灯片 + 讲解稿 + 配音(可用时) + 合成视频。"""
    from agents.presenter import compose_presentation_video

    if not req.topic.strip():
        raise HTTPException(status_code=400, detail="主题不能为空")
    return await compose_presentation_video(req.topic.strip(), req.level)


# ---------------------------------------------------------------------------
# 媒体能力接口（TTS / ASR / 文生图）
# ---------------------------------------------------------------------------

class TTSRequest(BaseModel):
    text: str
    voice: str = ""


@app.post("/api/agents/tts")
async def agent_tts(req: TTSRequest):
    """文本转语音。成功返回 base64 音频。"""
    cfg = model_config.get_config()
    if not cfg.get("base_url"):
        return {"ok": False, "error": "未配置模型端点。"}
    caps = await detect_capabilities(cfg["base_url"], cfg.get("api_key") or "")
    tts_models = caps["models"].get("tts", [])
    if not tts_models:
        return {"ok": False, "error": build_availability_hint("tts", ["tts"]), "hint": True}
    model = cfg.get("tts_model") or tts_models[0]
    voice = req.voice or cfg.get("tts_voice") or "default"
    ok, res = await media.tts(cfg["base_url"], cfg.get("api_key") or "", model, req.text, voice=voice)
    if not ok:
        return {"ok": False, "error": res}
    import base64
    return {"ok": True, "audio": base64.b64encode(res).decode(), "format": "mp3", "model": model}


class ASRRequest(BaseModel):
    pass


class ImageRequest(BaseModel):
    prompt: str
    size: str = "1024x1024"


@app.post("/api/agents/image")
async def agent_image(req: ImageRequest):
    """文生图。成功返回 base64 图片。"""
    cfg = model_config.get_config()
    if not cfg.get("base_url"):
        return {"ok": False, "error": "未配置模型端点。"}
    caps = await detect_capabilities(cfg["base_url"], cfg.get("api_key") or "")
    img_models = caps["models"].get("image", [])
    if not img_models:
        return {"ok": False, "error": build_availability_hint("image", ["image"]), "hint": True}
    model = cfg.get("image_model") or img_models[0]
    ok, res = await media.image(cfg["base_url"], cfg.get("api_key") or "", model, req.prompt, req.size)
    if not ok:
        return {"ok": False, "error": res}
    import base64
    return {"ok": True, "image": base64.b64encode(res).decode(), "model": model}


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
