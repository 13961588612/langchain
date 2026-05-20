from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ChannelType(StrEnum):
    WECOM = "wecom"
    FEISHU = "feishu"
    DINGTALK = "dingtalk"
    WEB = "web"
    API = "api"


class StandardMessage(BaseModel):
    """入站用户消息（Gateway → Agent，慢路径）。"""

    session_id: str
    channel: ChannelType
    user_id: str
    text: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CardActionEvent(BaseModel):
    """入站卡片交互事件（快路径优先在 Gateway 处理）。"""

    session_id: str
    channel: ChannelType
    task_id: str
    action_key: str
    user_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
