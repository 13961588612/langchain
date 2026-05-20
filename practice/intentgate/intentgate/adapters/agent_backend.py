from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from intentgate.schemas.message import CardActionEvent, StandardMessage
from intentgate.schemas.reply import AgentReply


class AgentBackend(ABC):
    """智能体后端抽象：AgentScope / AetherMind 实现同一接口。"""

    @abstractmethod
    async def chat(self, message: StandardMessage) -> AsyncIterator[AgentReply]:
        """处理用户文本，流式返回 AgentReply。"""

    @abstractmethod
    async def handle_action(self, event: CardActionEvent) -> AsyncIterator[AgentReply]:
        """处理复杂卡片动作（慢路径，Gateway 已发占位卡后异步调用）。"""
