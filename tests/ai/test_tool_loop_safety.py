from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from openfatture.ai.domain.context import ChatContext
from openfatture.ai.domain.response import AgentResponse, StreamChunk, ToolCall, UsageMetrics
from openfatture.ai.runtime.graph import build_tool_loop_graph
from openfatture.ai.runtime.graph_backend import GraphAssistantBackend


@pytest.mark.asyncio
@pytest.mark.parametrize("arguments", ["{invalid", "[]", "null", "", [], None])
async def test_invalid_arguments_never_execute(arguments) -> None:
    call = ToolCall.model_construct(id="bad", name="mutate", arguments=arguments)
    provider = MagicMock(provider_name="openai", supports_tools=True)
    provider.generate = AsyncMock(
        side_effect=[
            AgentResponse(tool_calls=[call], content=""),
            AgentResponse(content="corrected"),
        ]
    )
    registry = MagicMock()
    graph = build_tool_loop_graph(provider=provider, tool_registry=registry)
    result = await graph.ainvoke({"user_input": "go"})
    registry.execute_tool.assert_not_called()
    assert result["tool_results"][0]["success"] is False
    assert result["content"] == "corrected"


@pytest.mark.asyncio
async def test_model_parameters_and_budget() -> None:
    provider = MagicMock(provider_name="openai", supports_tools=True)
    provider.generate = AsyncMock(
        return_value=AgentResponse(
            content="",
            tool_calls=[ToolCall(id="c", name="mutate", arguments={})],
        )
    )
    registry = MagicMock()
    graph = build_tool_loop_graph(
        provider=provider, tool_registry=registry, temperature=0.2, max_tokens=90, max_iterations=1
    )
    result = await graph.ainvoke({"user_input": "go"})
    assert result["error"] == "max_iterations_reached"
    registry.execute_tool.assert_not_called()
    assert provider.generate.await_args.kwargs["temperature"] == 0.2
    assert provider.generate.await_args.kwargs["max_tokens"] == 90


@pytest.mark.asyncio
@pytest.mark.parametrize("persistent", [False, True])
async def test_streamed_content_not_duplicated_and_done_is_last(
    tmp_path: Path, persistent: bool
) -> None:
    from openfatture.ai.providers.openai import OpenAIProvider

    provider = object.__new__(OpenAIProvider)
    provider.model = "test"

    async def chunks(**kwargs):
        yield StreamChunk(content="one ")
        yield StreamChunk(content="two")
        yield StreamChunk(content="", is_final=True, usage=UsageMetrics(total_tokens=2))

    provider.stream_structured = chunks
    registry = MagicMock()
    registry.get_openai_functions.return_value = []
    backend = GraphAssistantBackend(provider=provider, tool_registry=registry)
    context = ChatContext(user_input="hello", available_tools=["read"], session_id="s")
    if persistent:
        context.metadata.update(checkpoint_directory=str(tmp_path), turn_id="t")
    events = [e async for e in backend.stream(context)]
    assert "".join(e.get_text() for e in events if e.is_content()) == "one two"
    assert [e.type.value for e in events].count("done") == 1
    assert events[-1].type.value == "done"
