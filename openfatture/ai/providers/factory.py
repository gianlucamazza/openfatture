"""Factory for creating LLM providers."""

from typing import Literal, TypedDict

from openfatture.ai.config import AISettings, get_ai_settings
from openfatture.ai.providers.anthropic import AnthropicProvider
from openfatture.ai.providers.base import BaseLLMProvider, ProviderError
from openfatture.ai.providers.ollama import OllamaProvider
from openfatture.ai.providers.openai import OpenAIProvider
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class ProviderConfig(TypedDict, total=False):
    """
    Type-safe configuration for LLM providers.

    All fields are optional to support partial configuration updates.
    Used for type-safe **kwargs unpacking in provider constructors.

    Fields:
        api_key: API key for authentication (OpenAI, Anthropic)
        base_url: Base URL for API (Ollama, or custom endpoints)
        model: Model name to use
        temperature: Generation temperature (0.0-2.0)
        max_tokens: Maximum tokens to generate
        timeout: Request timeout in seconds
    """

    api_key: str
    base_url: str
    model: str
    temperature: float
    max_tokens: int
    timeout: int


def create_provider(
    provider_type: Literal["openai", "anthropic", "ollama"] | None = None,
    settings: AISettings | None = None,
    **kwargs,
) -> BaseLLMProvider:
    """
    Create an LLM provider instance.

    Factory function that creates the appropriate provider based on
    configuration settings.

    Args:
        provider_type: Provider type (if None, uses settings)
        settings: AI settings (if None, uses global settings)
        **kwargs: Additional arguments passed to provider constructor

    Returns:
        BaseLLMProvider instance

    Raises:
        ProviderError: If provider cannot be created

    Examples:
        # Use default settings
        provider = create_provider()

        # Specify provider
        provider = create_provider(provider_type="anthropic")

        # Override settings
        provider = create_provider(
            provider_type="openai",
            model="gpt-4",
            temperature=0.5
        )
    """
    # Get settings if not provided
    if settings is None:
        settings = get_ai_settings()

    # Determine provider type
    provider = provider_type or settings.provider

    logger.info(
        "creating_llm_provider",
        provider=provider,
        model=settings.get_model_for_provider(),
    )

    try:
        if provider == "openai":
            return _create_openai_provider(settings, **kwargs)

        elif provider == "anthropic":
            return _create_anthropic_provider(settings, **kwargs)

        elif provider == "ollama":
            return _create_ollama_provider(settings, **kwargs)

        else:
            raise ProviderError(
                f"Unknown provider: {provider}. " f"Supported: openai, anthropic, ollama",
                provider=provider,
            )

    except Exception as e:
        logger.error(
            "provider_creation_failed",
            provider=provider,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise


def _create_openai_provider(
    settings: AISettings,
    **kwargs: str | int | float,
) -> OpenAIProvider:
    """Create OpenAI provider."""
    # Check if API key is configured
    api_key = settings.get_api_key_for_provider()

    if not api_key:
        raise ProviderError(
            "OpenAI API key not configured. "
            "Set OPENFATTURE_AI_OPENAI_API_KEY environment variable",
            provider="openai",
        )

    # Merge kwargs with settings (type-safe)
    config: ProviderConfig = {
        "api_key": api_key,
        "model": settings.openai_model,
        "temperature": settings.temperature,
        "max_tokens": settings.max_tokens,
        "timeout": settings.request_timeout_seconds,
    }
    # Update with kwargs (cast to match TypedDict)
    config.update(kwargs)  # type: ignore[typeddict-item]

    return OpenAIProvider(**config)


def _create_anthropic_provider(
    settings: AISettings,
    **kwargs: str | int | float,
) -> AnthropicProvider:
    """Create Anthropic provider."""
    # Check if API key is configured
    api_key = settings.get_api_key_for_provider()

    if not api_key:
        raise ProviderError(
            "Anthropic API key not configured. "
            "Set OPENFATTURE_AI_ANTHROPIC_API_KEY environment variable",
            provider="anthropic",
        )

    # Merge kwargs with settings (type-safe)
    config: ProviderConfig = {
        "api_key": api_key,
        "model": settings.anthropic_model,
        "temperature": settings.temperature,
        "max_tokens": settings.max_tokens,
        "timeout": settings.request_timeout_seconds,
    }
    # Update with kwargs (cast to match TypedDict)
    config.update(kwargs)  # type: ignore[typeddict-item]

    return AnthropicProvider(**config)


def _create_ollama_provider(
    settings: AISettings,
    **kwargs: str | int | float,
) -> OllamaProvider:
    """Create Ollama provider."""
    # Ollama doesn't use api_key, only base_url
    # Build config dict without TypedDict to avoid api_key type error
    config = {
        "base_url": settings.ollama_base_url,
        "model": settings.ollama_model,
        "temperature": settings.temperature,
        "max_tokens": settings.max_tokens,
        "timeout": settings.request_timeout_seconds,
    }
    # Update with kwargs, but remove api_key if present (Ollama doesn't use it)
    filtered_kwargs = {k: v for k, v in kwargs.items() if k != "api_key"}
    config.update(filtered_kwargs)

    return OllamaProvider(**config)  # type: ignore[arg-type]


async def test_provider(provider: BaseLLMProvider) -> bool:
    """
    Test if a provider is working.

    Args:
        provider: Provider instance to test

    Returns:
        True if provider is working, False otherwise
    """
    logger.info("testing_provider", provider=provider.provider_name, model=provider.model)

    try:
        is_healthy = await provider.health_check()

        if is_healthy:
            logger.info(
                "provider_test_success",
                provider=provider.provider_name,
                model=provider.model,
            )
        else:
            logger.warning(
                "provider_test_failed",
                provider=provider.provider_name,
                model=provider.model,
            )

        return is_healthy

    except Exception as e:
        logger.error(
            "provider_test_error",
            provider=provider.provider_name,
            error=str(e),
        )
        return False
