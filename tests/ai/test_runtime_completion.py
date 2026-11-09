"""End-to-end runtime outcomes and accounting with deterministic providers."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from openfatture.ai.domain.response import AgentResponse, ResponseStatus, ToolCall, UsageMetrics
from openfatture.ai.runtime.service import AssistantRuntime
from openfatture.ai.tools.models import Tool
from openfatture.ai.tools.registry import ToolRegistry


def runtime(monkeypatch, backend, responses, *, interaction=None):
    registry = ToolRegistry()
    registry.register(Tool(name="read_test", description="Read data", func=lambda: {"ok": True}))
    provider = MagicMock()
    provider.provider_name = "openai"
    provider.model = "test"
    provider.supports_tools = True
    provider.generate = AsyncMock(side_effect=responses)
    monkeypatch.setattr("openfatture.ai.runtime.service.get_tool_registry", lambda: registry)
    return AssistantRuntime(provider=provider, backend=backend, interaction=interaction), registry


def answer(content="done", *, tool=False):
    return AgentResponse(
        content=content,
        usage=UsageMetrics(
            prompt_tokens=8, completion_tokens=2, total_tokens=10, estimated_cost_usd=0.001
        ),
        tool_calls=[ToolCall(id="test", name="read_test", arguments={})] if tool else [],
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("backend", ["chat", "langgraph"])
@pytest.mark.parametrize("stream", [False, True])
async def test_multicall_usage_is_counted_once(monkeypatch, backend, stream):
    instance, _ = runtime(monkeypatch, backend, [answer("", tool=True), answer()])
    if stream:
        _ = [event async for event in instance.stream("read")]
    else:
        await instance.run("read")
    assert instance.last_response.success
    assert instance.last_response.usage.total_tokens == 20
    assert instance.total_usage.total_tokens == 20
    assert instance.last_response.metadata["usage_complete"]
    assert instance.turn_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("backend", ["chat", "langgraph"])
async def test_cancellation_preserves_completed_call_usage(monkeypatch, backend):
    instance, _ = runtime(monkeypatch, backend, [])
    entered = asyncio.Event()
    call = 0

    async def generate(**kwargs):
        nonlocal call
        call += 1
        if call == 1:
            return answer("", tool=True)
        entered.set()
        await asyncio.Event().wait()

    instance._provider.provider.generate.side_effect = generate

    async def consume():
        async for _event in instance.stream("read"):
            pass

    task = asyncio.create_task(consume())
    await asyncio.wait_for(entered.wait(), 10)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert instance.last_response.status == ResponseStatus.PARTIAL
    assert instance.total_usage.total_tokens == 10
    assert not instance.last_response.metadata["usage_complete"]
    assert instance.last_response.metadata["tool_outcomes"][0]["success"]
    assert instance.turn_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("backend", ["chat", "langgraph"])
async def test_stream_error_is_not_saved_as_success(monkeypatch, backend):
    response = AgentResponse(content="", status=ResponseStatus.ERROR, error="unavailable")
    instance, _ = runtime(monkeypatch, backend, [response])
    _ = [event async for event in instance.stream("read")]
    assert instance.last_response.status == ResponseStatus.ERROR
    assert not instance.last_response.metadata["usage_complete"]


@pytest.mark.asyncio
async def test_callbacks_are_session_scoped(monkeypatch):
    ui = SimpleNamespace(
        confirm=AsyncMock(return_value=False), activity=AsyncMock(), finished=AsyncMock()
    )
    first, registry = runtime(monkeypatch, "langgraph", [], interaction=ui)
    second = AssistantRuntime(provider=first._provider.provider, backend="langgraph")
    assert registry.confirmation_callback is None
    assert first._tool_registry.confirmation_callback is ui.confirm
    assert second._tool_registry.confirmation_callback is None


@pytest.mark.asyncio
async def test_interrupted_turn_is_persisted_with_partial_usage(monkeypatch, tmp_path):
    from openfatture.ai.session.file_store import FileSessionStore

    store = FileSessionStore(sessions_dir=tmp_path)
    monkeypatch.setattr("openfatture.ai.session.get_session_store", lambda: store)
    instance, _ = runtime(
        monkeypatch, "langgraph", [answer("", tool=True), RuntimeError("offline")]
    )
    from openfatture.ai.session.models import ChatSession

    instance.persist_session = True
    instance._session = ChatSession()
    instance._session_store = store
    with pytest.raises(RuntimeError):
        _ = [event async for event in instance.stream("read")]
    loaded = store.load(instance.session_id)
    assert loaded.messages[-1].metadata["status"] == "error"
    assert loaded.messages[-1].total_tokens == 10
    assert loaded.messages[-1].metadata["usage_complete"] is False
    assert loaded.metadata.total_tokens == 10


@pytest.mark.asyncio
@pytest.mark.parametrize("backend", ["chat", "langgraph"])
@pytest.mark.parametrize("stream", [False, True])
async def test_noninteractive_confirmation_is_reported_without_execution(
    monkeypatch, backend, stream
):
    instance, registry = runtime(monkeypatch, backend, [answer("", tool=True), answer()])
    tool = registry.get_tool("read_test")
    tool.requires_confirmation = True
    calls = []
    tool.func = lambda: calls.append(True)
    if stream:
        _ = [event async for event in instance.stream("read")]
    else:
        await instance.run("read")
    assert not calls
    assert not instance.last_response.success
    assert instance.last_response.error == "confirmation_required"
    assert instance.last_response.metadata["tool_outcomes"][0]["result"] == "confirmation_required"
