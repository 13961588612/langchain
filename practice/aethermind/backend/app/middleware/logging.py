"""Logging middleware for request/response tracking."""
import time
from typing import Callable

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs all HTTP requests with timing info."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        method = request.method
        url = str(request.url)
        client = request.client.host if request.client else "unknown"

        logger.info(f"--> {method} {url} from {client}")

        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error(f"<-- {method} {url} ERROR: {exc}")
            raise

        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(
            f"<-- {method} {url} {response.status_code} {elapsed_ms:.1f}ms"
        )

        return response


class TokenUsageTracker:
    """Tracks cumulative token usage across all agents."""

    def __init__(self):
        self._total_input_tokens: int = 0
        self._total_output_tokens: int = 0
        self._request_count: int = 0

    def track(self, input_tokens: int = 0, output_tokens: int = 0):
        """Record token usage for a single request."""
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens
        self._request_count += 1

    @property
    def stats(self) -> dict:
        return {
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "total_tokens": self._total_input_tokens + self._total_output_tokens,
            "request_count": self._request_count,
        }

    def reset(self):
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._request_count = 0


# Global token tracker
token_tracker = TokenUsageTracker()
