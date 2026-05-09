"""Model Hub - Unified model provider abstraction.

Supports: OpenAI, Anthropic, Google Gemini, Azure, Ollama, and custom providers.
"""
import os
from typing import Any, Optional

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from loguru import logger

from app.config import get_settings

settings = get_settings()

# Map provider names to environment variable keys for API keys
PROVIDER_API_KEY_MAP = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
    "google_genai": "GOOGLE_API_KEY",
    "azure": "AZURE_OPENAI_API_KEY",
    "azure_openai": "AZURE_OPENAI_API_KEY",
    "ollama": None,  # No API key needed for local
}


def _ensure_api_key(provider: str) -> None:
    """Ensure the required API key is set in environment for the provider."""
    env_key = PROVIDER_API_KEY_MAP.get(provider)
    if env_key is None:
        return  # No key needed (e.g., ollama)

    if not os.environ.get(env_key):
        # Try to get from settings
        key_value = getattr(settings, env_key, None)
        if key_value:
            os.environ[env_key] = key_value
            logger.debug(f"Set {env_key} from app settings")


def create_model(
    provider: str = "openai",
    model_name: str = "gpt-4o",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    **kwargs: Any,
) -> BaseChatModel:
    """Create a chat model instance for the given provider and model.

    Args:
        provider: Provider name (openai, anthropic, google, azure, ollama, etc.)
        model_name: Model identifier
        temperature: Sampling temperature
        max_tokens: Maximum tokens in response
        **kwargs: Additional model parameters

    Returns:
        Configured BaseChatModel instance
    """
    _ensure_api_key(provider)

    model_kwargs: dict[str, Any] = {"temperature": temperature}
    if max_tokens is not None:
        model_kwargs["max_tokens"] = max_tokens
    model_kwargs.update(kwargs)

    try:
        # Use LangChain's init_chat_model for provider-agnostic model init
        model_string = f"{provider}:{model_name}"
        model = init_chat_model(model_string, **model_kwargs)
        logger.info(f"Created model: {provider}:{model_name}")
        return model
    except Exception as exc:
        logger.error(f"Failed to create model {provider}:{model_name}: {exc}")
        raise


class ModelHub:
    """Central registry for managing model configurations.

    Provides model caching, fallback chains, and cost-aware routing.
    """

    def __init__(self):
        self._cache: dict[str, BaseChatModel] = {}

    def get_model(
        self,
        provider: str = "openai",
        model_name: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        use_cache: bool = True,
    ) -> BaseChatModel:
        """Get or create a cached model instance.

        Args:
            provider: Model provider
            model_name: Model identifier
            temperature: Sampling temperature
            max_tokens: Max response tokens
            use_cache: Whether to cache the model instance

        Returns:
            Configured chat model
        """
        cache_key = f"{provider}:{model_name}:{temperature}:{max_tokens}"

        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        model = create_model(
            provider=provider,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if use_cache:
            self._cache[cache_key] = model

        return model

    def clear_cache(self):
        """Clear the model cache."""
        self._cache.clear()
        logger.info("Model cache cleared")


# Global model hub instance
model_hub = ModelHub()
