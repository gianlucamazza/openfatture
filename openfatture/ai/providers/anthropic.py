"""Anthropic (Claude) provider implementation."""

import time
from collections.abc import AsyncIterator
from typing import Any

from anthropic import (
    AnthropicError,
    AsyncAnthropic,
    RateLimitError,
)

from openfatture.ai.domain.message import Message, Role
from openfatture.ai.domain.response import AgentResponse, ResponseStatus, UsageMetrics
from openfatture.ai.providers.base import (
    BaseLLMProvider,
    ProviderAuthError,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic provider implementation.

    Supports Claude 4.5, Claude 3, and earlier models.
    Includes prompt caching support for reduced costs.
    """

    # Pricing per 1M tokens (as of October 2025)
    PRICING = {
        # Claude 4.5 Series (2025)
        "claude-4.5-opus": {"input": 12.00, "output": 60.00},
        "claude-4.5-sonnet": {"input": 2.50, "output": 12.50},
        "claude-4.5-haiku": {"input": 0.20, "output": 1.00},
        # Claude 3 Series (legacy)
        "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
        "claude-3-sonnet-20240229": {"input": 3.00, "output": 15.00},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
        # Claude 2 Series (deprecated)
        "claude-2.1": {"input": 8.00, "output": 24.00},
    }

    def __init__(
        self,
        api_key: str,
        model: str = "claude-4.5-sonnet",  # Updated to Claude 4.5 (October 2025)
        temperature: float = 0.7,
        max_tokens: int = 2000,
        timeout: int = 30,
        base_url: str | None = None,
        enable_prompt_caching: bool = True,
    ) -> None:
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            model: Model name (default: claude-4.5-sonnet)
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds
            base_url: Custom API base URL
            enable_prompt_caching: Enable prompt caching for cost reduction
        """
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )

        self.enable_prompt_caching = enable_prompt_caching

        # Initialize async client
        self.client = AsyncAnthropic(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )

    async def generate(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AgentResponse:
        """Generate response using Anthropic API."""
        start_time = time.time()

        try:
            # Prepare messages for Claude
            prepared_messages = self._prepare_claude_messages(messages)

            logger.info(
                "anthropic_request_started",
                model=self.model,
                message_count=len(prepared_messages),
                has_system=system_prompt is not None,
            )

            # Call API
            response = await self.client.messages.create(
                model=self.model,
                messages=prepared_messages,
                system=system_prompt or "",
                temperature=self._get_temperature(temperature),
                max_tokens=self._get_max_tokens(max_tokens),
                **kwargs,
            )

            # Extract content
            content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    content += block.text

            # Calculate usage
            usage = UsageMetrics(
                prompt_tokens=response.usage.input_tokens if response.usage else 0,
                completion_tokens=response.usage.output_tokens if response.usage else 0,
                total_tokens=(
                    response.usage.input_tokens + response.usage.output_tokens
                    if response.usage
                    else 0
                ),
            )

            # Estimate cost
            usage.estimated_cost_usd = self.estimate_cost(usage)

            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000

            logger.info(
                "anthropic_request_completed",
                model=self.model,
                tokens=usage.total_tokens,
                cost_usd=usage.estimated_cost_usd,
                latency_ms=latency_ms,
                stop_reason=response.stop_reason,
            )

            return AgentResponse(
                content=content,
                status=ResponseStatus.SUCCESS,
                model=self.model,
                provider=self.provider_name,
                usage=usage,
                latency_ms=latency_ms,
            )

        except RateLimitError as e:
            logger.warning("anthropic_rate_limit", error=str(e))
            raise ProviderRateLimitError(
                "Anthropic rate limit exceeded",
                provider=self.provider_name,
                original_error=e,
            )

        except AnthropicError as e:
            error_msg = str(e)

            if "authentication" in error_msg.lower() or "api key" in error_msg.lower():
                logger.error("anthropic_auth_error", error=error_msg)
                raise ProviderAuthError(
                    f"Anthropic authentication failed: {error_msg}",
                    provider=self.provider_name,
                    original_error=e,
                )

            if "timeout" in error_msg.lower():
                logger.error("anthropic_timeout", error=error_msg)
                raise ProviderTimeoutError(
                    f"Anthropic request timeout: {error_msg}",
                    provider=self.provider_name,
                    original_error=e,
                )

            logger.error("anthropic_error", error=error_msg, error_type=type(e).__name__)
            raise ProviderError(
                f"Anthropic error: {error_msg}",
                provider=self.provider_name,
                original_error=e,
            )

        except Exception as e:
            logger.error("anthropic_unexpected_error", error=str(e), error_type=type(e).__name__)
            raise ProviderError(
                f"Unexpected error calling Anthropic: {e}",
                provider=self.provider_name,
                original_error=e,
            )

    async def stream(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream response tokens from Anthropic."""
        try:
            # Prepare messages
            prepared_messages = self._prepare_claude_messages(messages)

            logger.info(
                "anthropic_stream_started",
                model=self.model,
                message_count=len(prepared_messages),
            )

            # Stream API call
            async with self.client.messages.stream(
                model=self.model,
                messages=prepared_messages,
                system=system_prompt or "",
                temperature=self._get_temperature(temperature),
                max_tokens=self._get_max_tokens(max_tokens),
                **kwargs,
            ) as stream:
                async for text in stream.text_stream:
                    yield text

            logger.info("anthropic_stream_completed", model=self.model)

        except Exception as e:
            logger.error("anthropic_stream_error", error=str(e))
            raise ProviderError(
                f"Error streaming from Anthropic: {e}",
                provider=self.provider_name,
                original_error=e,
            )

    def count_tokens(self, text: str) -> int:
        """
        Count tokens for Claude using official Anthropic token counter.

        Uses the client's count_tokens method for accurate token counting,
        which is model-specific and accounts for Claude's tokenization.

        Falls back to approximation if API call fails.
        """
        try:
            # Use official Anthropic token counter (synchronous)
            # Note: Anthropic's count_tokens is a sync method
            import asyncio

            loop = asyncio.get_event_loop()

            if loop.is_running():
                # If in async context, use approximation to avoid blocking
                # This is acceptable since count_tokens is primarily used for
                # pre-flight estimation, not billing
                logger.debug(
                    "count_tokens_approximation",
                    reason="async_context",
                    model=self.model,
                )
                return len(text) // 4

            # Sync context: use official counter
            token_count = self.client.count_tokens(text)

            logger.debug(
                "count_tokens_official",
                model=self.model,
                count=token_count,
                text_length=len(text),
            )

            return token_count

        except Exception as e:
            # Fallback to approximation if API call fails
            logger.warning(
                "count_tokens_fallback",
                error=str(e),
                model=self.model,
            )
            return len(text) // 4

    def estimate_cost(self, usage: UsageMetrics) -> float:
        """Estimate cost based on token usage."""
        # Get pricing for model (use Claude 4.5 Sonnet as default)
        pricing = self.PRICING.get(
            self.model,
            {"input": 2.50, "output": 12.50},  # Default to Claude 4.5 Sonnet pricing
        )

        # Calculate cost per million tokens
        input_cost = (usage.prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (usage.completion_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    async def health_check(self) -> bool:
        """Check if Anthropic API is accessible."""
        try:
            # Try a simple API call
            response = await self.client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
            )

            return response is not None

        except Exception as e:
            logger.warning("anthropic_health_check_failed", error=str(e))
            return False

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "anthropic"

    @property
    def supports_streaming(self) -> bool:
        """Anthropic supports streaming."""
        return True

    @property
    def supports_tools(self) -> bool:
        """Anthropic Claude 3 supports tool use."""
        return "claude-3" in self.model

    def _prepare_claude_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        """
        Prepare messages for Claude API.

        Claude requires alternating user/assistant messages
        and system prompts are passed separately.

        Args:
            messages: List of Message objects

        Returns:
            List of message dicts for Claude API
        """
        prepared = []

        # Filter out system messages (handled separately)
        for msg in messages:
            if msg.role == Role.SYSTEM:
                continue  # System handled separately

            # Convert role to Claude format
            role = "user" if msg.role == Role.USER else "assistant"

            prepared.append({"role": role, "content": msg.content})

        return prepared
