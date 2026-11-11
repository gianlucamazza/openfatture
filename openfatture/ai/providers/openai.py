"""OpenAI provider implementation."""

from __future__ import annotations

import time
import warnings
from collections.abc import AsyncIterator
from typing import Any, cast

from openfatture.ai.domain.message import Message
from openfatture.ai.domain.response import (
    AgentResponse,
    ResponseStatus,
    StreamChunk,
    UsageMetrics,
)
from openfatture.ai.providers.base import (
    BaseLLMProvider,
    ProviderError,
)
from openfatture.ai.providers.openai_payload import (
    StreamedToolCalls,
    build_chat_messages,
    filter_extra_params,
    parse_tool_calls,
)
from openfatture.platform.extras import MissingExtraError
from openfatture.platform.logging import get_logger

try:
    from openai import AsyncOpenAI
except ImportError as exc:
    raise MissingExtraError("ai", feature="OpenAI provider", cause=exc) from exc

logger = get_logger(__name__)

# Lazy import tiktoken (not required at import time)
try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    logger.warning(
        "tiktoken_not_available",
        message="tiktoken not installed, using approximation for token counting",
    )


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI provider implementation.

    Supports GPT-5, GPT-4, GPT-3.5, and other OpenAI models.
    Uses tiktoken for accurate token counting when available.
    """

    # Pricing per 1M tokens (as of October 2025)
    PRICING = {
        # GPT-5 Series (2025)
        "gpt-5": {"input": 5.00, "output": 15.00},
        "gpt-5-turbo": {"input": 2.00, "output": 8.00},
        "gpt-5-mini": {"input": 0.20, "output": 0.80},
        # GPT-4 Series
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "gpt-4": {"input": 30.00, "output": 60.00},
        # GPT-3.5 Series (legacy)
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    }

    # Tiktoken encoding for token counting (initialized in __init__)
    _encoding: Any | None

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-5",  # Updated to GPT-5 (latest model - October 2025)
        temperature: float = 0.7,
        max_tokens: int = 2000,
        timeout: int = 30,
        base_url: str | None = None,
    ) -> None:
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: Model name (default: gpt-5)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds
            base_url: Custom API base URL
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.base_url = base_url

        # Check for deprecated models
        if model in self._get_deprecated_models():
            warnings.warn(
                f"Model '{model}' is deprecated and will be removed in a future version. "
                f"Please use a newer model like 'gpt-5' or 'gpt-4o'.",
                DeprecationWarning,
                stacklevel=2,
            )

        self.client = AsyncOpenAI(
            api_key=api_key,
            timeout=timeout,
            base_url=base_url,
        )

        # Initialize tiktoken encoding for accurate token counting
        self._encoding = None
        if TIKTOKEN_AVAILABLE:
            try:
                # tiktoken lacks type stubs, but returns Encoding object with encode() method
                self._encoding = cast(Any, tiktoken.encoding_for_model(self.model))
            except KeyError:
                # Fallback to cl100k_base for unknown models (GPT-4/GPT-5 compatible)
                logger.info(
                    "tiktoken_fallback",
                    model=self.model,
                    message="Using cl100k_base encoding as fallback",
                )
                self._encoding = cast(Any, tiktoken.get_encoding("cl100k_base"))

    def _get_deprecated_models(self) -> list[str]:
        """Get list of deprecated model names."""
        return ["gpt-3.5-turbo"]

    def _build_usage_metrics(self, usage: Any | None) -> UsageMetrics:
        """Create UsageMetrics from OpenAI usage payload."""
        # OpenAI uses prompt_tokens/completion_tokens (not input_tokens/output_tokens like Anthropic)
        prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
        completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
        total_tokens = getattr(usage, "total_tokens", 0) if usage else 0

        metrics = UsageMetrics(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )
        metrics.estimated_cost_usd = self.estimate_cost(metrics)
        metrics.cost_known = usage is not None and self.model in self.PRICING
        return metrics

    def _request_params(
        self,
        messages: list[Message],
        system_prompt: str | None,
        temperature: float | None,
        max_tokens: int | None,
        extra: dict[str, Any],
        *,
        stream: bool = False,
        include_usage: bool = False,
    ) -> dict[str, Any]:
        """Chat Completions request for this model.

        GPT-5 models use adaptive reasoning: they take no ``max_tokens`` and
        only the default temperature (1).
        """
        params: dict[str, Any] = {
            "model": self.model,
            "messages": build_chat_messages(messages, system_prompt),
        }
        if stream:
            params["stream"] = True
        max_output_tokens = self._get_max_output_tokens(max_tokens)
        if max_output_tokens and not self.model.startswith("gpt-5"):
            params["max_tokens"] = max_output_tokens
        temp = self._get_temperature(temperature)
        if not self.model.startswith("gpt-5") or temp == 1.0:
            params["temperature"] = temp
        if include_usage:
            params["stream_options"] = {"include_usage": True}
        params.update(filter_extra_params(extra))
        return params

    async def generate(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AgentResponse:
        """Generate response using OpenAI API."""
        start_time = time.time()

        try:
            api_params = self._request_params(
                messages, system_prompt, temperature, max_tokens, kwargs
            )

            logger.info(
                "openai_request_started",
                model=self.model,
                message_count=len(api_params["messages"]),
                temperature=self._get_temperature(temperature),
            )

            response = await self.client.chat.completions.create(**api_params)
            choice = response.choices[0]
            content = choice.message.content or ""
            tool_calls = parse_tool_calls(choice.message.tool_calls)

            usage = self._build_usage_metrics(response.usage)
            latency_ms = (time.time() - start_time) * 1000

            logger.info(
                "openai_request_completed",
                model=self.model,
                tokens=usage.total_tokens,
                cost_usd=usage.estimated_cost_usd,
                latency_ms=latency_ms,
                finish_reason=choice.finish_reason,
            )

            agent_response = AgentResponse(
                content=content,
                status=ResponseStatus.SUCCESS,
                model=self.model,
                provider=self.provider_name,
                usage=usage,
                latency_ms=latency_ms,
                tool_calls=tool_calls,
            )

            if choice.finish_reason:
                agent_response.metadata["finish_reason"] = choice.finish_reason

            return agent_response

        except Exception as e:
            logger.error("openai_unexpected_error", error=str(e), error_type=type(e).__name__)
            raise ProviderError(
                f"Unexpected error calling OpenAI: {e}",
                provider=self.provider_name,
                original_error=e,
            ) from e

    async def stream(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream response tokens from OpenAI."""
        try:
            stream_params = self._request_params(
                messages, system_prompt, temperature, max_tokens, kwargs, stream=True
            )

            logger.info(
                "openai_stream_started",
                model=self.model,
                message_count=len(stream_params["messages"]),
            )

            stream = await self.client.chat.completions.create(**stream_params)

            async for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content

        except Exception as e:
            logger.error("openai_stream_error", error=str(e))
            raise ProviderError(
                f"Error streaming from OpenAI: {e}",
                provider=self.provider_name,
                original_error=e,
            ) from e

    async def stream_structured(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream structured response chunks from OpenAI with tool call support."""
        try:
            stream_params = self._request_params(
                messages,
                system_prompt,
                temperature,
                max_tokens,
                kwargs,
                stream=True,
                include_usage=True,
            )

            logger.info(
                "openai_stream_structured_started",
                model=self.model,
                message_count=len(stream_params["messages"]),
            )

            tool_calls = StreamedToolCalls()
            finish_reason = None
            final_usage = None

            stream = await self.client.chat.completions.create(**stream_params)

            async for chunk in stream:
                if getattr(chunk, "usage", None):
                    final_usage = chunk.usage
                if not chunk.choices:
                    continue
                choice = chunk.choices[0]
                delta = choice.delta

                if delta.content:
                    yield StreamChunk(content=delta.content)

                if delta.tool_calls:
                    tool_calls.add(delta.tool_calls)

                if choice.finish_reason:
                    finish_reason = choice.finish_reason
                    for tool_call in tool_calls.complete():
                        yield StreamChunk(content="", tool_call=tool_call)

            yield StreamChunk(
                content="",
                is_final=True,
                finish_reason=finish_reason,
                usage=self._build_usage_metrics(final_usage),
            )

            usage = self._build_usage_metrics(final_usage)
            logger.info(
                "openai_stream_structured_completed",
                model=self.model,
                tokens=usage.total_tokens,
                cost_usd=usage.estimated_cost_usd,
                finish_reason=finish_reason,
            )

        except Exception as e:
            logger.error("openai_stream_structured_error", error=str(e))
            raise ProviderError(
                f"Error streaming from OpenAI: {e}",
                provider=self.provider_name,
                original_error=e,
            ) from e

    def count_tokens(self, text: str) -> int:
        """
        Count tokens using tiktoken for accurate counting.

        Falls back to approximation if tiktoken is not available.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        if self._encoding and TIKTOKEN_AVAILABLE:
            return len(self._encoding.encode(text))

        # Fallback approximation: ~4 chars per token
        return len(text) // 4

    def estimate_cost(self, usage: UsageMetrics) -> float:
        """Estimate cost based on token usage."""
        # Get pricing for model (use default if not found)
        pricing = self.PRICING.get(
            self.model,
            {"input": 0.0, "output": 0.0},  # Unknown price: cost_known is false
        )

        # Calculate cost per million tokens
        input_cost = (usage.prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (usage.completion_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def _get_max_output_tokens(self, override: int | None) -> int | None:
        """
        Determine the output token cap for a request.

        Args:
            override: Optional override value for the call

        Returns:
            Positive integer count or None to defer to model defaults
        """
        tokens = override if override is not None else self.max_tokens
        if tokens is None or tokens <= 0:
            return None
        return tokens

    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible."""
        try:
            # GPT-5 models don't support max_tokens parameters
            # They use adaptive reasoning instead
            params: dict[str, Any] = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Say OK"}],
            }

            # Only add max_tokens for non-GPT-5 models
            if not self.model.startswith("gpt-5"):
                params["max_tokens"] = 5

            response = await self.client.chat.completions.create(**params)
            return response is not None

        except Exception as e:
            logger.warning("openai_health_check_failed", error=str(e))
            return False

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "openai"

    @property
    def supports_streaming(self) -> bool:
        """OpenAI supports streaming."""
        return True

    @property
    def supports_tools(self) -> bool:
        """OpenAI supports function calling."""
        return True
