"""Base LLM provider abstraction."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from openfatture.ai.domain.message import Message
from openfatture.ai.domain.response import AgentResponse, UsageMetrics


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    Provides a unified interface for different LLM services
    (OpenAI, Anthropic, Ollama, etc.).

    All providers must implement:
    - Async generation
    - Streaming support
    - Token counting
    - Health checks
    - Cost estimation
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "default",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        timeout: int = 30,
    ) -> None:
        """
        Initialize provider.

        Args:
            api_key: API key for authentication (if needed)
            base_url: Base URL for API (for custom endpoints)
            model: Model name to use
            temperature: Generation temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

    @abstractmethod
    async def generate(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AgentResponse:
        """
        Generate a response from the LLM.

        Args:
            messages: List of conversation messages
            system_prompt: Optional system prompt override
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            **kwargs: Provider-specific arguments

        Returns:
            AgentResponse with content and metadata

        Raises:
            ProviderError: If generation fails
        """
        pass

    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Stream response tokens from the LLM.

        Args:
            messages: List of conversation messages
            system_prompt: Optional system prompt override
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            **kwargs: Provider-specific arguments

        Yields:
            Response tokens as strings

        Raises:
            ProviderError: If streaming fails
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text for this provider.

        Different providers use different tokenizers, so this
        must be implemented per provider.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        pass

    @abstractmethod
    def estimate_cost(self, usage: UsageMetrics) -> float:
        """
        Estimate cost in USD for token usage.

        Args:
            usage: Usage metrics with token counts

        Returns:
            Estimated cost in USD
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if provider is available and working.

        Returns:
            True if provider is healthy, False otherwise
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get the provider name (e.g., 'openai', 'anthropic')."""
        pass

    @property
    @abstractmethod
    def supports_streaming(self) -> bool:
        """Check if this provider supports streaming."""
        pass

    @property
    @abstractmethod
    def supports_tools(self) -> bool:
        """Check if this provider supports tool/function calling."""
        pass

    def _prepare_messages(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Prepare messages for API call.

        Handles system prompt injection and message formatting.

        Args:
            messages: List of Message objects
            system_prompt: Optional system prompt to prepend

        Returns:
            List of message dicts for API
        """
        prepared = []

        # Add system prompt if provided
        if system_prompt:
            prepared.append({"role": "system", "content": system_prompt})

        # Convert Message objects to dicts
        for msg in messages:
            prepared.append(msg.to_dict())

        return prepared

    def _get_temperature(self, override: float | None = None) -> float:
        """Get temperature with optional override."""
        return override if override is not None else self.temperature

    def _get_max_tokens(self, override: int | None = None) -> int:
        """Get max tokens with optional override."""
        return override if override is not None else self.max_tokens


class ProviderError(Exception):
    """Base exception for provider errors."""

    def __init__(
        self,
        message: str,
        provider: str,
        original_error: Exception | None = None,
    ) -> None:
        """
        Initialize provider error.

        Args:
            message: Error message
            provider: Provider name
            original_error: Original exception if wrapped
        """
        super().__init__(message)
        self.provider = provider
        self.original_error = original_error


class ProviderAuthError(ProviderError):
    """Authentication error (invalid API key, etc.)."""

    pass


class ProviderRateLimitError(ProviderError):
    """Rate limit exceeded."""

    pass


class ProviderTimeoutError(ProviderError):
    """Request timeout."""

    pass


class ProviderUnavailableError(ProviderError):
    """Provider service unavailable."""

    pass
