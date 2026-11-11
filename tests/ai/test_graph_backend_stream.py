"""Event translation of GraphAssistantBackend.stream for both tool-graph paths."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, AsyncIterator, Callable
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from openfatture.ai.domain.context import ChatContext
from openfatture.ai.domain.response import AgentResponse, ResponseStatus, UsageMetrics
from openfatture.ai.runtime.graph_backend import GraphAssistantBackend
from openfatture.ai.streaming.events import StreamEvent

INITIAL: dict[str, Any] = {"messages": [], "iteration": 0, "status": "", "content": ""}

CUSTOM_TOOL_UPDATES: list[Any] = [
    {"event": "tool_start", "tool": "list_invoices", "parameters": None, "tool_call_id": "c1"},
    {"event": "tool_finished", "tool": "list_invoices", "success": True, "result": [1]},
    {"event": "tool_finished", "success": False, "result": "boom", "tool_call_id": "c2"},
    {"event": "tool_progress", "tool": "ignored"},
]
TOOL_EVENTS = [
    ("tool_start", {"tool_name": "list_invoices", "parameters": {}}, {"tool_call_id": "c1"}),
    (
        "tool_result",
        {"tool_name": "list_invoices", "result": "[1]", "duration_ms": None},
        {"tool_call_id": None},
    ),
    ("tool_error", {"tool_name": "unknown", "error": "boom"}, {"tool_call_id": "c2"}),
]


def _backend() -> GraphAssistantBackend:
    provider = MagicMock(provider_name="openai", supports_tools=True, model="m")
    registry = MagicMock()
    registry.list_tools.return_value = []
    return GraphAssistantBackend(provider=provider, tool_registry=registry)


def _context(user_input: str = "hello", **metadata: Any) -> ChatContext:
    context = ChatContext(user_input=user_input, available_tools=["list_invoices"])
    context.metadata.update(metadata)
    return context


def _dump(events: list[StreamEvent]) -> list[tuple[str, Any, dict[str, Any]]]:
    return [(e.type.value, e.data, e.metadata) for e in events]


async def _collect(backend: GraphAssistantBackend, context: ChatContext) -> list[StreamEvent]:
    return [event async for event in backend.stream(context)]


class FakeGraph:
    def __init__(self, parts: list[tuple[str, Any]]) -> None:
        self.parts = parts
        self.calls: list[dict[str, Any]] = []

    async def astream(self, initial: dict[str, Any], **kwargs: Any) -> AsyncIterator[Any]:
        self.calls.append({"initial": initial, **kwargs})
        for mode, data in self.parts:
            yield {"type": mode, "data": data}


def _run_graph(backend: GraphAssistantBackend, parts: list[tuple[str, Any]]) -> list[StreamEvent]:
    graph = FakeGraph(parts)
    with (
        patch.object(backend, "_get_tool_graph", return_value=graph),
        patch.object(backend, "_initial_tool_state", return_value=dict(INITIAL)),
    ):
        events = asyncio.run(_collect(backend, _context()))
    assert graph.calls[0]["stream_mode"] == ["updates", "custom"]
    assert graph.calls[0]["config"] == {"recursion_limit": 2 * backend.max_iterations + 2}
    return events


def test_graph_stream_translates_custom_and_node_updates() -> None:
    events = _run_graph(
        _backend(),
        [
            ("custom", "not-a-dict"),
            ("custom", {"event": "content", "content": "Hi "}),
            *[("custom", update) for update in CUSTOM_TOOL_UPDATES],
            ("updates", {"call_model": "not-a-dict"}),
            ("updates", {"call_model": {"status": "tool_calls", "content": ""}}),
            ("updates", {"call_tools": {"iteration": 1, "tool_results": []}}),
            (
                "updates",
                {
                    "call_model": {
                        "status": "final",
                        "content": "Hi there",
                        "streamed": True,
                        "usage": {"total_tokens": 9},
                    }
                },
            ),
        ],
    )
    assert _dump(events) == [
        ("content", "Hi ", {}),
        *TOOL_EVENTS,
        ("status", "Calling tools…", {}),
        ("metrics", {"total_tokens": 9}, {}),
        ("done", {}, {"status": "success", "error": None}),
    ]


def test_graph_stream_emits_unstreamed_final_content_once() -> None:
    events = _run_graph(
        _backend(),
        [("updates", {"call_model": {"status": "final", "content": "Answer"}})],
    )
    assert _dump(events) == [
        ("content", "Answer", {}),
        ("metrics", {}, {}),
        ("done", {}, {"status": "success", "error": None}),
    ]


def test_graph_stream_falls_back_to_merged_content() -> None:
    events = _run_graph(
        _backend(),
        [
            ("updates", {"call_model": {"status": "final", "content": "Late", "streamed": True}}),
            ("updates", {"finish": {"error": "max_iterations_reached"}}),
        ],
    )
    assert _dump(events) == [
        ("metrics", {}, {}),
        ("content", "Late", {}),
        ("done", {}, {"status": "partial", "error": "max_iterations_reached"}),
    ]


def test_graph_stream_without_content() -> None:
    events = _run_graph(_backend(), [("updates", {"call_model": {"status": "final"}})])
    assert _dump(events) == [
        ("metrics", {}, {}),
        ("done", {}, {"status": "success", "error": None}),
    ]


def _durable(
    backend: GraphAssistantBackend,
    updates: list[Any],
    response: AgentResponse,
) -> Callable[..., Any]:
    async def run_tool_graph(context: ChatContext, on_event: Any = None) -> AgentResponse:
        assert context.metadata["streaming"] is True
        for update in updates:
            on_event(update)
            await asyncio.sleep(0)
        return response

    return run_tool_graph


def test_checkpointed_stream_forwards_events_without_duplicate_content() -> None:
    backend = _backend()
    response = AgentResponse(
        content="Hi",
        status=ResponseStatus.SUCCESS,
        usage=UsageMetrics(total_tokens=4),
        metadata={"interrupted": True},
    )
    updates = [{"event": "content", "content": "Hi"}, *CUSTOM_TOOL_UPDATES]
    with patch.object(backend, "_run_tool_graph", _durable(backend, updates, response)):
        events = asyncio.run(_collect(backend, _context(checkpoint_directory="/x", turn_id="t")))
    dumped = _dump(events)
    assert dumped[: len(TOOL_EVENTS) + 1] == [("content", "Hi", {}), *TOOL_EVENTS]
    metrics = dumped[len(TOOL_EVENTS) + 1]
    assert metrics[0] == "metrics"
    assert metrics[1] == UsageMetrics(total_tokens=4).model_dump()
    assert dumped[len(TOOL_EVENTS) + 2 :] == [
        ("done", {}, {"status": "success", "error": None, "interrupted": True})
    ]


def test_checkpointed_stream_emits_final_content_when_not_streamed() -> None:
    backend = _backend()
    response = AgentResponse(content="Done", status=ResponseStatus.ERROR, error="x")
    with patch.object(backend, "_run_tool_graph", _durable(backend, [], response)):
        events = asyncio.run(_collect(backend, _context(checkpoint_directory="/x", turn_id="t")))
    assert [e.type.value for e in events] == ["metrics", "content", "done"]
    assert events[1].data == "Done"
    assert events[2].metadata == {"status": "error", "error": "x", "interrupted": False}


def test_checkpointed_stream_without_content() -> None:
    backend = _backend()
    response = AgentResponse(content="", status=ResponseStatus.SUCCESS)
    with patch.object(backend, "_run_tool_graph", _durable(backend, [], response)):
        events = asyncio.run(_collect(backend, _context(checkpoint_directory="/x", turn_id="t")))
    assert [e.type.value for e in events] == ["metrics", "done"]


def test_closing_checkpointed_stream_cancels_the_turn() -> None:
    backend = _backend()
    cancelled = asyncio.Event()

    async def run_tool_graph(context: ChatContext, on_event: Any = None) -> AgentResponse:
        on_event({"event": "tool_start", "tool": "slow"})
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cancelled.set()
            raise
        raise AssertionError("unreachable")

    async def consume_first() -> StreamEvent:
        stream = backend.stream(_context(checkpoint_directory="/x", turn_id="t"))
        first = await anext(stream)
        assert isinstance(stream, AsyncGenerator)
        await stream.aclose()
        return first

    with patch.object(backend, "_run_tool_graph", run_tool_graph):
        first = asyncio.run(consume_first())
    assert first.type.value == "tool_start"
    assert cancelled.is_set()


@pytest.mark.parametrize("user_input", ["   ", "x" * 5001])
def test_invalid_input_ends_with_error(user_input: str) -> None:
    events = asyncio.run(_collect(_backend(), _context(user_input)))
    assert len(events) == 1
    assert events[0].type.value == "done"
    assert events[0].metadata["status"] == "error"
