"""Skill model."""
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tags: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)
    skill_files: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )  # {filename: content}
    downloads: Mapped[int] = mapped_column(default=0, nullable=False)
    rating: Mapped[float] = mapped_column(default=0.0, nullable=False)
    is_public: Mapped[bool] = mapped_column(default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<Skill(id={self.id}, name={self.name})>"
