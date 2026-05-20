from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8090

    AGENT_BACKEND: str = "mock"
    AGENT_BACKEND_URL: str = "http://127.0.0.1:8100"
    AETHERMIND_AGENT_ID: str = "default"

    WECOM_BOT_ID: str = ""
    WECOM_BOT_SECRET: str = ""
    WECOM_WS_URL: str = "wss://openws.work.weixin.qq.com"

    SESSION_STORE: str = "memory"
    REDIS_URL: str = "redis://127.0.0.1:6379/0"

    CARDS_DIR: str = "./cards"

    @property
    def cards_path(self) -> Path:
        return Path(self.CARDS_DIR).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
