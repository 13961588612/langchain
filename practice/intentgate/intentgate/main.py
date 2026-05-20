"""IntentGate application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from intentgate.adapters import create_agent_backend
from intentgate.adapters.agent_backend import AgentBackend
from intentgate.config import get_settings
from intentgate.gateway.api import router as gateway_router
from intentgate.gateway.session import InMemorySessionStore
from intentgate.runtime.card_runtime import CardRuntime

settings = get_settings()
_agent_backend: AgentBackend | None = None
_card_runtime: CardRuntime | None = None
_session_store = InMemorySessionStore()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _agent_backend, _card_runtime
    logger.info("Starting IntentGate...")
    _agent_backend = create_agent_backend(settings)
    _card_runtime = CardRuntime(settings.cards_path)
    logger.info(f"Agent backend: {settings.AGENT_BACKEND}")
    logger.info(f"Cards dir: {settings.cards_path}")
    yield
    logger.info("Shutting down IntentGate...")


app = FastAPI(
    title="IntentGate",
    description="Multi-channel card interaction gateway",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(gateway_router)


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "service": "intentgate",
        "agent_backend": settings.AGENT_BACKEND,
    }


def get_agent_backend() -> AgentBackend:
    if _agent_backend is None:
        raise RuntimeError("Agent backend not initialized")
    return _agent_backend


def get_card_runtime() -> CardRuntime:
    if _card_runtime is None:
        raise RuntimeError("Card runtime not initialized")
    return _card_runtime


def get_session_store() -> InMemorySessionStore:
    return _session_store
