"""Ollama provider implementation for local LLMs."""

import time
from collections.abc import AsyncIterator
from typing import Any

import httpx

from openfatture.ai.domain.message import Message
from openfatture.ai.domain.response import AgentResponse, ResponseStatus, UsageMetrics
from openfatture.ai.providers.base import (
    BaseLLMProvider,
    ProviderError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class OllamaProvider(BaseLLMProvider):
    """
    Ollama provider implementation for local LLMs.

    Supports running models locally via Ollama:
    - Llama 3, Llama 2
    - Mistral, Mixtral
    - CodeLlama
    - And many others

    No API key required - runs entirely locally.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        timeout: int = 60,  # Longer timeout for local inference
    ) -> None:
        """
        Initialize Ollama provider.

        Args:
            base_url: Ollama server URL
            model: Model name (must be pulled in Ollama)
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds
        """
        super().__init__(
            api_key=None,  # No API key needed
            base_url=base_url,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )

        # HTTP client for Ollama API
        self.client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def generate(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AgentResponse:
        """Generate response using Ollama API."""
        start_time = time.time()

        try:
            # Prepare prompt from messages
            prompt = self._messages_to_prompt(messages, system_prompt)

            logger.info(
                "ollama_request_started",
                model=self.model,
                prompt_length=len(prompt),
            )

            # Call Ollama generate API
            response = await self.client.post(
                "/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": self._get_temperature(temperature),
                    "num_predict": self._get_max_tokens(max_tokens),
                    "stream": False,
                    **kwargs,
                },
            )

            response.raise_for_status()
            data = response.json()

            # Extract response
            content = data.get("response", "")

            # Estimate token usage (Ollama doesn't provide exact counts)
            prompt_tokens = self.count_tokens(prompt)
            completion_tokens = self.count_tokens(content)

            usage = UsageMetrics(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                estimated_cost_usd=0.0,  # Free for local models
            )

            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000

            logger.info(
                "ollama_request_completed",
                model=self.model,
                tokens=usage.total_tokens,
                latency_ms=latency_ms,
            )

            return AgentResponse(
                content=content,
                status=ResponseStatus.SUCCESS,
                model=self.model,
                provider=self.provider_name,
                usage=usage,
                latency_ms=latency_ms,
            )

        except httpx.TimeoutException as e:
            logger.error("ollama_timeout", error=str(e))
            raise ProviderTimeoutError(
                f"Ollama request timeout after {self.timeout}s",
                provider=self.provider_name,
                original_error=e,
            )

        except httpx.ConnectError as e:
            logger.error("ollama_connection_error", error=str(e), base_url=self.base_url)
            raise ProviderUnavailableError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running (ollama serve)",
                provider=self.provider_name,
                original_error=e,
            )

        except httpx.HTTPStatusError as e:
            error_msg = str(e)

            if "model" in error_msg.lower() and "not found" in error_msg.lower():
                logger.error("ollama_model_not_found", model=self.model)
                raise ProviderError(
                    f"Model '{self.model}' not found. Pull it with: ollama pull {self.model}",
                    provider=self.provider_name,
                    original_error=e,
                )

            logger.error("ollama_http_error", error=error_msg, status=e.response.status_code)
            raise ProviderError(
                f"Ollama HTTP error: {error_msg}",
                provider=self.provider_name,
                original_error=e,
            )

        except Exception as e:
            logger.error("ollama_unexpected_error", error=str(e), error_type=type(e).__name__)
            raise ProviderError(
                f"Unexpected error calling Ollama: {e}",
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
        """Stream response tokens from Ollama."""
        try:
            # Prepare prompt
            prompt = self._messages_to_prompt(messages, system_prompt)

            logger.info(
                "ollama_stream_started",
                model=self.model,
                prompt_length=len(prompt),
            )

            # Stream API call
            async with self.client.stream(
                "POST",
                "/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": self._get_temperature(temperature),
                    "num_predict": self._get_max_tokens(max_tokens),
                    "stream": True,
                    **kwargs,
                },
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line:
                        import json

                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]

                            # Check if done
                            if data.get("done", False):
                                break

                        except json.JSONDecodeError:
                            continue

            logger.info("ollama_stream_completed", model=self.model)

        except Exception as e:
            logger.error("ollama_stream_error", error=str(e))
            raise ProviderError(
                f"Error streaming from Ollama: {e}",
                provider=self.provider_name,
                original_error=e,
            )

    def count_tokens(self, text: str) -> int:
        """
        Count tokens for Ollama.

        Since Ollama doesn't provide exact token counts,
        we use the same approximation as other providers.
        """
        return len(text) // 4

    def estimate_cost(self, usage: UsageMetrics) -> float:
        """Ollama is free (local models)."""
        return 0.0

    async def health_check(self) -> bool:
        """Check if Ollama server is accessible."""
        try:
            response = await self.client.get("/api/tags")
            return response.status_code == 200

        except Exception as e:
            logger.warning("ollama_health_check_failed", error=str(e))
            return False

    async def list_models(self) -> list[str]:
        """
        List available models on Ollama server.

        Returns:
            List of model names
        """
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()

            data = response.json()
            models = [model["name"] for model in data.get("models", [])]

            return models

        except Exception as e:
            logger.error("ollama_list_models_error", error=str(e))
            return []

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "ollama"

    @property
    def supports_streaming(self) -> bool:
        """Ollama supports streaming."""
        return True

    @property
    def supports_tools(self) -> bool:
        """Ollama doesn't natively support tool calling."""
        return False

    def _messages_to_prompt(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
    ) -> str:
        """
        Convert messages to a single prompt string.

        Ollama's simpler API expects a single prompt string
        rather than structured messages.

        Args:
            messages: List of Message objects
            system_prompt: Optional system prompt

        Returns:
            Formatted prompt string
        """
        parts = []

        # Add system prompt if provided
        if system_prompt:
            parts.append(f"System: {system_prompt}\n")

        # Add messages
        for msg in messages:
            if msg.role.value == "system":
                parts.append(f"System: {msg.content}\n")
            elif msg.role.value == "user":
                parts.append(f"User: {msg.content}\n")
            elif msg.role.value == "assistant":
                parts.append(f"Assistant: {msg.content}\n")

        # Add final prompt for assistant response
        parts.append("Assistant: ")

        return "\n".join(parts)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - close HTTP client."""
        await self.client.aclose()
