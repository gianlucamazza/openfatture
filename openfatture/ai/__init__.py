"""AI-powered assistance features for OpenFatture.

This package provides LLM-based agents for intelligent invoice management:
- Invoice description generation
- Tax advice and VAT suggestions
- Cash flow prediction
- Compliance checking

Architecture:
    - Domain: Core models (Message, Response, Context, Agent)
    - Providers: LLM provider abstractions (OpenAI, Anthropic, Ollama)
    - Agents: Specialized agents for different tasks
    - Config: Configuration management
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
    PromptManager,
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
    "PromptManager",
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
