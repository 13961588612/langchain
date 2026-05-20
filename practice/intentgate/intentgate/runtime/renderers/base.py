from abc import ABC, abstractmethod
from typing import Any

from intentgate.schemas.message import ChannelType
from intentgate.schemas.reply import CardIntent


class CardRenderer(ABC):
    """将 CardIntent 渲染为各客户端原生卡片格式。"""

    channel: ChannelType

    @abstractmethod
    def render(self, intent: CardIntent, template_def: dict[str, Any]) -> dict[str, Any]:
        pass
