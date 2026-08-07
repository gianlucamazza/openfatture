"""LLM provider plugins, loaded on demand."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    # Import eagerly for type checkers only: at runtime the names are resolved
    # lazily by __getattr__ below so importing this package stays cheap.
    from openfatture.ai.providers.anthropic import AnthropicProvider
    from openfatture.ai.providers.base import (
        BaseLLMProvider,
        ProviderAuthError,
        ProviderError,
        ProviderRateLimitError,
        ProviderTimeoutError,
        ProviderUnavailableError,
    )
    from openfatture.ai.providers.factory import create_provider, test_provider
    from openfatture.ai.providers.ollama import OllamaProvider
    from openfatture.ai.providers.openai import OpenAIProvider


def __getattr__(name: str) -> Any:
    if name in {"AnthropicProvider", "OllamaProvider", "OpenAIProvider"}:
        module_name = {
            "AnthropicProvider": "anthropic",
            "OllamaProvider": "ollama",
            "OpenAIProvider": "openai",
        }[name]
        module = __import__(f"openfatture.ai.providers.{module_name}", fromlist=[name])
        return getattr(module, name)
    if name in {
        "BaseLLMProvider",
        "ProviderAuthError",
        "ProviderError",
        "ProviderRateLimitError",
        "ProviderTimeoutError",
        "ProviderUnavailableError",
    }:
        from openfatture.ai.providers import base

        return getattr(base, name)
    if name in {"create_provider", "test_provider"}:
        from openfatture.ai.providers import factory

        return getattr(factory, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Base
    "BaseLLMProvider",
    # Providers
    "OpenAIProvider",
    "AnthropicProvider",
    "OllamaProvider",
    # Factory
    "create_provider",
    "test_provider",
    # Exceptions
    "ProviderError",
    "ProviderAuthError",
    "ProviderRateLimitError",
    "ProviderTimeoutError",
    "ProviderUnavailableError",
]
