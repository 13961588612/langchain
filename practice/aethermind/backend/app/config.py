"""Application configuration via pydantic-settings."""
import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_SECRET_KEY: str = "change-me-to-a-random-secret"
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://aethermind:aethermind_secret@localhost:5432/aethermind"
    )
    DATABASE_URL_SYNC: str = (
        "postgresql://aethermind:aethermind_secret@localhost:5432/aethermind"
    )

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM API Keys
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_ENDPOINT: str = ""

    # LangSmith
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = "aethermind"
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"

    # Work directories
    WORKDIR_ROOT: str = str(PROJECT_ROOT / "workdirs")

    # Channels
    WECOM_CORP_ID: str = ""
    WECOM_AGENT_ID: str = ""
    WECOM_SECRET: str = ""
    WECOM_TOKEN: str = ""
    WECOM_ENCODING_AES_KEY: str = ""

    FEISHU_APP_ID: str = ""
    FEISHU_APP_SECRET: str = ""
    FEISHU_VERIFICATION_TOKEN: str = ""

    DINGTALK_APP_KEY: str = ""
    DINGTALK_APP_SECRET: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


def configure_langsmith():
    """Configure LangSmith tracing if API key is available."""
    settings = get_settings()
    if settings.LANGSMITH_API_KEY:
        os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGSMITH_PROJECT"] = settings.LANGSMITH_PROJECT
        os.environ["LANGSMITH_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
        os.environ["LANGSMITH_TRACING"] = "true"
