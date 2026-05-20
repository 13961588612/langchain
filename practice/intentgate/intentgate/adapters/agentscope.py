from collections.abc import AsyncIterator

import httpx

from intentgate.adapters.agent_backend import AgentBackend
from intentgate.schemas.message import CardActionEvent, StandardMessage
from intentgate.schemas.reply import AgentReply


class AgentScopeBackend(AgentBackend):
    """AgentScope 适配器（P1：对接 Runtime Agent API 或自建 Bridge）。"""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    async def chat(self, message: StandardMessage) -> AsyncIterator[AgentReply]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/v1/sessions/{message.session_id}/messages",
                json=message.model_dump(mode="json"),
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        yield AgentReply.model_validate_json(line[6:])

    async def handle_action(self, event: CardActionEvent) -> AsyncIterator[AgentReply]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/v1/sessions/{event.session_id}/actions",
                json=event.model_dump(mode="json"),
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        yield AgentReply.model_validate_json(line[6:])
