"""Multi-node LangGraph tool loop (helper, not product path)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openfatture.ai.domain.response import AgentResponse, ResponseStatus, ToolCall, UsageMetrics
from openfatture.ai.tools.models import ToolResult


def _provider_response(
    *,
    content: str = "",
    tool_calls: list[ToolCall] | None = None,
    tokens: int = 3,
) -> AgentResponse:
    return AgentResponse(
        content=content,
        status=ResponseStatus.SUCCESS,
        tool_calls=tool_calls or [],
        usage=UsageMetrics(total_tokens=tokens, estimated_cost_usd=0.0),
    )


@pytest.mark.asyncio
async def test_tool_loop_runs_tools_then_final_answer() -> None:
    """call_model → call_tools → call_model(final) with one tool invocation."""
    provider = MagicMock()
    provider.provider_name = "openai"
    provider.supports_tools = True
    provider.generate = AsyncMock(
        side_effect=[
            _provider_response(
                content="",
                tool_calls=[
                    ToolCall(id="tc1", name="search_invoices", arguments={"limit": 5}),
                ],
            ),
            _provider_response(content="Found 2 invoices", tokens=5),
        ]
    )

    registry = MagicMock()
    registry.get_openai_functions.return_value = [
        {"type": "function", "function": {"name": "search_invoices", "parameters": {}}}
    ]
    registry.execute_tool = AsyncMock(
        return_value=ToolResult(
            success=True,
            data={"count": 2},
            error=None,
            tool_name="search_invoices",
        )
    )

    with patch("openfatture.platform.extras.require_extra"):
        from openfatture.ai.runtime.graph import build_tool_loop_graph

        graph = build_tool_loop_graph(
            provider=provider,
            tool_registry=registry,
            max_iterations=5,
        )

    result: dict[str, Any] = await graph.ainvoke(
        {
            "user_input": "list invoices",
            "system_prompt": "You are helpful.",
            "messages": [],
            "iteration": 0,
            "max_iterations": 5,
            "tool_results": [],
        }
    )

    assert result["status"] == "final"
    assert "Found 2 invoices" in (result.get("content") or "")
    assert result.get("tool_results")
    assert result["tool_results"][0]["tool"] == "search_invoices"
    assert result["tool_results"][0]["success"] is True
    assert provider.generate.await_count == 2
    registry.execute_tool.assert_awaited_once()


@pytest.mark.asyncio
async def test_tool_loop_stops_at_max_iterations() -> None:
    """Safety cap: endless tool_calls cannot spin forever."""
    provider = MagicMock()
    provider.provider_name = "openai"
    provider.supports_tools = True
    # Always request another tool call
    provider.generate = AsyncMock(
        return_value=_provider_response(
            content="",
            tool_calls=[ToolCall(id="tc", name="noop", arguments={})],
        )
    )

    registry = MagicMock()
    registry.get_openai_functions.return_value = []
    registry.execute_tool = AsyncMock(
        return_value=ToolResult(success=True, data="ok", error=None, tool_name="noop")
    )

    with patch("openfatture.platform.extras.require_extra"):
        from openfatture.ai.runtime.graph import build_tool_loop_graph

        graph = build_tool_loop_graph(
            provider=provider,
            tool_registry=registry,
            max_iterations=2,
        )

    result = await graph.ainvoke(
        {
            "user_input": "loop",
            "messages": [],
            "iteration": 0,
            "max_iterations": 2,
            "tool_results": [],
        }
    )

    assert int(result.get("iteration") or 0) >= 2
    assert provider.generate.await_count <= 3
    assert registry.execute_tool.await_count >= 1


@pytest.mark.asyncio
async def test_build_assistant_graph_uses_tool_loop_when_tools_supported() -> None:
    with (
        patch("openfatture.platform.extras.require_extra"),
        patch("openfatture.ai.providers.factory.create_provider") as mock_prov,
        patch("openfatture.ai.agents.chat_agent.ChatAgent") as mock_agent_cls,
    ):
        provider = MagicMock(provider_name="openai", model="gpt", supports_tools=True)
        mock_prov.return_value = provider
        agent = MagicMock()
        agent.tool_registry = MagicMock()
        agent.tool_registry.get_openai_functions.return_value = []
        mock_agent_cls.return_value = agent

        from openfatture.ai.runtime import create_assistant_runtime
        from openfatture.ai.runtime.graph import build_assistant_graph

        runtime = create_assistant_runtime()
        graph = build_assistant_graph(runtime)
        assert graph is not None
        assert hasattr(graph, "ainvoke")
