from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openfatture.ai.domain.response import AgentResponse
from openfatture.ai.runtime.model_calls import generate


@pytest.mark.asyncio
async def test_transient_retries_stop_at_three() -> None:
    provider = MagicMock(client=None)
    provider.generate = AsyncMock(side_effect=ConnectionError("offline"))
    with patch("openfatture.ai.runtime.model_calls.asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(ConnectionError):
            await generate(provider)
    assert provider.generate.await_count == 3


@pytest.mark.asyncio
async def test_no_retry_for_invalid_request_or_sdk_retries() -> None:
    for error, retries in [(ValueError("invalid"), 0), (ConnectionError("offline"), 2)]:
        provider = MagicMock(client=MagicMock(max_retries=retries))
        provider.generate = AsyncMock(side_effect=error)
        with pytest.raises(type(error)):
            await generate(provider)
        assert provider.generate.await_count == 1


@pytest.mark.asyncio
async def test_timeout_cancels_inflight_model() -> None:
    import asyncio

    cancelled = asyncio.Event()

    async def blocked():
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    provider = MagicMock(client=MagicMock(max_retries=2))
    provider.generate = blocked
    with pytest.raises(TimeoutError):
        await generate(provider, timeout=0.01)
    assert cancelled.is_set()


@pytest.mark.asyncio
async def test_transient_then_success() -> None:
    provider = MagicMock(client=None)
    provider.generate = AsyncMock(side_effect=[ConnectionError(), AgentResponse(content="ok")])
    with patch("openfatture.ai.runtime.model_calls.asyncio.sleep", new_callable=AsyncMock):
        assert (await generate(provider)).content == "ok"


@pytest.mark.asyncio
async def test_streamed_provider_emits_tokens_and_records_usage_once() -> None:
    from openfatture.ai.domain.response import StreamChunk, UsageMetrics
    from openfatture.ai.providers.openai import OpenAIProvider
    from openfatture.ai.runtime.contracts import (
        AccountedProvider,
        TurnAccounting,
        current_accounting,
    )
    from openfatture.ai.runtime.model_calls import generate_streamed

    provider = object.__new__(OpenAIProvider)

    async def chunks(**kwargs):
        yield StreamChunk(content="first ")
        yield StreamChunk(content="second")
        yield StreamChunk(content="", is_final=True, usage=UsageMetrics(total_tokens=7))

    provider.stream_structured = chunks
    accounting = TurnAccounting()
    token = current_accounting.set(accounting)
    events = []
    try:
        response = await generate_streamed(AccountedProvider(provider), events.append)
    finally:
        current_accounting.reset(token)
    assert response.content == "first second"
    assert [e["content"] for e in events] == ["first ", "second"]
    assert accounting.calls == 1
    assert accounting.usage.total_tokens == 7


@pytest.mark.asyncio
async def test_partial_stream_is_not_retried() -> None:
    from openfatture.ai.domain.response import StreamChunk
    from openfatture.ai.providers.openai import OpenAIProvider
    from openfatture.ai.runtime.model_calls import generate_streamed

    provider = object.__new__(OpenAIProvider)
    calls = 0

    async def chunks(**kwargs):
        nonlocal calls
        calls += 1
        yield StreamChunk(content="partial")
        raise ConnectionError("lost stream")

    provider.stream_structured = chunks
    events = []
    with pytest.raises(ConnectionError):
        await generate_streamed(provider, events.append)
    assert calls == 1
    assert events[0]["content"] == "partial"
