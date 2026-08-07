"""Parity contracts: LangGraph tool-loop helper vs ChatAgent product path.

These tests document that the graph helper can complete the same tool
round-trip shape as the product ChatAgent path, without flipping the CLI
default backend.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openfatture.ai.domain.response import AgentResponse, ResponseStatus, ToolCall, UsageMetrics
from openfatture.ai.tools.models import ToolResult


def _final(content: str = "done") -> AgentResponse:
    return AgentResponse(
        content=content,
        status=ResponseStatus.SUCCESS,
        usage=UsageMetrics(total_tokens=2, estimated_cost_usd=0.0),
    )


def _with_tool() -> AgentResponse:
    return AgentResponse(
        content="",
        status=ResponseStatus.SUCCESS,
        tool_calls=[ToolCall(id="1", name="search_invoices", arguments={"limit": 5})],
        usage=UsageMetrics(total_tokens=3, estimated_cost_usd=0.0),
    )


@pytest.mark.asyncio
async def test_graph_tool_round_trip_matches_shape() -> None:
    """Graph: model → tool → final content (same semantic shape as product loop)."""
    provider = MagicMock()
    provider.provider_name = "openai"
    provider.supports_tools = True
    provider.generate = AsyncMock(side_effect=[_with_tool(), _final("Found invoices")])

    registry = MagicMock()
    registry.get_openai_functions.return_value = []
    registry.execute_tool = AsyncMock(
        return_value=ToolResult(
            success=True, data={"count": 1}, error=None, tool_name="search_invoices"
        )
    )

    with patch("openfatture.platform.extras.require_extra"):
        from openfatture.ai.runtime.graph import build_tool_loop_graph

        graph = build_tool_loop_graph(provider=provider, tool_registry=registry, max_iterations=5)

    result: dict[str, Any] = await graph.ainvoke(
        {
            "user_input": "list invoices",
            "messages": [],
            "iteration": 0,
            "max_iterations": 5,
            "tool_results": [],
        }
    )

    assert result["status"] == "final"
    assert result["content"] == "Found invoices"
    assert result["tool_results"][0]["tool"] == "search_invoices"
    assert result["tool_results"][0]["success"] is True
    assert provider.generate.await_count == 2
    registry.execute_tool.assert_awaited_once()


@pytest.mark.asyncio
async def test_product_runtime_backend_is_chat_agent() -> None:
    """Product path still reports chat_agent_tool_loop (B1-β)."""
    with (
        patch("openfatture.platform.extras.require_extra"),
        patch("openfatture.ai.providers.factory.create_provider") as mock_prov,
        patch("openfatture.ai.agents.chat_agent.ChatAgent") as mock_agent_cls,
    ):
        mock_prov.return_value = MagicMock(provider_name="openai", model="gpt")
        agent = MagicMock()
        agent.execute = AsyncMock(return_value=_final("ok"))
        mock_agent_cls.return_value = agent

        from openfatture.ai.runtime import create_assistant_runtime

        runtime = create_assistant_runtime()
        assert runtime.backend == "chat_agent_tool_loop"
        response = await runtime.run("hello")
        assert response.content == "ok"


@pytest.mark.asyncio
async def test_graph_zero_tools_final_answer() -> None:
    """No tool_calls → final in one model step (parity with simple chat)."""
    provider = MagicMock()
    provider.provider_name = "openai"
    provider.supports_tools = True
    provider.generate = AsyncMock(return_value=_final("hello"))

    registry = MagicMock()
    registry.get_openai_functions.return_value = []

    with patch("openfatture.platform.extras.require_extra"):
        from openfatture.ai.runtime.graph import build_tool_loop_graph

        graph = build_tool_loop_graph(provider=provider, tool_registry=registry, max_iterations=3)

    result = await graph.ainvoke(
        {"user_input": "hi", "messages": [], "iteration": 0, "tool_results": []}
    )
    assert result["status"] == "final"
    assert result["content"] == "hello"
    registry.execute_tool.assert_not_called()
