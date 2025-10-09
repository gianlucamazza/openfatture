"""
AI-powered assistance features for OpenFatture.

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

# Core domain models
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

# Configuration
from openfatture.ai.config import AISettings, get_ai_settings

# Providers
from openfatture.ai.providers import (
    AnthropicProvider,
    BaseLLMProvider,
    OllamaProvider,
    OpenAIProvider,
    ProviderError,
    create_provider,
)

__version__ = "1.0.0"

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
