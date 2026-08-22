"""FastAPI 入口"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.agents.graph import use_persistent_checkpointer, close_checkpointer
from app.database import init_db
from app.tools.llm import setup_external_callbacks
from app.routers import auth, chat, sessions, profile

logger = logging.getLogger(__name__)

_WEAK_SECRETS = {"change-me", "change-me-in-production", ""}


def assert_production_security() -> None:
    """生产模式下拒绝弱配置启动（fail-fast，而不是静默兜底）"""
    if getattr(settings, "ENV", "dev") != "production":
        return
    weak = []
    if settings.JWT_SECRET in _WEAK_SECRETS:
        weak.append("JWT_SECRET")
    if not settings.LITELLM_API_KEY:
        weak.append("LITELLM_API_KEY")
    if weak:
        raise RuntimeError(
            f"生产环境缺少安全配置: {', '.join(weak)}。"
            "请在环境变量中设置后再启动（ refusing to start with defaults ）。"
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库
    await init_db()
    assert_production_security()
    setup_external_callbacks()
    persisted = await use_persistent_checkpointer()
    logger.info("Checkpointer 持久化: %s", "PostgreSQL" if persisted else "MemorySaver(进程内)")
    yield
    await close_checkpointer()


app = FastAPI(
    title="EduAgent",
    description="AI 编程学习 Agent",
    version="0.4.19",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(sessions.router)
app.include_router(profile.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.4.19"}
