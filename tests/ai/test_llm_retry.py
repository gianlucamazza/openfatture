"""Retries, backoff and cost warnings of agent provider calls."""

from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import MagicMock

import pytest

from openfatture.ai.domain import llm_retry
from openfatture.ai.domain.agent_contract import AgentConfig
from openfatture.ai.domain.message import Message, Role
from openfatture.ai.domain.response import AgentResponse, UsageMetrics
from openfatture.ai.providers.base import BaseLLMProvider, ProviderError

MESSAGES = [Message(role=Role.USER, content="ciao")]


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    delays: list[float] = []

    async def record(delay: float) -> None:
        delays.append(delay)

    monkeypatch.setattr(llm_retry.asyncio, "sleep", record)
    return delays


def _provider(outcomes: list[AgentResponse | ProviderError]) -> BaseLLMProvider:
    provider = MagicMock(spec=BaseLLMProvider)
    provider.provider_name = "fake"

    async def generate(**kwargs: Any) -> AgentResponse:
        outcome = outcomes.pop(0)
        if isinstance(outcome, ProviderError):
            raise outcome
        return outcome

    provider.generate = generate
    return provider


def _config(**overrides: Any) -> AgentConfig:
    return AgentConfig(name="agent", description="test", **overrides)


@pytest.mark.asyncio
async def test_generate_retries_with_backoff_and_warns_on_cost(sleeps: list[float]):
    expensive = AgentResponse(content="ok", usage=UsageMetrics(estimated_cost_usd=2.0))
    failures: list[AgentResponse | ProviderError] = [
        ProviderError("busy", provider="fake"),
        ProviderError("busy", provider="fake"),
        expensive,
    ]
    log = MagicMock()
    result = await llm_retry.generate_with_retry(
        _provider(failures), _config(max_retries=2), log, MESSAGES
    )
    assert result is expensive
    assert sleeps == [1, 2]
    events = [call.args[0] for call in log.warning.call_args_list]
    assert events == ["agent_llm_call_failed", "agent_llm_call_failed", "agent_cost_exceeded"]


@pytest.mark.asyncio
async def test_generate_raises_the_last_error(sleeps: list[float]):
    last = ProviderError("down", provider="fake")
    with pytest.raises(ProviderError) as raised:
        await llm_retry.generate_with_retry(
            _provider([ProviderError("first", provider="fake"), last]),
            _config(max_retries=1),
            MagicMock(),
            MESSAGES,
        )
    assert raised.value is last
    assert sleeps == [1]


@pytest.mark.asyncio
async def test_stream_raises_after_retries(sleeps: list[float]):
    provider = MagicMock(spec=BaseLLMProvider)
    provider.provider_name = "fake"

    async def stream(**kwargs: Any) -> AsyncIterator[str]:
        raise ProviderError("down", provider="fake")
        yield ""

    provider.stream = stream
    with pytest.raises(ProviderError, match="down"):
        async for _ in llm_retry.stream_with_retry(
            provider, _config(max_retries=1), MagicMock(), MESSAGES
        ):
            pass
    assert sleeps == [1]
