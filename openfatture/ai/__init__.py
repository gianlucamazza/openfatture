"""Business assistant for OpenFatture.

Architecture:
    - runtime: the assistant entry point and LangGraph tool loop
    - tools: assistant tools over the application services
    - providers: LLM provider adapters (OpenAI-compatible, Anthropic, Ollama)
    - domain: messages, responses and agent contracts
    - rag: optional knowledge search
"""

from typing import Any

# Same version as the distribution package (do not maintain a second number).
from openfatture import __version__

# Core domain models
# Configuration
from openfatture.ai.config import AISettings, get_ai_settings
from openfatture.ai.domain import (
    AgentConfig,
    AgentContext,
    AgentProtocol,
    AgentResponse,
    BaseAgent,
    Message,
    ResponseStatus,
    Role,
)


def __getattr__(name: str) -> Any:
    """Load LLM provider adapters only when a caller explicitly requests one."""
    if name in {
        "AnthropicProvider",
        "BaseLLMProvider",
        "OllamaProvider",
        "OpenAIProvider",
        "ProviderError",
        "create_provider",
    }:
        from openfatture.ai import providers

        return getattr(providers, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Domain
    "AgentConfig",
    "AgentContext",
    "AgentProtocol",
    "AgentResponse",
    "BaseAgent",
    "Message",
    "Role",
    "ResponseStatus",
    # Config
    "AISettings",
    "get_ai_settings",
    # Providers
    "BaseLLMProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "OllamaProvider",
    "create_provider",
    "ProviderError",
]
