from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "EduFlow AI Service"
    VERSION: str = "0.1.0"
    DEBUG: bool = True
    OPENAI_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.7
    REDIS_URL: str = "redis://localhost:6379/0"
    API_PORT: int = 8100
    MAX_TOKENS: int = 4096
    
    class Config:
        env_file = ".env"

settings = Settings()