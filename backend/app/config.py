"""应用配置"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./eduagent.db"

    # 运行环境：dev / production（production 下弱配置会拒绝启动）
    ENV: str = "dev"

    # JWT
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # LLM (LiteLLM — 支持 OpenAI / Claude / Gemini 等 100+ 模型)
    LITELLM_API_KEY: str = ""
    LITELLM_BASE_URL: str = "https://api.openai.com/v1"
    LITELLM_MODEL: str = "gpt-4o-mini"

    # 外部追踪（可选）：逗号分隔，如 "langfuse" 或 "langsmith"。
    # 对应 SDK 需自行安装并配置其环境变量（如 LANGFUSE_PUBLIC_KEY）。
    # 未安装 SDK 时 litellm 会在调用期报错——留空即完全关闭。
    LITELLM_SUCCESS_CALLBACK: str = ""

    # 本地追踪（默认开启）：LLM 调用 span 追加到 TRACE_DIR/traces.jsonl，
    # 用 scripts/view_traces.py 查看。零依赖零账号。
    TRACE_ENABLED: bool = True
    TRACE_DIR: str = "logs"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    # 限流（滑动窗口；配 REDIS_URL 用分布式实现，留空用进程内实现）
    RATE_LIMIT_CHAT_PER_MIN: int = 20
    RATE_LIMIT_AUTH_PER_MIN: int = 10
    REDIS_URL: str = ""

    # E2B 代码沙箱（开源 — pip install e2b）
    E2B_API_KEY: str = ""

    # Qdrant 向量数据库（开源 — pip install qdrant-client）
    QDRANT_URL: str = "http://localhost:6333"

    # Mem0 长期记忆（开源 — pip install mem0ai）
    MEM0_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def llm_available(self) -> bool:
        return bool(self.LITELLM_API_KEY)


settings = Settings()
