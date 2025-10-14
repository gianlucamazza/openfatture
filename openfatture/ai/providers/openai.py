"""OpenAI provider implementation."""

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any, cast

from openai import AsyncOpenAI, OpenAIError, RateLimitError
from pydantic import BaseModel

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

if TYPE_CHECKING:
    from openai._streaming import AsyncStream
    from openai.types.chat import (
        ChatCompletion,
        ChatCompletionChunk,
        ChatCompletionMessageParam,
        ChatCompletionToolMessageParam,
    )
else:  # pragma: no cover - runtime fallback when type hints unavailable
    AsyncStream = Any
    ChatCompletion = Any
    ChatCompletionChunk = Any
    ChatCompletionMessageParam = Any
    ChatCompletionToolMessageParam = Any


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

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-5",  # Updated to GPT-5 (October 2025)
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
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds
            base_url: Custom API base URL (for proxies)
        """
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )

        # Initialize async client
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )

        # Initialize tiktoken encoding for accurate token counting
        self._encoding = None
        if TIKTOKEN_AVAILABLE:
            try:
                self._encoding = tiktoken.encoding_for_model(self.model)
            except KeyError:
                # Fallback to cl100k_base for unknown models (GPT-4/GPT-5 compatible)
                logger.info(
                    "tiktoken_fallback",
                    model=self.model,
                    message="Using cl100k_base encoding as fallback",
                )
                self._encoding = tiktoken.get_encoding("cl100k_base")

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
            # Prepare messages
            prepared_messages = self._prepare_chat_messages(messages, system_prompt)

            logger.info(
                "openai_request_started",
                model=self.model,
                message_count=len(prepared_messages),
                temperature=self._get_temperature(temperature),
            )

            # Prepare token limit parameter (varies by model)
            max_tokens_value = self._get_max_tokens(max_tokens)
            token_param = (
                "max_completion_tokens" if self._uses_max_completion_tokens() else "max_tokens"
            )

            # Prepare API call parameters
            api_params = {
                "model": self.model,
                "messages": prepared_messages,
                **{token_param: max_tokens_value},
                **kwargs,
            }
            
            # Add temperature parameter only if the model supports it
            # GPT-5 doesn't support custom temperature values, only the default (1)
            if not self.model.startswith("gpt-5"):
                api_params["temperature"] = self._get_temperature(temperature)

            # Call API
            response_raw = await self.client.chat.completions.create(**api_params)
            response = cast("ChatCompletion", response_raw)

            # Extract response
            content = response.choices[0].message.content or ""
            finish_reason = response.choices[0].finish_reason

            # Calculate usage
            usage = UsageMetrics(
                prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                completion_tokens=response.usage.completion_tokens if response.usage else 0,
                total_tokens=response.usage.total_tokens if response.usage else 0,
            )

            # Estimate cost
            usage.estimated_cost_usd = self.estimate_cost(usage)

            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000

            logger.info(
                "openai_request_completed",
                model=self.model,
                tokens=usage.total_tokens,
                cost_usd=usage.estimated_cost_usd,
                latency_ms=latency_ms,
                finish_reason=finish_reason,
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
            logger.warning("openai_rate_limit", error=str(e))
            raise ProviderRateLimitError(
                "OpenAI rate limit exceeded",
                provider=self.provider_name,
                original_error=e,
            )

        except OpenAIError as e:
            error_msg = str(e)

            if "authentication" in error_msg.lower() or "api key" in error_msg.lower():
                logger.error("openai_auth_error", error=error_msg)
                raise ProviderAuthError(
                    f"OpenAI authentication failed: {error_msg}",
                    provider=self.provider_name,
                    original_error=e,
                )

            if "timeout" in error_msg.lower():
                logger.error("openai_timeout", error=error_msg)
                raise ProviderTimeoutError(
                    f"OpenAI request timeout: {error_msg}",
                    provider=self.provider_name,
                    original_error=e,
                )

            logger.error("openai_error", error=error_msg, error_type=type(e).__name__)
            raise ProviderError(
                f"OpenAI error: {error_msg}",
                provider=self.provider_name,
                original_error=e,
            )

        except Exception as e:
            logger.error("openai_unexpected_error", error=str(e), error_type=type(e).__name__)
            raise ProviderError(
                f"Unexpected error calling OpenAI: {e}",
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
        """Stream response tokens from OpenAI."""
        try:
            # Prepare messages
            prepared_messages = self._prepare_chat_messages(messages, system_prompt)

            logger.info(
                "openai_stream_started",
                model=self.model,
                message_count=len(prepared_messages),
            )

            # Prepare token limit parameter (varies by model)
            max_tokens_value = self._get_max_tokens(max_tokens)
            token_param = (
                "max_completion_tokens" if self._uses_max_completion_tokens() else "max_tokens"
            )

            # Prepare API call parameters
            stream_params = {
                "model": self.model,
                "messages": prepared_messages,
                "stream": True,
                **{token_param: max_tokens_value},
                **kwargs,
            }
            
            # Add temperature parameter only if the model supports it
            # GPT-5 doesn't support custom temperature values, only the default (1)
            if not self.model.startswith("gpt-5"):
                stream_params["temperature"] = self._get_temperature(temperature)

            # Stream API call
            stream_raw = await self.client.chat.completions.create(**stream_params)
            stream = cast("AsyncStream[ChatCompletionChunk]", stream_raw)

            # Yield chunks
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

            logger.info("openai_stream_completed", model=self.model)

        except Exception as e:
            logger.error("openai_stream_error", error=str(e))
            raise ProviderError(
                f"Error streaming from OpenAI: {e}",
                provider=self.provider_name,
                original_error=e,
            )

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
            {"input": 5.00, "output": 15.00},  # Default to GPT-5 pricing
        )

        # Calculate cost per million tokens
        input_cost = (usage.prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (usage.completion_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def _uses_max_completion_tokens(self) -> bool:
        """
        Check if model uses max_completion_tokens instead of max_tokens.

        OpenAI changed the API for newer models (GPT-5, GPT-4o):
        - Old models (GPT-4, GPT-3.5): use 'max_tokens'
        - New models (GPT-5, GPT-4o): use 'max_completion_tokens'

        Returns:
            True if model uses max_completion_tokens, False otherwise
        """
        # GPT-5 series and newer GPT-4o models use max_completion_tokens
        new_model_prefixes = ["gpt-5", "gpt-4o"]
        return any(self.model.startswith(prefix) for prefix in new_model_prefixes)

    async def generate_structured(
        self,
        messages: list[Message],
        response_model: type[BaseModel],
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> tuple[AgentResponse, BaseModel | None]:
        """
        Generate a structured response using Pydantic model.

        Uses OpenAI's JSON mode and validates output against Pydantic model.

        Args:
            messages: List of conversation messages
            response_model: Pydantic model class for validation
            system_prompt: Optional system prompt override
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            **kwargs: Provider-specific arguments

        Returns:
            Tuple of (AgentResponse, parsed_model or None)
        """
        import json

        # Add JSON instruction to system prompt
        json_instruction = f"\n\nRespond with valid JSON matching this schema:\n{response_model.model_json_schema()}"

        enhanced_system_prompt = (system_prompt or "") + json_instruction

        # Request JSON mode
        kwargs["response_format"] = {"type": "json_object"}

        # Generate with JSON mode
        response = await self.generate(
            messages=messages,
            system_prompt=enhanced_system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        # Try to parse as Pydantic model
        try:
            parsed_data = json.loads(response.content)
            model_instance = response_model(**parsed_data)

            logger.info(
                "structured_output_parsed",
                model=self.model,
                schema=response_model.__name__,
            )

            return response, model_instance

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(
                "structured_output_parse_failed",
                model=self.model,
                error=str(e),
                content_preview=response.content[:200],
            )

            return response, None

    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible."""
        try:
            # Prepare token limit parameter (varies by model)
            token_param = (
                "max_completion_tokens" if self._uses_max_completion_tokens() else "max_tokens"
            )

            # Try a simple API call
            response_raw = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                **{token_param: 5},
            )

            response = cast("ChatCompletion", response_raw)
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

    def _prepare_chat_messages(
        self,
        messages: list[Message],
        system_prompt: str | None,
    ) -> list[ChatCompletionMessageParam]:
        """
        Prepare messages in the format expected by OpenAI chat completions.

        Args:
            messages: Conversation history
            system_prompt: Optional system instruction prepended to the history

        Returns:
            List of typed message parameters for the OpenAI SDK
        """
        prepared: list[ChatCompletionMessageParam] = []

        if system_prompt:
            prepared.append(
                cast(ChatCompletionMessageParam, {"role": "system", "content": system_prompt})
            )

        for message in messages:
            if message.role == Role.SYSTEM:
                prepared.append(
                    cast(
                        ChatCompletionMessageParam,
                        {"role": "system", "content": message.content},
                    )
                )
            elif message.role == Role.USER:
                prepared.append(
                    cast(
                        ChatCompletionMessageParam,
                        {"role": "user", "content": message.content},
                    )
                )
            elif message.role == Role.ASSISTANT:
                prepared.append(
                    cast(
                        ChatCompletionMessageParam,
                        {"role": "assistant", "content": message.content},
                    )
                )
            elif message.role == Role.TOOL:
                if not message.tool_call_id:
                    logger.warning(
                        "tool_message_missing_id",
                        message="Skipping tool message without tool_call_id",
                    )
                    continue
                tool_message: ChatCompletionToolMessageParam = cast(
                    ChatCompletionToolMessageParam,
                    {
                        "role": "tool",
                        "content": message.content,
                        "tool_call_id": message.tool_call_id,
                    },
                )
                prepared.append(tool_message)

        return prepared
