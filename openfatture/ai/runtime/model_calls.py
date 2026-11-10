"""Bound model calls without multiplying SDK-managed retry attempts."""

from __future__ import annotations

import asyncio
import random
from typing import Any

from openfatture.ai.domain.response import AgentResponse
from openfatture.ai.providers.base import (
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)


def transient(error: BaseException) -> bool:
    cause = getattr(error, "original_error", None) or error
    status = getattr(cause, "status_code", None)
    return isinstance(
        cause,
        (
            ConnectionError,
            TimeoutError,
            ProviderRateLimitError,
            ProviderTimeoutError,
            ProviderUnavailableError,
        ),
    ) or (isinstance(status, int) and (status in {408, 409, 429} or status >= 500))


async def generate(provider: Any, *, timeout: float = 120, **kwargs: Any) -> AgentResponse:
    # OpenAI and Anthropic SDKs already make three attempts by default.
    sdk_retries = getattr(getattr(provider, "client", None), "max_retries", 0)
    attempts = 1 if isinstance(sdk_retries, int) and sdk_retries > 0 else 3
    for attempt in range(attempts):
        try:
            return await asyncio.wait_for(provider.generate(**kwargs), timeout)
        except Exception as exc:
            if attempt + 1 == attempts or not transient(exc):
                raise
            await asyncio.sleep(random.uniform(0, min(2**attempt, 4)))
    raise AssertionError("Unreachable")


async def generate_streamed(
    provider: Any, emit: Any, *, timeout: float = 120, **kwargs: Any
) -> AgentResponse:
    from openfatture.ai.domain.response import UsageMetrics
    from openfatture.ai.providers.base import BaseLLMProvider
    from openfatture.ai.runtime.contracts import current_accounting

    raw = getattr(provider, "provider", provider)
    if not isinstance(raw, BaseLLMProvider) or getattr(type(raw), "stream_structured", None) in {
        None,
        BaseLLMProvider.stream_structured,
    }:
        return await generate(provider, timeout=timeout, **kwargs)
    content = []
    calls = []
    usage = UsageMetrics(cost_known=False)
    complete = False
    try:
        async with asyncio.timeout(timeout):
            async for chunk in raw.stream_structured(**kwargs):
                if chunk.content:
                    content.append(chunk.content)
                    emit({"event": "content", "content": chunk.content})
                if chunk.tool_call:
                    calls.append(chunk.tool_call)
                if chunk.usage:
                    usage = chunk.usage
                complete |= chunk.is_final
        if not complete:
            raise RuntimeError("Provider stream ended without a final chunk")
        response = AgentResponse(
            content="".join(content), tool_calls=calls, usage=usage, metadata={"streamed": True}
        )
        accounting = current_accounting.get()
        if accounting:
            accounting.record(response)
        return response
    except BaseException:
        accounting = current_accounting.get()
        if accounting:
            accounting.incomplete = True
        raise
