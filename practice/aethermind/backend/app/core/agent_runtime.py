"""Agent Runtime - Core agent execution engine using DeepAgents + LangGraph.

This module is the heart of AetherMind. It:
- Creates DeepAgent instances from database configurations
- Manages LangGraph checkpoints for conversation persistence
- Handles streaming chat with tool calls
- Integrates with the Model Hub
"""

import asyncio
import os
from pathlib import Path
from typing import Any, AsyncGenerator, Optional

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from loguru import logger

from app.config import get_settings, configure_langsmith

settings = get_settings()
configure_langsmith()


class AgentRuntime:
    """Manages the lifecycle and execution of DeepAgent instances.

    Each agent is created lazily on first use and cached. The runtime
    handles model creation, skills loading, work directory setup,
    and checkpoint management.
    """

    def __init__(self):
        self._agents: dict[str, Any] = {}  # agent_id -> CompiledStateGraph
        self._checkpointer: Optional[AsyncPostgresSaver] = None
        self._checkpointer_lock = asyncio.Lock()

    async def _get_checkpointer(self) -> AsyncPostgresSaver:
        """Get or create the Postgres checkpointer for LangGraph persistence."""
        if self._checkpointer is None:
            async with self._checkpointer_lock:
                if self._checkpointer is None:
                    db_url = settings.DATABASE_URL.replace(
                        "postgresql+asyncpg://", "postgresql://"
                    )
                    self._checkpointer = AsyncPostgresSaver.from_conn_string(db_url)
                    await self._checkpointer.setup()
                    logger.info("Postgres checkpointer initialized")
        return self._checkpointer

    async def _build_agent(self, agent_config: dict[str, Any]) -> Any:
        """Build a DeepAgent from configuration.

        Uses DeepAgents create_deep_agent to construct an agent with:
        - Configured model from Model Hub
        - Custom system prompt from agent config
        - Filesystem backend for work directory
        - Skills loaded from work directory or database
        - Checkpointer for conversation persistence
        """
        from deepagents import create_deep_agent
        from app.core.model_hub import model_hub

        agent_id = agent_config["id"]
        provider = agent_config.get("model_provider", "openai")
        model_name = agent_config.get("model_name", "gpt-4o")
        system_prompt = agent_config.get("system_prompt") or ""

        # Resolve model parameters
        model_params = {}
        if agent_config.get("model_parameters"):
            import json
            try:
                model_params = json.loads(agent_config["model_parameters"])
            except json.JSONDecodeError:
                logger.warning(f"Invalid model_parameters JSON for agent {agent_id}")

        # Create the chat model
        model = model_hub.get_model(
            provider=provider,
            model_name=model_name,
            temperature=model_params.get("temperature", 0.7),
            max_tokens=model_params.get("max_tokens"),
        )

        # Configure filesystem backend for agent work directory
        from deepagents.backends.filesystem import FilesystemBackend

        work_dir = agent_config.get("work_directory")
        if not work_dir:
            work_dir = os.path.join(settings.WORKDIR_ROOT, agent_id)
            os.makedirs(work_dir, exist_ok=True)

        backend = FilesystemBackend(root_dir=work_dir)

        # Load skills from work directory
        skills_dir = os.path.join(work_dir, "skills")
        skills = []
        if os.path.isdir(skills_dir):
            skills.append(skills_dir)

        # Get checkpointer
        checkpointer = await self._get_checkpointer()

        # Build system prompt with soul/profile
        full_system_prompt = self._build_system_prompt(
            system_prompt,
            agent_config.get("soul_config"),
            agent_config.get("profile_config"),
        )

        # Create the deep agent
        agent = create_deep_agent(
            model=model,
            system_prompt=full_system_prompt,
            backend=backend,
            skills=skills,
            checkpointer=checkpointer,
        )

        logger.info(f"Agent built: {agent_id} ({provider}:{model_name})")
        return agent

    @staticmethod
    def _build_system_prompt(
        base_prompt: str,
        soul_config: Optional[str] = None,
        profile_config: Optional[str] = None,
    ) -> str:
        """Assemble the full system prompt from base + soul + profile."""
        parts = [base_prompt.strip()] if base_prompt.strip() else []

        if soul_config:
            parts.append(f"\n## Personality & Soul\n{soul_config.strip()}")

        if profile_config:
            parts.append(f"\n## Behavior Profile\n{profile_config.strip()}")

        return "\n\n".join(parts)

    async def get_or_create_agent(
        self,
        agent_id: str,
        agent_config: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Get a cached agent or build a new one from config.

        If agent_config is not provided, loads it from the database.
        """
        if agent_id in self._agents:
            return self._agents[agent_id]

        if agent_config is None:
            # Load from database
            from app.database import async_session_factory
            from app.models.agent import Agent
            from sqlalchemy import select

            async with async_session_factory() as session:
                result = await session.execute(
                    select(Agent).where(
                        Agent.id == agent_id,
                        Agent.is_deleted == False,
                        Agent.is_active == True,
                    )
                )
                agent_row = result.scalar_one_or_none()
                if not agent_row:
                    raise ValueError(f"Agent {agent_id} not found or inactive")

                agent_config = {
                    "id": agent_row.id,
                    "name": agent_row.name,
                    "system_prompt": agent_row.system_prompt,
                    "model_provider": agent_row.model_provider,
                    "model_name": agent_row.model_name,
                    "model_parameters": agent_row.model_parameters,
                    "soul_config": agent_row.soul_config,
                    "profile_config": agent_row.profile_config,
                    "work_directory": agent_row.work_directory,
                }

        agent = await self._build_agent(agent_config)
        self._agents[agent_id] = agent
        return agent

    async def stream_chat(
        self,
        agent_id: str,
        thread_id: str,
        message: str,
        agent_config: Optional[dict[str, Any]] = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream a chat response from the agent.

        Yields dicts with keys: event (token/tool_call/tool_result/done/error),
        content, and optional metadata.

        Args:
            agent_id: The agent's unique ID
            thread_id: LangGraph thread ID for conversation continuity
            message: User's message text
            agent_config: Optional agent configuration dict

        Yields:
            Streaming chunks as dicts
        """
        try:
            agent = await self.get_or_create_agent(agent_id, agent_config)
            config = {"configurable": {"thread_id": thread_id}}

            input_state = {
                "messages": [{"role": "user", "content": message}],
            }

            async for event in agent.astream_events(input_state, config=config, version="v2"):
                kind = event.get("event", "")

                if kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk", None)
                    if chunk and hasattr(chunk, "content"):
                        content = chunk.content
                        if content:
                            yield {"event": "token", "content": content}

                elif kind == "on_tool_start":
                    tool_name = event.get("name", "unknown")
                    tool_input = event.get("data", {}).get("input", {})
                    yield {
                        "event": "tool_call",
                        "content": f"Calling tool: {tool_name}",
                        "metadata": {
                            "tool_name": tool_name,
                            "tool_input": str(tool_input),
                        },
                    }

                elif kind == "on_tool_end":
                    tool_name = event.get("name", "unknown")
                    output = event.get("data", {}).get("output", "")
                    yield {
                        "event": "tool_result",
                        "content": f"Tool result: {tool_name}",
                        "metadata": {
                            "tool_name": tool_name,
                            "output": str(output)[:500],
                        },
                    }

            yield {
                "event": "done",
                "content": "",
                "metadata": {"thread_id": thread_id, "agent_id": agent_id},
            }

        except Exception as exc:
            logger.error(f"Error streaming chat for agent {agent_id}: {exc}")
            yield {"event": "error", "content": str(exc)}

    def clear_agent_cache(self, agent_id: Optional[str] = None):
        """Clear cached agent instances."""
        if agent_id:
            self._agents.pop(agent_id, None)
            logger.info(f"Cleared agent cache for {agent_id}")
        else:
            self._agents.clear()
            logger.info("Cleared all agent caches")


# Global runtime instance
agent_runtime = AgentRuntime()
