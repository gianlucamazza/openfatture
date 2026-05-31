"""Tests for native tool calling and structured output.

Covers:
(a) Anthropic provider extracts ``tool_use`` blocks into ``tool_calls``.
(b) OpenAI provider extracts ``message.tool_calls`` into ``tool_calls``.
(c) Native dispatch loop (provider.supports_tools=True) executes mock tools
    and returns the final tool-call-free response.
(d) Dispatch falls back to ReAct when supports_tools=False.
(e) Structured output enforced: validated payload in metadata['structured'].

All tests use mock providers / mock clients. No network access.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openfatture.ai.agents.chat_agent import ChatAgent
from openfatture.ai.domain.context import ChatContext
from openfatture.ai.domain.response import AgentResponse, ResponseStatus, ToolCall, UsageMetrics
from openfatture.ai.orchestration.native_tools import NativeToolOrchestrator
from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType, ToolResult
from openfatture.ai.tools.registry import ToolRegistry

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_tool_registry():
    """Registry with a single mock ``get_invoice_count`` tool."""
    registry = MagicMock(spec=ToolRegistry)

    sample_tools = [
        Tool(
            name="get_invoice_count",
            description="Get total invoice count",
            func=lambda: {"count": 42},
            parameters=[
                ToolParameter(
                    name="year",
                    type=ToolParameterType.INTEGER,
                    description="Year filter",
                    required=False,
                ),
            ],
            category="invoice",
            enabled=True,
        ),
    ]

    registry.list_tools = MagicMock(return_value=sample_tools)
    registry.get_openai_functions = MagicMock(
        return_value=[{"type": "function", "function": sample_tools[0].to_openai_function()}]
    )
    registry.get_anthropic_tools = MagicMock(return_value=[sample_tools[0].to_anthropic_tool()])

    async def mock_execute_tool(tool_name, parameters, confirm=False):
        if tool_name == "get_invoice_count":
            return ToolResult(success=True, data={"count": 42}, tool_name=tool_name)
        return ToolResult(success=False, error="unknown", tool_name=tool_name)

    registry.execute_tool = AsyncMock(side_effect=mock_execute_tool)
    return registry


def _make_response(content="", tool_calls=None):
    return AgentResponse(
        content=content,
        status=ResponseStatus.SUCCESS,
        model="mock-model",
        provider="mock",
        usage=UsageMetrics(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        tool_calls=tool_calls or [],
    )


# ---------------------------------------------------------------------------
# (a) Anthropic provider: tool_use extraction
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_anthropic_extracts_tool_use_block():
    """Anthropic generate() populates tool_calls from a tool_use block."""
    from openfatture.ai.providers.anthropic import AnthropicProvider

    provider = AnthropicProvider(api_key="test-key", model="claude-4.5-sonnet")

    tool_use_block = SimpleNamespace(
        type="tool_use",
        id="toolu_123",
        name="get_invoice_count",
        input={"year": 2025},
    )
    text_block = SimpleNamespace(type="text", text="Let me check that.")

    fake_message = SimpleNamespace(
        content=[text_block, tool_use_block],
        usage=SimpleNamespace(input_tokens=10, output_tokens=8),
        stop_reason="tool_use",
    )

    provider.client.messages.create = AsyncMock(return_value=fake_message)

    response = await provider.generate(messages=[], system_prompt="sys")

    assert response.has_tool_calls
    assert len(response.tool_calls) == 1
    tc = response.tool_calls[0]
    assert tc.id == "toolu_123"
    assert tc.name == "get_invoice_count"
    assert tc.arguments == {"year": 2025}
    assert response.content == "Let me check that."
    assert response.metadata["stop_reason"] == "tool_use"


@pytest.mark.asyncio
async def test_anthropic_text_only_has_no_tool_calls():
    """Text-only Anthropic responses keep tool_calls empty."""
    from openfatture.ai.providers.anthropic import AnthropicProvider

    provider = AnthropicProvider(api_key="test-key", model="claude-4.5-sonnet")

    text_block = SimpleNamespace(type="text", text="Plain answer.")
    fake_message = SimpleNamespace(
        content=[text_block],
        usage=SimpleNamespace(input_tokens=5, output_tokens=3),
        stop_reason="end_turn",
    )
    provider.client.messages.create = AsyncMock(return_value=fake_message)

    response = await provider.generate(messages=[])

    assert response.tool_calls == []
    assert response.has_tool_calls is False
    assert response.content == "Plain answer."


# ---------------------------------------------------------------------------
# (b) OpenAI provider: tool_calls extraction
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_openai_extracts_tool_calls():
    """OpenAI generate() populates tool_calls from message.tool_calls."""
    from openfatture.ai.providers.openai import OpenAIProvider

    provider = OpenAIProvider(api_key="test-key", model="gpt-4o")

    tool_call = SimpleNamespace(
        id="call_abc",
        function=SimpleNamespace(name="get_invoice_count", arguments='{"year": 2025}'),
    )
    message = SimpleNamespace(content=None, tool_calls=[tool_call])
    choice = SimpleNamespace(message=message, finish_reason="tool_calls")
    fake_response = SimpleNamespace(
        choices=[choice],
        usage=SimpleNamespace(prompt_tokens=12, completion_tokens=6, total_tokens=18),
    )

    provider.client.chat.completions.create = AsyncMock(return_value=fake_response)

    response = await provider.generate(messages=[])

    assert response.has_tool_calls
    tc = response.tool_calls[0]
    assert tc.id == "call_abc"
    assert tc.name == "get_invoice_count"
    assert tc.arguments == {"year": 2025}
    assert response.metadata["finish_reason"] == "tool_calls"


@pytest.mark.asyncio
async def test_openai_text_only_has_no_tool_calls():
    """Text-only OpenAI responses keep tool_calls empty."""
    from openfatture.ai.providers.openai import OpenAIProvider

    provider = OpenAIProvider(api_key="test-key", model="gpt-4o")

    message = SimpleNamespace(content="Plain answer.", tool_calls=None)
    choice = SimpleNamespace(message=message, finish_reason="stop")
    fake_response = SimpleNamespace(
        choices=[choice],
        usage=SimpleNamespace(prompt_tokens=4, completion_tokens=2, total_tokens=6),
    )
    provider.client.chat.completions.create = AsyncMock(return_value=fake_response)

    response = await provider.generate(messages=[])

    assert response.tool_calls == []
    assert response.content == "Plain answer."


# ---------------------------------------------------------------------------
# (c) Native orchestrator loop executes tools then returns final answer
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_native_orchestrator_executes_tools(mock_tool_registry):
    """Native loop: tool_use response -> tool exec -> final answer."""
    provider = MagicMock()
    provider.provider_name = "openai"
    provider.model = "gpt-4o"
    provider.supports_tools = True

    responses = [
        _make_response(
            content="",
            tool_calls=[ToolCall(id="call_1", name="get_invoice_count", arguments={"year": 2025})],
        ),
        _make_response(content="Hai emesso 42 fatture nel 2025."),
    ]

    async def fake_generate(*args, **kwargs):
        return responses.pop(0)

    provider.generate = AsyncMock(side_effect=fake_generate)

    orchestrator = NativeToolOrchestrator(
        provider=provider,
        tool_registry=mock_tool_registry,
        max_iterations=5,
    )

    context = ChatContext(user_input="Quante fatture?", enable_tools=True)
    response = await orchestrator.execute(context=context, messages=[])

    assert "42 fatture" in response.content
    assert mock_tool_registry.execute_tool.call_count == 1
    mock_tool_registry.execute_tool.assert_called_with(
        tool_name="get_invoice_count", parameters={"year": 2025}, confirm=False
    )

    metrics = orchestrator.get_metrics()
    assert metrics["tool_calls_attempted"] == 1
    assert metrics["tool_calls_succeeded"] == 1
    assert metrics["tool_call_success_rate"] == 1.0

    # tool_choice must use OpenAI "auto" form for an openai provider
    _, kwargs = provider.generate.call_args_list[0]
    assert kwargs["tool_choice"] == "auto"
    assert kwargs["tools"]


@pytest.mark.asyncio
async def test_native_orchestrator_anthropic_tool_choice(mock_tool_registry):
    """Native loop uses Anthropic tool_choice/schema for anthropic providers."""
    provider = MagicMock()
    provider.provider_name = "anthropic"
    provider.model = "claude-4.5-sonnet"
    provider.supports_tools = True

    provider.generate = AsyncMock(return_value=_make_response(content="done"))

    orchestrator = NativeToolOrchestrator(
        provider=provider,
        tool_registry=mock_tool_registry,
        max_iterations=5,
    )

    context = ChatContext(user_input="hi", enable_tools=True)
    await orchestrator.execute(context=context, messages=[])

    _, kwargs = provider.generate.call_args_list[0]
    assert kwargs["tool_choice"] == {"type": "auto"}
    mock_tool_registry.get_anthropic_tools.assert_called()


# ---------------------------------------------------------------------------
# (c2) ChatAgent dispatch -> native path when supports_tools=True
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chat_agent_dispatches_to_native(mock_tool_registry):
    """ChatAgent.execute routes to native orchestrator when supports_tools=True."""
    provider = MagicMock()
    provider.provider_name = "openai"
    provider.model = "gpt-4o"
    provider.supports_tools = True

    responses = [
        _make_response(
            tool_calls=[ToolCall(id="call_1", name="get_invoice_count", arguments={})],
        ),
        _make_response(content="Risposta finale con 42 fatture."),
    ]
    provider.generate = AsyncMock(side_effect=lambda *a, **k: responses.pop(0))

    agent = ChatAgent(provider=provider, tool_registry=mock_tool_registry, enable_tools=True)

    context = ChatContext(user_input="Quante fatture?", enable_tools=True)
    context.available_tools = ["get_invoice_count"]

    response = await agent.execute(context)

    assert "42 fatture" in response.content
    assert response.metadata["orchestrator"] == "native_tools"
    assert mock_tool_registry.execute_tool.call_count == 1


# ---------------------------------------------------------------------------
# (d) ChatAgent dispatch -> ReAct when supports_tools=False
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chat_agent_dispatches_to_react(mock_tool_registry):
    """ChatAgent.execute falls back to ReAct when supports_tools=False."""
    provider = MagicMock()
    provider.provider_name = "ollama"
    provider.model = "qwen3:8b"
    provider.supports_tools = False

    agent = ChatAgent(provider=provider, tool_registry=mock_tool_registry, enable_tools=True)

    context = ChatContext(user_input="Quante fatture?", enable_tools=True)
    context.available_tools = ["get_invoice_count"]

    with patch("openfatture.ai.agents.chat_agent.ReActOrchestrator") as mock_react_cls:
        instance = mock_react_cls.return_value
        instance.execute = AsyncMock(return_value="Risposta ReAct con 42 fatture.")
        instance.get_metrics = MagicMock(return_value={"total_executions": 1})

        response = await agent.execute(context)

    assert "Risposta ReAct" in response.content
    assert response.metadata["orchestrator"] == "react"
    # Native provider.generate must NOT have been used for tool dispatch
    mock_react_cls.assert_called_once()


# ---------------------------------------------------------------------------
# (e) Structured output enforced
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_structured_output_anthropic_forced_tool(mock_tool_registry):
    """Structured output via forced Anthropic tool populates metadata['structured']."""
    provider = MagicMock()
    provider.provider_name = "anthropic"
    provider.model = "claude-4.5-sonnet"
    provider.supports_tools = True

    structured_payload = {"vat_rate": 22, "natura": None}
    provider.generate = AsyncMock(
        return_value=_make_response(
            tool_calls=[ToolCall(id="call_s", name="vat_result", arguments=structured_payload)],
        )
    )

    agent = ChatAgent(provider=provider, tool_registry=mock_tool_registry, enable_tools=True)
    agent.config.output_schema = {
        "title": "vat_result",
        "type": "object",
        "properties": {"vat_rate": {"type": "integer"}, "natura": {"type": ["string", "null"]}},
        "required": ["vat_rate"],
    }

    context = ChatContext(user_input="Aliquota IVA consulenza?", enable_tools=True)
    context.available_tools = ["get_invoice_count"]

    response = await agent.execute(context)

    assert response.metadata["is_structured"] is True
    assert response.metadata["structured"] == structured_payload

    # Verify the forced tool_choice was passed to the provider
    _, kwargs = provider.generate.call_args
    assert kwargs["tool_choice"] == {"type": "tool", "name": "vat_result"}
    assert kwargs["tools"][0]["input_schema"]["title"] == "vat_result"


@pytest.mark.asyncio
async def test_structured_output_openai_json_schema_and_fallback(mock_tool_registry):
    """OpenAI structured output: json_schema request + post-hoc content parse."""
    provider = MagicMock()
    provider.provider_name = "openai"
    provider.model = "gpt-4o"
    provider.supports_tools = True

    # OpenAI returns the JSON in content (no tool call), exercising the fallback parse.
    provider.generate = AsyncMock(
        return_value=_make_response(content='{"vat_rate": 22, "natura": null}')
    )

    agent = ChatAgent(provider=provider, tool_registry=mock_tool_registry, enable_tools=True)
    agent.config.output_schema = {
        "title": "vat_result",
        "type": "object",
        "properties": {"vat_rate": {"type": "integer"}},
        "required": ["vat_rate"],
    }

    context = ChatContext(user_input="Aliquota IVA?", enable_tools=True)
    context.available_tools = ["get_invoice_count"]

    response = await agent.execute(context)

    assert response.metadata["is_structured"] is True
    assert response.metadata["structured"] == {"vat_rate": 22, "natura": None}

    _, kwargs = provider.generate.call_args
    assert kwargs["response_format"]["type"] == "json_schema"
    assert kwargs["response_format"]["json_schema"]["name"] == "vat_result"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
