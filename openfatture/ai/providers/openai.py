"""OpenAI provider implementation."""

from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator
from typing import Any, cast

from openai import AsyncOpenAI, OpenAIError, RateLimitError
from openai.types.responses import Response as OpenAIResponse
from openai.types.responses.response_function_tool_call import ResponseFunctionToolCall
from openai.types.responses.response_output_item import ResponseOutputItem
from pydantic import BaseModel

from openfatture.ai.domain.message import Message, Role
from openfatture.ai.domain.response import (
    AgentResponse,
    ResponseStatus,
    StreamChunk,
    ToolCall,
    UsageMetrics,
)
from openfatture.ai.providers.base import (
    BaseLLMProvider,
    ProviderAuthError,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from openfatture.utils.logging import get_logger

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
                self._encoding = tiktoken.encoding_for_model(self.model)  # type: ignore
            except KeyError:
                # Fallback to cl100k_base for unknown models (GPT-4/GPT-5 compatible)
                logger.info(
                    "tiktoken_fallback",
                    model=self.model,
                    message="Using cl100k_base encoding as fallback",
                )
                self._encoding = tiktoken.get_encoding("cl100k_base")  # type: ignore

    _ALLOWED_EXTRA_PARAMS = {
        "tools",
        "tool_choice",
        "parallel_tool_calls",
        "metadata",
        "top_p",
        "top_logprobs",
        "max_tool_calls",
        "reasoning",
        "safety_identifier",
        "store",
        "user",
        "include",
        "prompt_cache_key",
        "service_tier",
        "stream_options",
        "conversation",
        "previous_response_id",
        "background",
        "text",
        "max_output_tokens",
    }

    def _build_usage_metrics(self, usage: Any | None) -> UsageMetrics:
        """Create UsageMetrics from OpenAI usage payload."""
        prompt_tokens = getattr(usage, "input_tokens", 0) if usage else 0
        completion_tokens = getattr(usage, "output_tokens", 0) if usage else 0
        total_tokens = getattr(usage, "total_tokens", 0) if usage else 0

        metrics = UsageMetrics(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )
        metrics.estimated_cost_usd = self.estimate_cost(metrics)
        return metrics

    def _build_message_input(self, role: str, content: str) -> dict[str, Any]:
        """Build Responses API message input item."""
        return {
            "role": role,
            "type": "message",
            "content": [
                {
                    "type": "input_text",
                    "text": content,
                }
            ],
        }

    def _build_responses_payload(
        self,
        messages: list[Message],
        system_prompt: str | None,
    ) -> tuple[str | None, list[dict[str, Any]]]:
        """
        Convert internal messages into Responses API instructions + input payload.
        """
        instructions_parts: list[str] = []
        inputs: list[dict[str, Any]] = []

        if system_prompt:
            instructions_parts.append(system_prompt)

        for message in messages:
            if message.role == Role.SYSTEM:
                instructions_parts.append(message.content)
                continue

            if message.role == Role.USER:
                inputs.append(self._build_message_input("user", message.content))
                continue

            if message.role == Role.ASSISTANT:
                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        tool_payload = self._convert_tool_call(tool_call)
                        if tool_payload:
                            inputs.append(tool_payload)

                if message.content:
                    inputs.append(self._build_message_input("assistant", message.content))
                continue

            if message.role == Role.TOOL:
                if not message.tool_call_id:
                    logger.warning(
                        "tool_message_missing_id",
                        message="Skipping tool message without tool_call_id",
                    )
                    continue

                inputs.append(
                    {
                        "type": "function_call_output",
                        "call_id": message.tool_call_id,
                        "output": message.content,
                    }
                )

        instructions = "\n\n".join(part for part in instructions_parts if part)
        return (instructions or None, inputs)

    def _convert_tool_call(self, tool_call: Any) -> dict[str, Any] | None:
        """Convert a stored tool call into Responses API format."""
        try:
            arguments: Any
            name: str | None
            call_id: str | None

            if isinstance(tool_call, ToolCall):
                arguments = tool_call.arguments
                name = tool_call.name
                call_id = tool_call.id
            else:
                # Handle OpenAI-style dict tool call
                if isinstance(tool_call, dict):
                    function = tool_call.get("function", {})
                    arguments = function.get("arguments") or tool_call.get("arguments", {})
                    name = function.get("name") or tool_call.get("name")
                    call_id = (
                        tool_call.get("id")
                        or tool_call.get("call_id")
                        or f"tool_call_{int(time.time() * 1000)}"
                    )
                else:
                    return None

            if arguments and isinstance(arguments, str):
                arguments_str = arguments
            else:
                arguments_str = json.dumps(arguments or {})

            return {
                "type": "function_call",
                "call_id": call_id or f"tool_call_{int(time.time() * 1000)}",
                "name": name or "unknown_tool",
                "arguments": arguments_str,
            }
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("tool_call_conversion_failed", error=str(exc))
            return None

    def _extract_tool_calls(self, output_items: list[ResponseOutputItem]) -> list[ToolCall]:
        """Extract tool calls from a Responses output array."""
        extracted: list[ToolCall] = []
        for item in output_items:
            if getattr(item, "type", None) != "function_call":
                continue

            function_item = cast(ResponseFunctionToolCall, item)
            try:
                arguments = json.loads(function_item.arguments) if function_item.arguments else {}
            except json.JSONDecodeError:
                logger.warning(
                    "tool_call_arguments_parse_failed",
                    tool_name=function_item.name,
                    arguments=function_item.arguments,
                )
                arguments = {}

            extracted.append(
                ToolCall(
                    id=function_item.id or function_item.call_id,
                    name=function_item.name,
                    arguments=arguments,
                )
            )
        return extracted

    def _extract_extra_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """Filter kwargs to supported Responses API parameters."""
        extra: dict[str, Any] = {}
        for key, value in params.items():
            if key == "response_format":
                logger.debug(
                    "responses_param_dropped",
                    param=key,
                    reason="Responses API uses `text.format` for structured outputs",
                )
                continue
            if key in self._ALLOWED_EXTRA_PARAMS:
                extra[key] = value
        return extra

    def _build_tool_call_from_state(self, state: dict[str, Any]) -> ToolCall:
        """Convert accumulated streaming state into a ToolCall."""
        arguments_raw = state.get("arguments") or "{}"
        try:
            arguments = (
                json.loads(arguments_raw) if isinstance(arguments_raw, str) else arguments_raw
            )
        except json.JSONDecodeError:
            logger.warning(
                "tool_call_arguments_stream_parse_failed",
                tool_name=state.get("name"),
                arguments=arguments_raw,
            )
            arguments = {}

        return ToolCall(
            id=str(state.get("id") or f"tool_call_{int(time.time() * 1000)}"),
            name=state.get("name", "unknown_tool"),
            arguments=arguments or {},
        )

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
            instructions, input_items = self._build_responses_payload(messages, system_prompt)

            logger.info(
                "openai_request_started",
                model=self.model,
                message_count=len(input_items),
                temperature=self._get_temperature(temperature),
            )

            max_output_tokens = self._get_max_output_tokens(max_tokens)

            api_params: dict[str, Any] = {
                "model": self.model,
                "input": input_items,
            }

            if instructions:
                api_params["instructions"] = instructions

            if max_output_tokens:
                api_params["max_output_tokens"] = max_output_tokens

            # Add temperature parameter only if the model supports it
            if not self.model.startswith("gpt-5"):
                api_params["temperature"] = self._get_temperature(temperature)

            extra_params = self._extract_extra_params(kwargs)
            api_params.update(extra_params)

            response: OpenAIResponse = await self.client.responses.create(**api_params)
            content = response.output_text or ""
            tool_calls = self._extract_tool_calls(response.output)

            usage = self._build_usage_metrics(response.usage)
            latency_ms = (time.time() - start_time) * 1000

            logger.info(
                "openai_request_completed",
                model=self.model,
                tokens=usage.total_tokens,
                cost_usd=usage.estimated_cost_usd,
                latency_ms=latency_ms,
                status=getattr(response.status, "value", None),
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

            if response.parallel_tool_calls:
                agent_response.metadata["parallel_tool_calls"] = response.parallel_tool_calls

            if response.status:
                agent_response.metadata["status"] = response.status

            return agent_response

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
            instructions, input_items = self._build_responses_payload(messages, system_prompt)

            logger.info(
                "openai_stream_started",
                model=self.model,
                message_count=len(input_items),
            )

            max_output_tokens = self._get_max_output_tokens(max_tokens)

            stream_params: dict[str, Any] = {
                "model": self.model,
                "input": input_items,
            }

            if instructions:
                stream_params["instructions"] = instructions

            if max_output_tokens:
                stream_params["max_output_tokens"] = max_output_tokens

            if not self.model.startswith("gpt-5"):
                stream_params["temperature"] = self._get_temperature(temperature)

            stream_params.update(self._extract_extra_params(kwargs))

            stream_manager = self.client.responses.stream(**stream_params)

            async with stream_manager as stream:
                async for event in stream:
                    if event.type == "response.output_text.delta" and getattr(event, "delta", None):
                        yield event.delta

                # Ensure stream fully consumed and resources released
                final_response = await stream.get_final_response()
                logger.info(
                    "openai_stream_completed",
                    model=self.model,
                    status=getattr(final_response.status, "value", None),
                )

        except Exception as e:
            logger.error("openai_stream_error", error=str(e))
            raise ProviderError(
                f"Error streaming from OpenAI: {e}",
                provider=self.provider_name,
                original_error=e,
            )

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
            instructions, input_items = self._build_responses_payload(messages, system_prompt)

            logger.info(
                "openai_stream_structured_started",
                model=self.model,
                message_count=len(input_items),
            )

            max_output_tokens = self._get_max_output_tokens(max_tokens)

            stream_params: dict[str, Any] = {
                "model": self.model,
                "input": input_items,
            }

            if instructions:
                stream_params["instructions"] = instructions

            if max_output_tokens:
                stream_params["max_output_tokens"] = max_output_tokens

            if not self.model.startswith("gpt-5"):
                stream_params["temperature"] = self._get_temperature(temperature)

            stream_params.update(self._extract_extra_params(kwargs))

            tool_state: dict[str, dict[str, Any]] = {}
            final_response: OpenAIResponse | None = None

            stream_manager = self.client.responses.stream(**stream_params)

            async with stream_manager as stream:
                async for event in stream:
                    event_type = getattr(event, "type", "")

                    if event_type == "response.output_text.delta":
                        try:
                            delta = getattr(event, "delta", "")
                            if delta:
                                yield StreamChunk(content=delta)
                        except AttributeError:
                            pass
                        continue

                    if event_type == "response.output_item.added":
                        item = getattr(event, "item", None)
                        if item and getattr(item, "type", None) == "function_call":
                            identifier = getattr(item, "id", None) or getattr(item, "call_id", None)
                            if identifier:
                                tool_state[identifier] = {
                                    "id": identifier,
                                    "name": getattr(item, "name", "unknown_tool"),
                                    "arguments": "",
                                }
                        continue

                    if event_type == "response.function_call_arguments.delta":
                        item_id = getattr(event, "item_id", None)
                        if item_id:
                            state = tool_state.setdefault(
                                item_id,
                                {
                                    "id": item_id,
                                    "name": getattr(event, "name", "unknown_tool"),
                                    "arguments": "",
                                },
                            )
                            state["arguments"] = getattr(
                                event, "snapshot", state.get("arguments", "")
                            )
                        continue

                    if event_type == "response.function_call_arguments.done":
                        item_id = getattr(event, "item_id", None)
                        if item_id:
                            state = tool_state.setdefault(
                                item_id,
                                {
                                    "id": item_id,
                                    "name": getattr(event, "name", "unknown_tool"),
                                    "arguments": "",
                                },
                            )
                            state["name"] = getattr(event, "name", state.get("name"))
                            state["arguments"] = getattr(
                                event, "arguments", state.get("arguments", "")
                            )
                            tool_call = self._build_tool_call_from_state(state)
                            yield StreamChunk(content="", tool_call=tool_call)
                            tool_state.pop(item_id, None)
                        continue

                    if event_type == "response.completed":
                        final_response = getattr(event, "response", None)

                if final_response is None:
                    final_response = await stream.get_final_response()

            finish_reason = None
            if final_response and final_response.status:
                finish_reason = final_response.status

            yield StreamChunk(content="", is_final=True, finish_reason=finish_reason)

            usage = self._build_usage_metrics(getattr(final_response, "usage", None))
            logger.info(
                "openai_stream_structured_completed",
                model=self.model,
                tokens=usage.total_tokens,
                cost_usd=usage.estimated_cost_usd,
                status=finish_reason,
            )

        except Exception as e:
            logger.error("openai_stream_structured_error", error=str(e))
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
        schema = response_model.model_json_schema()
        kwargs = dict(kwargs)
        kwargs["text"] = {
            "format": {
                "type": "json_schema",
                "name": response_model.__name__,
                "schema": schema,
                "strict": True,
            }
        }

        # Generate with JSON mode
        response = await self.generate(
            messages=messages,
            system_prompt=system_prompt,
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
            response = await self.client.responses.create(
                model=self.model,
                input="health_check",  # type: ignore[arg-type]
                max_output_tokens=5,
            )
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
