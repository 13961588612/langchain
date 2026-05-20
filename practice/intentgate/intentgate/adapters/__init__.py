from intentgate.adapters.aethermind import AetherMindBackend
from intentgate.adapters.agent_backend import AgentBackend
from intentgate.adapters.agentscope import AgentScopeBackend
from intentgate.adapters.mock import MockAgentBackend
from intentgate.config import Settings


def create_agent_backend(settings: Settings) -> AgentBackend:
    match settings.AGENT_BACKEND:
        case "agentscope":
            return AgentScopeBackend(settings.AGENT_BACKEND_URL)
        case "aethermind":
            return AetherMindBackend(
                settings.AGENT_BACKEND_URL,
                settings.AETHERMIND_AGENT_ID,
            )
        case _:
            return MockAgentBackend()
