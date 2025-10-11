"""Factory for creating LLM providers."""

from typing import Literal

from openfatture.ai.config import AISettings, get_ai_settings
from openfatture.ai.providers.anthropic import AnthropicProvider
from openfatture.ai.providers.base import BaseLLMProvider, ProviderError
from openfatture.ai.providers.ollama import OllamaProvider
from openfatture.ai.providers.openai import OpenAIProvider
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


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


def _pop_str_param(
    params: dict[str, str | int | float],
    name: str,
    default: str,
    provider: str,
) -> str:
    value = params.pop(name, default)
    if not isinstance(value, str):
        raise ProviderError(f"Parameter '{name}' must be a string", provider=provider)
    return value


def _pop_optional_str_param(
    params: dict[str, str | int | float],
    name: str,
    default: str | None,
    provider: str,
) -> str | None:
    if name not in params:
        return default
    value = params.pop(name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ProviderError(f"Parameter '{name}' must be a string", provider=provider)
    return value


def _pop_float_param(
    params: dict[str, str | int | float],
    name: str,
    default: float,
    provider: str,
) -> float:
    value = params.pop(name, default)
    if isinstance(value, (int, float)):
        return float(value)
    raise ProviderError(f"Parameter '{name}' must be a number", provider=provider)


def _pop_int_param(
    params: dict[str, str | int | float],
    name: str,
    default: int,
    provider: str,
) -> int:
    value = params.pop(name, default)
    if isinstance(value, int):
        return value
    raise ProviderError(f"Parameter '{name}' must be an integer", provider=provider)


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

    params = dict(kwargs)
    allowed_keys = {"model", "temperature", "max_tokens", "timeout", "base_url"}
    unexpected = set(params) - allowed_keys
    if unexpected:
        raise ProviderError(
            f"Unsupported parameters for OpenAI provider: {', '.join(sorted(unexpected))}",
            provider="openai",
        )

    model = _pop_str_param(params, "model", settings.openai_model, provider="openai")
    temperature = _pop_float_param(params, "temperature", settings.temperature, provider="openai")
    max_tokens = _pop_int_param(params, "max_tokens", settings.max_tokens, provider="openai")
    timeout = _pop_int_param(params, "timeout", settings.request_timeout_seconds, provider="openai")
    base_url = _pop_optional_str_param(params, "base_url", None, provider="openai")

    return OpenAIProvider(
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        base_url=base_url,
    )


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

    params = dict(kwargs)
    allowed_keys = {
        "model",
        "temperature",
        "max_tokens",
        "timeout",
        "base_url",
        "enable_prompt_caching",
    }
    unexpected = set(params) - allowed_keys
    if unexpected:
        raise ProviderError(
            f"Unsupported parameters for Anthropic provider: {', '.join(sorted(unexpected))}",
            provider="anthropic",
        )

    model = _pop_str_param(params, "model", settings.anthropic_model, provider="anthropic")
    temperature = _pop_float_param(
        params, "temperature", settings.temperature, provider="anthropic"
    )
    max_tokens = _pop_int_param(params, "max_tokens", settings.max_tokens, provider="anthropic")
    timeout = _pop_int_param(
        params, "timeout", settings.request_timeout_seconds, provider="anthropic"
    )
    base_url = _pop_optional_str_param(params, "base_url", None, provider="anthropic")

    enable_prompt_caching_value = params.pop("enable_prompt_caching", True)
    if not isinstance(enable_prompt_caching_value, bool):
        raise ProviderError(
            "Parameter 'enable_prompt_caching' must be a boolean",
            provider="anthropic",
        )
    enable_prompt_caching = enable_prompt_caching_value

    return AnthropicProvider(
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        base_url=base_url,
        enable_prompt_caching=enable_prompt_caching,
    )


def _create_ollama_provider(
    settings: AISettings,
    **kwargs: str | int | float,
) -> OllamaProvider:
    """Create Ollama provider."""
    # Ollama doesn't use api_key, only base_url
    # Build config dict without TypedDict to avoid api_key type error
    params = {k: v for k, v in kwargs.items() if k != "api_key"}
    allowed_keys = {"base_url", "model", "temperature", "max_tokens", "timeout"}
    unexpected = set(params) - allowed_keys
    if unexpected:
        raise ProviderError(
            f"Unsupported parameters for Ollama provider: {', '.join(sorted(unexpected))}",
            provider="ollama",
        )

    base_url = _pop_str_param(params, "base_url", settings.ollama_base_url, provider="ollama")
    model = _pop_str_param(params, "model", settings.ollama_model, provider="ollama")
    temperature = _pop_float_param(params, "temperature", settings.temperature, provider="ollama")
    max_tokens = _pop_int_param(params, "max_tokens", settings.max_tokens, provider="ollama")
    timeout = _pop_int_param(params, "timeout", settings.request_timeout_seconds, provider="ollama")

    return OllamaProvider(
        base_url=base_url,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )


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
