"""AetherMind - Universal Agent Work Platform.

FastAPI application entry point.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.agents import router as agents_router
from app.api.conversations import router as conversations_router
from app.config import get_settings, configure_langsmith
from app.database import init_db
from app.middleware.logging import LoggingMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    logger.info("Starting AetherMind...")
    logger.info(f"Environment: {settings.APP_ENV}")

    # Configure LangSmith tracing
    configure_langsmith()

    # Initialize database tables
    try:
        await init_db()
        logger.info("Database tables initialized")
    except Exception as exc:
        logger.warning(f"Database init skipped (may not be available yet): {exc}")

    yield

    logger.info("Shutting down AetherMind...")


app = FastAPI(
    title="AetherMind API",
    description="Universal Agent Work Platform - Create, configure, and orchestrate AI agents",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
app.add_middleware(LoggingMiddleware)

# API routes
app.include_router(agents_router)
app.include_router(conversations_router)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    from app.middleware.logging import token_tracker

    return {
        "status": "ok",
        "version": "0.1.0",
        "environment": settings.APP_ENV,
        "token_usage": token_tracker.stats,
    }
