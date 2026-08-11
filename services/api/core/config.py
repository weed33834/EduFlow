from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "EduFlow API"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    # 运行环境：development / production。production 下强制使用非默认密钥。
    ENV: str = "development"

    # SQLite database
    DATABASE_URL: str = "sqlite+aiosqlite:///./eduflow.db"

    # Security
    SECRET_KEY: str = "eduflow-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # AI service
    AI_SERVICE_URL: str = "http://localhost:8100"

    # Learning engine (FSRS 知识追踪 / 间隔重复)
    ENGINE_SERVICE_URL: str = "http://localhost:8200"

    # Learning configuration
    PASS_SCORE_THRESHOLD: int = 60

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]


settings = Settings()
