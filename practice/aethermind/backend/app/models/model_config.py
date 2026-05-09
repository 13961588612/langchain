"""Model configuration model."""
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ModelConfig(Base):
    __tablename__ = "model_configs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # openai / anthropic / google / azure / ollama
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    api_key_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parameters: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    # e.g. {"temperature": 0.7, "max_tokens": 4096, "top_p": 0.9}
    is_default: Mapped[bool] = mapped_column(default=False, nullable=False)
    cost_per_1k_input: Mapped[float] = mapped_column(default=0.0, nullable=False)
    cost_per_1k_output: Mapped[float] = mapped_column(default=0.0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<ModelConfig(id={self.id}, provider={self.provider}:{self.model_name})>"
