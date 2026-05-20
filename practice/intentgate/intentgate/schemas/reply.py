from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ReplyKind(StrEnum):
    TEXT = "text"
    STREAM = "stream"
    CARD = "card"
    MARKDOWN = "markdown"


class CardAction(BaseModel):
    key: str
    label: str
    style: int | None = None


class CardIntent(BaseModel):
    """Agent 产出的结构化卡片意图，由 Card Runtime 渲染为各客户端原生格式。"""

    template: str
    slots: dict[str, str | int | float] = Field(default_factory=dict)
    actions: list[CardAction] = Field(default_factory=list)
    task_id: str | None = None
    feedback_id: str | None = None


class StreamChunk(BaseModel):
    id: str
    content: str
    finish: bool = False


class AgentReply(BaseModel):
    """出站统一回复（Agent → Gateway → Channel Renderer）。"""

    session_id: str
    kind: ReplyKind
    text: str | None = None
    stream: StreamChunk | None = None
    card: CardIntent | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
