"""
EduFlow AI Service - 核心配置模块

使用 pydantic-settings 管理应用配置，支持从环境变量和 .env 文件加载。
"""
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置项。

    所有配置均可通过环境变量覆盖，环境变量名不区分大小写。
    也可在项目根目录放置 .env 文件进行配置。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- 应用基础信息 ----
    APP_NAME: str = "EduFlow AI Service"
    VERSION: str = "0.1.0"
    DEBUG: bool = False

    # ---- LLM 相关配置 ----
    OPENAI_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 4096

    # ---- 基础设施 ----
    REDIS_URL: str = "redis://localhost:6379/0"
    API_PORT: int = 8100


settings = Settings()
