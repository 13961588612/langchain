from collections.abc import AsyncIterator

import httpx

from intentgate.adapters.agent_backend import AgentBackend
from intentgate.schemas.message import CardActionEvent, StandardMessage
from intentgate.schemas.reply import AgentReply


class AetherMindBackend(AgentBackend):
    """AetherMind 适配器（P4：对接 /api/agents/{id}/chat SSE）。"""

    def __init__(self, base_url: str, agent_id: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._agent_id = agent_id

    async def chat(self, message: StandardMessage) -> AsyncIterator[AgentReply]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/api/agents/{self._agent_id}/chat",
                json={"message": message.text, "session_id": message.session_id},
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        yield AgentReply.model_validate_json(line[6:])

    async def handle_action(self, event: CardActionEvent) -> AsyncIterator[AgentReply]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/api/agents/{self._agent_id}/actions",
                json=event.model_dump(mode="json"),
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        yield AgentReply.model_validate_json(line[6:])
