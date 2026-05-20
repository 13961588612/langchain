from collections.abc import AsyncIterator

from intentgate.adapters.agent_backend import AgentBackend
from intentgate.schemas.message import CardActionEvent, StandardMessage
from intentgate.schemas.reply import AgentReply, ReplyKind


class MockAgentBackend(AgentBackend):
    """开发用占位后端，验证 Gateway 协议链路。"""

    async def chat(self, message: StandardMessage) -> AsyncIterator[AgentReply]:
        yield AgentReply(
            session_id=message.session_id,
            kind=ReplyKind.TEXT,
            text=f"[mock] 收到：{message.text}",
        )

    async def handle_action(self, event: CardActionEvent) -> AsyncIterator[AgentReply]:
        yield AgentReply(
            session_id=event.session_id,
            kind=ReplyKind.TEXT,
            text=f"[mock] 动作 {event.action_key} @ {event.task_id}",
        )
