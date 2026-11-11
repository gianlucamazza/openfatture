"""Provider calls with retries and exponential backoff, shared by every agent."""

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from openfatture.ai.domain.agent_contract import AgentConfig
from openfatture.ai.domain.message import Message
from openfatture.ai.domain.response import AgentResponse
from openfatture.ai.providers.base import BaseLLMProvider, ProviderError


async def generate_with_retry(
    provider: BaseLLMProvider,
    config: AgentConfig,
    log: Any,
    messages: list[Message],
    **llm_kwargs: Any,
) -> AgentResponse:
    """
    Call the provider, retrying ``config.max_retries`` times on ``ProviderError``.

    A response above ``config.max_cost_per_request`` is logged, not rejected.

    Raises:
        ProviderError: If all retries fail
    """
    last_error = None

    for attempt in range(config.max_retries + 1):
        try:
            response = await provider.generate(
                messages=messages,
                system_prompt=config.system_prompt,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                **llm_kwargs,
            )

            if response.usage.estimated_cost_usd > config.max_cost_per_request:
                log.warning(
                    "agent_cost_exceeded",
                    agent=config.name,
                    cost=response.usage.estimated_cost_usd,
                    limit=config.max_cost_per_request,
                )

            return response

        except ProviderError as e:
            last_error = e

            log.warning(
                "agent_llm_call_failed",
                agent=config.name,
                attempt=attempt + 1,
                max_retries=config.max_retries,
                error=str(e),
            )

            if attempt >= config.max_retries:
                break

            # Wait before retrying (exponential backoff)
            await asyncio.sleep(2**attempt)

    raise last_error or ProviderError(
        "LLM call failed after all retries",
        provider=provider.provider_name,
    )


async def stream_with_retry(
    provider: BaseLLMProvider,
    config: AgentConfig,
    log: Any,
    messages: list[Message],
    **llm_kwargs: Any,
) -> AsyncIterator[str]:
    """
    Stream from the provider, retrying ``config.max_retries`` times on ``ProviderError``.

    Yields:
        str: Response chunks as they arrive

    Raises:
        ProviderError: If all retries fail
    """
    last_error = None

    for attempt in range(config.max_retries + 1):
        try:
            async for chunk in provider.stream(
                messages=messages,
                system_prompt=config.system_prompt,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                **llm_kwargs,
            ):
                yield chunk

            # If we got here, streaming succeeded
            return

        except ProviderError as e:
            last_error = e

            log.warning(
                "agent_llm_streaming_failed",
                agent=config.name,
                attempt=attempt + 1,
                max_retries=config.max_retries,
                error=str(e),
            )

            if attempt >= config.max_retries:
                break

            # Wait before retrying (exponential backoff)
            await asyncio.sleep(2**attempt)

    raise last_error or ProviderError(
        "LLM streaming call failed after all retries",
        provider=provider.provider_name,
    )
