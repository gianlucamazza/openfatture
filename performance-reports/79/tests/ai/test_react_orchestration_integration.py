"""Integration tests for ReAct orchestration.

Tests the full ReAct loop (execute and stream methods) with real and mocked components.
Focuses on:
- Tool calling iterations
- Error handling
- Max iterations
- Streaming behavior
- Integration with ToolRegistry

Run with: pytest tests/ai/test_react_orchestration_integration.py -v
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from openfatture.ai.domain.context import ChatContext
from openfatture.ai.domain.response import AgentResponse, ResponseStatus, UsageMetrics
from openfatture.ai.orchestration.react import ReActOrchestrator
from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType, ToolResult
from openfatture.ai.tools.registry import ToolRegistry


@pytest.fixture
def mock_provider_for_react():
    """Create mock provider that simulates ReAct-style responses."""
    provider = MagicMock()
    provider.provider_name = "mock_react"
    provider.model = "mock-model"
    provider.supports_tools = False  # Simulate Ollama-style provider

    # Queue of responses to return
    provider._response_queue = []

    async def mock_generate(messages, **kwargs):
        """Pop next response from queue."""
        if not provider._response_queue:
            # Default final answer
            content = "<final_answer>Default response</final_answer>"
        else:
            content = provider._response_queue.pop(0)

        return AgentResponse(
            content=content,
            status=ResponseStatus.SUCCESS,
            model="mock-model",
            provider="mock_react",
            usage=UsageMetrics(
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30,
                estimated_cost_usd=0.001,
            ),
            latency_ms=50.0,
        )

    async def mock_stream(messages, **kwargs):
        """Stream response word by word."""
        if not provider._response_queue:
            content = "<final_answer>Default response</final_answer>"
        else:
            content = provider._response_queue.pop(0)

        # Split into words and yield
        for word in content.split():
            await asyncio.sleep(0.001)
            yield word + " "

    provider.generate = AsyncMock(side_effect=mock_generate)
    provider.stream = mock_stream

    return provider


@pytest.fixture
def mock_tool_registry():
    """Create mock tool registry with sample tools."""
    registry = MagicMock(spec=ToolRegistry)

    # Define dummy functions for tools
    def dummy_get_invoice_count():
        return {"count": 42}

    def dummy_search_invoices(limit=10):
        return [
            {"numero": "001/2025", "cliente": "Acme Corp", "totale": 1200.0},
            {"numero": "002/2025", "cliente": "Beta Ltd", "totale": 850.0},
        ]

    # Define sample tools
    sample_tools = [
        Tool(
            name="get_invoice_count",
            description="Get total invoice count",
            func=dummy_get_invoice_count,
            parameters=[],
            category="invoice",
            enabled=True,
        ),
        Tool(
            name="search_invoices",
            description="Search invoices by criteria",
            func=dummy_search_invoices,
            parameters=[
                ToolParameter(
                    name="limit",
                    type=ToolParameterType.INTEGER,
                    description="Maximum results",
                    required=False,
                ),
            ],
            category="invoice",
            enabled=True,
        ),
    ]

    registry.list_tools = MagicMock(return_value=sample_tools)

    # Mock tool execution
    async def mock_execute_tool(tool_name, parameters, confirm=False):
        """Mock tool execution with predefined results."""
        if tool_name == "get_invoice_count":
            return ToolResult(
                success=True,
                data={"count": 42},
                tool_name=tool_name,
            )
        elif tool_name == "search_invoices":
            return ToolResult(
                success=True,
                data=[
                    {"numero": "001/2025", "cliente": "Acme Corp", "totale": 1200.0},
                    {"numero": "002/2025", "cliente": "Beta Ltd", "totale": 850.0},
                ],
                tool_name=tool_name,
            )
        else:
            return ToolResult(
                success=False,
                error=f"Unknown tool: {tool_name}",
                tool_name=tool_name,
            )

    registry.execute_tool = AsyncMock(side_effect=mock_execute_tool)

    return registry


@pytest.fixture
def sample_chat_context():
    """Create sample ChatContext for testing."""
    context = ChatContext(
        user_input="Quante fatture ho emesso quest'anno?",
        session_id="test-session-react",
        enable_tools=True,
    )
    # Add available tools
    context.available_tools = ["get_invoice_count", "search_invoices"]
    return context


@pytest.mark.asyncio
class TestReActExecute:
    """Test ReActOrchestrator.execute() method."""

    async def test_execute_single_tool_call_then_final_answer(
        self, mock_provider_for_react, mock_tool_registry, sample_chat_context
    ):
        """Test execute with one tool call followed by final answer."""
        # Setup provider responses
        mock_provider_for_react._response_queue = [
            # First iteration: tool call
            "<thought>I need to get the invoice count</thought>\n<action>get_invoice_count</action>\n<action_input>{}</action_input>",
            # Second iteration: final answer after seeing observation
            "<final_answer>Hai emesso 42 fatture quest'anno.</final_answer>",
        ]

        orchestrator = ReActOrchestrator(
            provider=mock_provider_for_react,
            tool_registry=mock_tool_registry,
            max_iterations=5,
        )

        result = await orchestrator.execute(sample_chat_context)

        # Verify
        assert "42 fatture" in result
        assert mock_tool_registry.execute_tool.call_count == 1
        mock_tool_registry.execute_tool.assert_called_with(
            tool_name="get_invoice_count",
            parameters={},
            confirm=False,
        )

    async def test_execute_multiple_tool_calls(
        self, mock_provider_for_react, mock_tool_registry, sample_chat_context
    ):
        """Test execute with multiple tool calls in sequence."""
        mock_provider_for_react._response_queue = [
            # First tool call
            "<thought>Get count</thought>\n<action>get_invoice_count</action>\n<action_input>{}</action_input>",
            # Second tool call
            '<thought>Search details</thought>\n<action>search_invoices</action>\n<action_input>{"limit": 2}</action_input>',
            # Final answer
            "<final_answer>Hai 42 fatture, ultime 2: 001/2025 e 002/2025</final_answer>",
        ]

        orchestrator = ReActOrchestrator(
            provider=mock_provider_for_react,
            tool_registry=mock_tool_registry,
            max_iterations=5,
        )

        result = await orchestrator.execute(sample_chat_context)

        # Verify multiple tools executed
        assert mock_tool_registry.execute_tool.call_count == 2
        assert "42 fatture" in result
        assert "001/2025" in result or "002/2025" in result

    async def test_execute_max_iterations_reached(
        self, mock_provider_for_react, mock_tool_registry, sample_chat_context
    ):
        """Test execute when max iterations is reached without final answer."""
        # Provider keeps making tool calls without final answer
        mock_provider_for_react._response_queue = [
            "<thought>Call 1</thought>\n<action>get_invoice_count</action>\n<action_input>{}</action_input>",
            "<thought>Call 2</thought>\n<action>get_invoice_count</action>\n<action_input>{}</action_input>",
            "<thought>Call 3</thought>\n<action>get_invoice_count</action>\n<action_input>{}</action_input>",
        ]

        orchestrator = ReActOrchestrator(
            provider=mock_provider_for_react,
            tool_registry=mock_tool_registry,
            max_iterations=3,  # Low limit
        )

        result = await orchestrator.execute(sample_chat_context)

        # Should return max iterations message
        assert "limite di iterazioni" in result.lower()
        assert "3" in result  # Max iterations number
        assert mock_tool_registry.execute_tool.call_count == 3

    async def test_execute_tool_execution_failure(
        self, mock_provider_for_react, mock_tool_registry, sample_chat_context
    ):
        """Test execute when tool execution fails."""
        mock_provider_for_react._response_queue = [
            # Call unknown tool
            "<thought>Try unknown</thought>\n<action>unknown_tool</action>\n<action_input>{}</action_input>",
            # LLM should handle error and provide final answer
            "<final_answer>Mi dispiace, non posso recuperare quel dato.</final_answer>",
        ]

        orchestrator = ReActOrchestrator(
            provider=mock_provider_for_react,
            tool_registry=mock_tool_registry,
            max_iterations=5,
        )

        result = await orchestrator.execute(sample_chat_context)

        # Should complete with error handling
        assert result is not None
        assert len(result) > 0
        # Tool was called but failed
        assert mock_tool_registry.execute_tool.call_count == 1

    async def test_execute_immediate_final_answer(
        self, mock_provider_for_react, mock_tool_registry, sample_chat_context
    ):
        """Test execute when LLM gives immediate final answer (no tools needed)."""
        mock_provider_for_react._response_queue = [
            "<final_answer>OpenFatture è un sistema di fatturazione elettronica.</final_answer>",
        ]

        orchestrator = ReActOrchestrator(
            provider=mock_provider_for_react,
            tool_registry=mock_tool_registry,
            max_iterations=5,
        )

        result = await orchestrator.execute(sample_chat_context)

        # Should return answer without calling tools
        assert "OpenFatture" in result
        assert mock_tool_registry.execute_tool.call_count == 0

    async def test_execute_no_tool_or_final_treats_as_final(
        self, mock_provider_for_react, mock_tool_registry, sample_chat_context
    ):
        """Test execute when response has neither tool call nor final answer."""
        mock_provider_for_react._response_queue = [
            "This is just a response without tool call or final answer markers.",
        ]

        orchestrator = ReActOrchestrator(
            provider=mock_provider_for_react,
            tool_registry=mock_tool_registry,
            max_iterations=5,
        )

        result = await orchestrator.execute(sample_chat_context)

        # Should treat as final answer
        assert result is not None
        assert "response without tool call" in result
        assert mock_tool_registry.execute_tool.call_count == 0


@pytest.mark.asyncio
class TestReActStream:
    """Test ReActOrchestrator.stream() method."""

    async def test_stream_basic_flow(
        self, mock_provider_for_react, mock_tool_registry, sample_chat_context
    ):
        """Test basic streaming with tool call and final answer."""
        mock_provider_for_react._response_queue = [
            "<thought>Check count</thought>\n<action>get_invoice_count</action>\n<action_input>{}</action_input>",
            "<final_answer>Hai emesso 42 fatture</final_answer>",
        ]

        orchestrator = ReActOrchestrator(
            provider=mock_provider_for_react,
            tool_registry=mock_tool_registry,
            max_iterations=5,
        )

        # Collect chunks
        chunks = []
        async for chunk in orchestrator.stream(sample_chat_context):
            chunks.append(chunk)

        full_response = "".join(chunks)

        # Verify final answer was streamed
        assert "42 fatture" in full_response
        assert len(chunks) > 1  # Multiple chunks
        assert mock_tool_registry.execute_tool.call_count == 1

    async def test_stream_immediate_final_answer(
        self, mock_provider_for_react, mock_tool_registry, sample_chat_context
    ):
        """Test streaming with immediate final answer (no tools)."""
        mock_provider_for_react._response_queue = [
            "<final_answer>La risposta è semplice e diretta</final_answer>",
        ]

        orchestrator = ReActOrchestrator(
            provider=mock_provider_for_react,
            tool_registry=mock_tool_registry,
            max_iterations=5,
        )

        chunks = []
        async for chunk in orchestrator.stream(sample_chat_context):
            chunks.append(chunk)

        full_response = "".join(chunks)

        assert "risposta" in full_response
        assert mock_tool_registry.execute_tool.call_count == 0

    async def test_stream_max_iterations(
        self, mock_provider_for_react, mock_tool_registry, sample_chat_context
    ):
        """Test streaming when max iterations is reached."""
        mock_provider_for_react._response_queue = [
            "<thought>Try 1</thought>\n<action>get_invoice_count</action>\n<action_input>{}</action_input>",
            "<thought>Try 2</thought>\n<action>get_invoice_count</action>\n<action_input>{}</action_input>",
        ]

        orchestrator = ReActOrchestrator(
            provider=mock_provider_for_react,
            tool_registry=mock_tool_registry,
            max_iterations=2,
        )

        chunks = []
        async for chunk in orchestrator.stream(sample_chat_context):
            chunks.append(chunk)

        full_response = "".join(chunks)

        # Should yield error message
        assert "limite di iterazioni" in full_response.lower()


@pytest.mark.asyncio
class TestReActIntegration:
    """Integration tests with real components."""

    async def test_react_with_real_tool_registry(
        self, mock_provider_for_react, sample_chat_context
    ):
        """Test ReAct with real ToolRegistry (no tools registered)."""
        # Use real registry but empty
        real_registry = ToolRegistry()

        mock_provider_for_react._response_queue = [
            "<final_answer>No tools available, answering directly</final_answer>",
        ]

        orchestrator = ReActOrchestrator(
            provider=mock_provider_for_react,
            tool_registry=real_registry,
            max_iterations=5,
        )

        result = await orchestrator.execute(sample_chat_context)

        assert result is not None
        assert len(result) > 0

    async def test_react_system_prompt_includes_tools(
        self, mock_provider_for_react, mock_tool_registry
    ):
        """Test that system prompt includes tool descriptions."""
        orchestrator = ReActOrchestrator(
            provider=mock_provider_for_react,
            tool_registry=mock_tool_registry,
            max_iterations=5,
        )

        context = ChatContext(
            user_input="Test query",
            enable_tools=True,
        )

        # Build messages
        messages = orchestrator._build_react_messages(context)

        # First message should be system prompt
        assert len(messages) > 0
        system_prompt = messages[0].content

        # Verify XML ReAct format (2025)
        assert "<thought>" in system_prompt
        assert "<action>" in system_prompt
        assert "<action_input>" in system_prompt
        assert "<final_answer>" in system_prompt

        # Verify tools are listed
        assert "get_invoice_count" in system_prompt
        assert "search_invoices" in system_prompt

    async def test_react_format_observation_dict(self, mock_provider_for_react, mock_tool_registry):
        """Test observation formatting for dict data."""
        orchestrator = ReActOrchestrator(
            provider=mock_provider_for_react,
            tool_registry=mock_tool_registry,
        )

        result = orchestrator._format_observation({"count": 42, "status": "ok"})

        assert "count: 42" in result
        assert "status: ok" in result

    async def test_react_format_observation_list(self, mock_provider_for_react, mock_tool_registry):
        """Test observation formatting for list data."""
        orchestrator = ReActOrchestrator(
            provider=mock_provider_for_react,
            tool_registry=mock_tool_registry,
        )

        data = [
            {"numero": "001", "totale": 1200},
            {"numero": "002", "totale": 850},
        ]

        result = orchestrator._format_observation(data)

        assert "numero=001" in result
        assert "totale=1200" in result
        assert "numero=002" in result

    async def test_react_format_observation_empty(
        self, mock_provider_for_react, mock_tool_registry
    ):
        """Test observation formatting for None/empty data."""
        orchestrator = ReActOrchestrator(
            provider=mock_provider_for_react,
            tool_registry=mock_tool_registry,
        )

        assert orchestrator._format_observation(None) == "Nessun risultato"
        assert orchestrator._format_observation([]) == "Lista vuota"
        assert orchestrator._format_observation("") == ""

    async def test_react_get_stats(self, mock_provider_for_react, mock_tool_registry):
        """Test orchestrator statistics."""
        orchestrator = ReActOrchestrator(
            provider=mock_provider_for_react,
            tool_registry=mock_tool_registry,
            max_iterations=7,
        )

        stats = orchestrator.get_stats()

        assert stats["provider"] == "mock_react"
        assert stats["model"] == "mock-model"
        assert stats["max_iterations"] == 7
        assert "parser_stats" in stats

    async def test_react_metrics_tracking(
        self, mock_provider_for_react, mock_tool_registry, sample_chat_context
    ):
        """Test that metrics are tracked correctly during execution."""
        mock_provider_for_react._response_queue = [
            # First: tool call (success)
            "<thought>Get count</thought>\n<action>get_invoice_count</action>\n<action_input>{}</action_input>",
            # Second: another tool call (success)
            '<thought>Search</thought>\n<action>search_invoices</action>\n<action_input>{"limit": 2}</action_input>',
            # Third: final answer
            "<final_answer>Found results</final_answer>",
        ]

        orchestrator = ReActOrchestrator(
            provider=mock_provider_for_react,
            tool_registry=mock_tool_registry,
            max_iterations=5,
        )

        # Execute
        result = await orchestrator.execute(sample_chat_context)

        # Check metrics
        metrics = orchestrator.get_metrics()

        assert metrics["total_executions"] == 1
        assert metrics["tool_calls_attempted"] == 2
        assert metrics["tool_calls_succeeded"] == 2
        assert metrics["tool_calls_failed"] == 0
        assert metrics["tool_call_success_rate"] == 1.0
        assert metrics["max_iterations_reached"] == 0
        assert metrics["avg_iterations"] == 3.0  # 3 iterations total
        assert "parser_stats" in metrics

    async def test_react_metrics_with_failures(
        self, mock_provider_for_react, mock_tool_registry, sample_chat_context
    ):
        """Test metrics tracking when tool calls fail."""

        # Setup tool to fail
        async def mock_execute_fail(tool_name, parameters, confirm=False):
            return ToolResult(
                success=False,
                error="Tool execution failed",
                tool_name=tool_name,
            )

        mock_tool_registry.execute_tool = AsyncMock(side_effect=mock_execute_fail)

        mock_provider_for_react._response_queue = [
            # Tool call (will fail)
            "<thought>Try</thought>\n<action>get_invoice_count</action>\n<action_input>{}</action_input>",
            # Final answer after failure
            "<final_answer>Could not complete</final_answer>",
        ]

        orchestrator = ReActOrchestrator(
            provider=mock_provider_for_react,
            tool_registry=mock_tool_registry,
            max_iterations=5,
        )

        result = await orchestrator.execute(sample_chat_context)

        metrics = orchestrator.get_metrics()

        assert metrics["tool_calls_attempted"] == 1
        assert metrics["tool_calls_succeeded"] == 0
        assert metrics["tool_calls_failed"] == 1
        assert metrics["tool_call_success_rate"] == 0.0

    async def test_react_metrics_max_iterations(
        self, mock_provider_for_react, mock_tool_registry, sample_chat_context
    ):
        """Test metrics when max iterations is reached."""
        # Setup infinite loop (no final answer)
        mock_provider_for_react._response_queue = [
            "<thought>1</thought>\n<action>get_invoice_count</action>\n<action_input>{}</action_input>",
            "<thought>2</thought>\n<action>get_invoice_count</action>\n<action_input>{}</action_input>",
        ]

        orchestrator = ReActOrchestrator(
            provider=mock_provider_for_react,
            tool_registry=mock_tool_registry,
            max_iterations=2,
        )

        result = await orchestrator.execute(sample_chat_context)

        metrics = orchestrator.get_metrics()

        assert metrics["max_iterations_reached"] == 1
        assert metrics["total_iterations"] == 2
        assert metrics["avg_iterations"] == 2.0


@pytest.mark.asyncio
class TestReActErrorHandling:
    """Test error handling in ReAct orchestration."""

    async def test_react_handles_tool_exception(
        self, mock_provider_for_react, mock_tool_registry, sample_chat_context
    ):
        """Test that ReAct handles tool execution exceptions gracefully."""

        # Make tool raise exception
        async def mock_execute_with_error(tool_name, parameters, confirm=False):
            raise RuntimeError("Tool execution failed!")

        mock_tool_registry.execute_tool = AsyncMock(side_effect=mock_execute_with_error)

        mock_provider_for_react._response_queue = [
            "<thought>Try tool</thought>\n<action>get_invoice_count</action>\n<action_input>{}</action_input>",
            "<final_answer>Error occurred, cannot complete</final_answer>",
        ]

        orchestrator = ReActOrchestrator(
            provider=mock_provider_for_react,
            tool_registry=mock_tool_registry,
            max_iterations=5,
        )

        result = await orchestrator.execute(sample_chat_context)

        # Should complete with error handling
        assert result is not None
        # Tool was attempted
        assert mock_tool_registry.execute_tool.call_count == 1

    async def test_react_handles_invalid_json_parameters(
        self, mock_provider_for_react, mock_tool_registry, sample_chat_context
    ):
        """Test parsing of invalid JSON in Action Input."""
        mock_provider_for_react._response_queue = [
            # Invalid JSON (will be handled by parser)
            "<thought>Try</thought>\n<action>search_invoices</action>\n<action_input>{invalid json}</action_input>",
            "<final_answer>Completed</final_answer>",
        ]

        orchestrator = ReActOrchestrator(
            provider=mock_provider_for_react,
            tool_registry=mock_tool_registry,
            max_iterations=5,
        )

        result = await orchestrator.execute(sample_chat_context)

        # Should either parse or skip the tool call
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
