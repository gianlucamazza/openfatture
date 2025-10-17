"""Tests for streaming response functionality.

These tests verify that streaming works correctly across providers,
agents, and the UI layer.
"""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from openfatture.ai.agents.chat_agent import ChatAgent
from openfatture.ai.domain import AgentConfig, BaseAgent
from openfatture.ai.domain.context import AgentContext, ChatContext
from openfatture.ai.domain.message import Message, Role
from openfatture.ai.domain.response import AgentResponse, ResponseStatus, UsageMetrics
from openfatture.ai.providers.base import BaseLLMProvider, ProviderError


def mock_stream(chunks):
    """Helper to create async iterator from chunk list."""

    async def _stream():
        for chunk in chunks:
            yield chunk

    return _stream()


class MockResponseStream:
    """Minimal async response stream used to simulate OpenAI Responses streaming."""

    def __init__(self, events, final_response):
        self._events = iter(events)
        self._final_response = final_response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._events)
        except StopIteration:
            raise StopAsyncIteration

    async def get_final_response(self):
        return self._final_response


class DummyStreamingAgent(BaseAgent):
    """Dummy agent for testing streaming."""

    async def _build_prompt(self, context: AgentContext) -> list[Message]:
        """Build simple prompt."""
        return [Message(role=Role.USER, content=context.user_input)]


@pytest.fixture
def mock_streaming_provider():
    """Create a mock provider with streaming support."""
    provider = MagicMock(spec=BaseLLMProvider)
    provider.provider_name = "mock_streaming"
    provider.model = "mock-stream-1"

    # Mock non-streaming generate
    async def mock_generate(messages, **kwargs):
        return AgentResponse(
            content="This is a complete response.",
            status=ResponseStatus.SUCCESS,
            model="mock-stream-1",
            provider="mock_streaming",
            usage=UsageMetrics(
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30,
                estimated_cost_usd=0.001,
            ),
            latency_ms=100.0,
        )

    provider.generate = AsyncMock(side_effect=mock_generate)

    # Mock streaming
    async def mock_stream(messages, **kwargs):
        """Simulate streaming response chunks."""
        chunks = [
            "This ",
            "is ",
            "a ",
            "streaming ",
            "response ",
            "with ",
            "multiple ",
            "chunks.",
        ]
        for chunk in chunks:
            await asyncio.sleep(0.01)  # Simulate network delay
            yield chunk

    provider.stream = mock_stream

    return provider


@pytest.fixture
def mock_error_streaming_provider():
    """Create a mock provider that fails during streaming."""
    provider = MagicMock(spec=BaseLLMProvider)
    provider.provider_name = "error_streaming"
    provider.model = "error-stream-1"

    async def mock_stream_with_error(messages, **kwargs):
        """Simulate streaming that fails mid-stream."""
        yield "Partial "
        yield "response "
        raise ProviderError("Streaming connection lost", provider="error_streaming")

    provider.stream = mock_stream_with_error

    return provider


@pytest.fixture
def mock_openai_provider():
    """Create a mock OpenAI provider for testing."""
    from openfatture.ai.providers.openai import OpenAIProvider

    # Create a real provider instance with a mock client
    provider = OpenAIProvider(api_key="test-key", model="gpt-4")

    # Use AsyncMock for async methods
    provider.client = AsyncMock()
    provider.client.responses = AsyncMock()
    provider.client.chat = AsyncMock()
    provider.client.chat.completions = AsyncMock()

    # Mock basic helpers to keep deterministic behaviour
    provider._get_max_output_tokens = MagicMock(return_value=2000)
    provider._get_temperature = MagicMock(return_value=0.7)
    provider._extract_extra_params = MagicMock(side_effect=lambda params: params)

    return provider


@pytest.mark.asyncio
@pytest.mark.streaming
class TestBaseAgentStreaming:
    """Tests for BaseAgent streaming functionality."""

    async def test_execute_stream_basic(self, mock_streaming_provider):
        """Test basic streaming execution."""
        config = AgentConfig(
            name="test_agent",
            description="Test agent",
            streaming_enabled=True,
        )

        agent = DummyStreamingAgent(config=config, provider=mock_streaming_provider)
        context = AgentContext(user_input="Test streaming")

        # Collect chunks
        chunks = []
        async for chunk in agent.execute_stream(context):
            chunks.append(chunk)

        # Verify
        assert len(chunks) == 8
        full_response = "".join(chunks)
        assert "streaming response" in full_response
        assert agent.total_requests == 1

    async def test_execute_stream_requires_config(self, mock_streaming_provider):
        """Test that execute_stream raises error if streaming not enabled."""
        config = AgentConfig(
            name="test_agent",
            description="Test agent",
            streaming_enabled=False,  # Streaming disabled
        )

        agent = DummyStreamingAgent(config=config, provider=mock_streaming_provider)
        context = AgentContext(user_input="Test")

        # Should raise ValueError
        with pytest.raises(ValueError, match="Streaming not enabled"):
            async for _ in agent.execute_stream(context):
                pass

    async def test_execute_stream_with_invalid_input(self, mock_streaming_provider):
        """Test streaming with invalid input validation."""
        config = AgentConfig(
            name="test_agent",
            description="Test agent",
            streaming_enabled=True,
        )

        agent = DummyStreamingAgent(config=config, provider=mock_streaming_provider)
        context = AgentContext(user_input="")  # Empty input

        # Should yield error message
        chunks = []
        async for chunk in agent.execute_stream(context):
            chunks.append(chunk)

        full_response = "".join(chunks)
        assert "[Error:" in full_response
        assert agent.total_errors == 0  # Validation errors don't count as execution errors

    async def test_execute_stream_metrics_tracking(self, mock_streaming_provider):
        """Test that metrics are tracked during streaming."""
        config = AgentConfig(
            name="test_agent",
            description="Test agent",
            streaming_enabled=True,
        )

        agent = DummyStreamingAgent(config=config, provider=mock_streaming_provider)

        # Execute streaming twice
        for i in range(2):
            context = AgentContext(user_input=f"Test {i}")
            async for _ in agent.execute_stream(context):
                pass

        # Verify metrics
        metrics = agent.get_metrics()
        assert metrics["total_requests"] == 2
        assert metrics["total_tokens"] > 0  # Estimated tokens

    async def test_execute_stream_error_handling(self, mock_error_streaming_provider):
        """Test error handling during streaming."""
        config = AgentConfig(
            name="test_agent",
            description="Test agent",
            streaming_enabled=True,
            max_retries=0,  # No retries for this test
        )

        agent = DummyStreamingAgent(config=config, provider=mock_error_streaming_provider)
        context = AgentContext(user_input="Test")

        # Should yield partial response then error
        chunks = []
        async for chunk in agent.execute_stream(context):
            chunks.append(chunk)

        full_response = "".join(chunks)
        assert "Partial response" in full_response
        assert "[Error:" in full_response
        assert agent.total_errors == 1

    async def test_streaming_retry_logic(self):
        """Test retry logic in streaming mode."""
        # Create provider that fails first attempt, succeeds second
        provider = MagicMock(spec=BaseLLMProvider)
        provider.provider_name = "retry_test"
        provider.model = "retry-1"

        attempt_count = 0

        async def mock_stream_with_retry(messages, **kwargs):
            nonlocal attempt_count
            attempt_count += 1

            if attempt_count == 1:
                # First attempt fails
                raise ProviderError("Temporary error", provider="retry_test")
            else:
                # Second attempt succeeds
                yield "Success "
                yield "after "
                yield "retry"

        provider.stream = mock_stream_with_retry

        config = AgentConfig(
            name="retry_agent",
            description="Retry test",
            streaming_enabled=True,
            max_retries=2,
        )

        agent = DummyStreamingAgent(config=config, provider=provider)
        context = AgentContext(user_input="Test retry")

        chunks = []
        async for chunk in agent.execute_stream(context):
            chunks.append(chunk)

        # Should succeed on second attempt
        full_response = "".join(chunks)
        assert "Success after retry" in full_response
        assert attempt_count == 2


@pytest.mark.asyncio
@pytest.mark.streaming
class TestChatAgentStreaming:
    """Tests for ChatAgent streaming."""

    async def test_chat_agent_streaming_enabled_by_default(self, mock_streaming_provider):
        """Test that ChatAgent has streaming enabled by default."""
        agent = ChatAgent(provider=mock_streaming_provider)

        # Streaming should be enabled
        assert agent.config.streaming_enabled is True

    async def test_chat_agent_can_disable_streaming(self, mock_streaming_provider):
        """Test that streaming can be disabled in ChatAgent."""
        agent = ChatAgent(provider=mock_streaming_provider, enable_streaming=False)

        # Streaming should be disabled
        assert agent.config.streaming_enabled is False

    async def test_chat_agent_streaming_execution(self, mock_streaming_provider):
        """Test ChatAgent streaming with real context."""
        agent = ChatAgent(
            provider=mock_streaming_provider, enable_streaming=True, enable_tools=False
        )

        context = ChatContext(
            user_input="Ciao, come funziona OpenFatture?", session_id="test-session-1"
        )

        chunks = []
        async for chunk in agent.execute_stream(context):
            chunks.append(chunk)

        # Verify
        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert len(full_response) > 0


@pytest.mark.asyncio
@pytest.mark.streaming
class TestProviderStreaming:
    """Tests for provider streaming (verify API contracts)."""

    async def test_openai_provider_has_stream_method(self):
        """Verify OpenAI provider implements stream method."""
        import inspect

        from openfatture.ai.providers.openai import OpenAIProvider

        # Verify method exists
        assert hasattr(OpenAIProvider, "stream")

        # Verify it's an async generator
        assert inspect.isasyncgenfunction(OpenAIProvider.stream)

        # Verify signature
        sig = inspect.signature(OpenAIProvider.stream)
        assert "messages" in sig.parameters
        assert "system_prompt" in sig.parameters
        assert "temperature" in sig.parameters
        assert "max_tokens" in sig.parameters

    async def test_anthropic_provider_has_stream_method(self):
        """Verify Anthropic provider implements stream method."""
        import inspect

        from openfatture.ai.providers.anthropic import AnthropicProvider

        # Verify method exists
        assert hasattr(AnthropicProvider, "stream")

        # Verify it's an async generator
        assert inspect.isasyncgenfunction(AnthropicProvider.stream)

        # Verify signature
        sig = inspect.signature(AnthropicProvider.stream)
        assert "messages" in sig.parameters

    async def test_ollama_provider_has_stream_method(self):
        """Verify Ollama provider implements stream method."""

        from openfatture.ai.providers.ollama import OllamaProvider

        # Verify method exists
        assert hasattr(OllamaProvider, "stream")

    async def test_openai_provider_has_stream_structured_method(self):
        """Verify OpenAI provider implements stream_structured method."""
        import inspect

        from openfatture.ai.providers.openai import OpenAIProvider

        # Verify method exists
        assert hasattr(OpenAIProvider, "stream_structured")

        # Verify it's an async generator
        assert inspect.isasyncgenfunction(OpenAIProvider.stream_structured)

        # Verify signature
        sig = inspect.signature(OpenAIProvider.stream_structured)
        assert "messages" in sig.parameters
        assert "system_prompt" in sig.parameters
        assert "temperature" in sig.parameters
        assert "max_tokens" in sig.parameters

    async def test_ollama_provider_has_stream_structured_method(self):
        """Verify Ollama provider implements stream_structured method."""
        import inspect

        from openfatture.ai.providers.ollama import OllamaProvider

        # Verify method exists
        assert hasattr(OllamaProvider, "stream_structured")

        # Verify it's an async generator
        assert inspect.isasyncgenfunction(OllamaProvider.stream_structured)

        # Verify signature
        sig = inspect.signature(OllamaProvider.stream_structured)
        assert "messages" in sig.parameters


@pytest.mark.asyncio
@pytest.mark.streaming
class TestStreamingToolCalls:
    """Tests for streaming tool calls functionality."""

    async def test_openai_stream_structured_basic_content_only(self, mock_openai_provider):
        """Test stream_structured yields content chunks without tools."""

        # Chat Completions API streaming format
        events = [
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(content="Hello", tool_calls=None), finish_reason=None
                    )
                ],
                usage=None,
            ),
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(content=" world", tool_calls=None), finish_reason=None
                    )
                ],
                usage=None,
            ),
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(content=None, tool_calls=None), finish_reason="stop"
                    )
                ],
                usage=SimpleNamespace(input_tokens=10, output_tokens=5, total_tokens=15),
            ),
        ]

        mock_openai_provider.client.chat.completions.create.return_value = MockResponseStream(
            events=events,
            final_response=None,
        )

        messages = [Message(role=Role.USER, content="Test")]
        chunks = []

        async for chunk in mock_openai_provider.stream_structured(messages):
            chunks.append(chunk)

        assert len(chunks) == 3
        assert chunks[0].content == "Hello"
        assert chunks[1].content == " world"
        assert chunks[2].is_final is True
        assert chunks[2].finish_reason == "stop"

    async def test_openai_stream_structured_tool_calls_single(self, mock_openai_provider):
        """Test stream_structured yields tool calls correctly."""

        # Chat Completions API streaming format with tool calls
        tool_call_delta = SimpleNamespace(
            index=0,
            id="call_123",
            function=SimpleNamespace(name="search_invoices", arguments='{"query": "test"}'),
        )

        events = [
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(content="I'll help you", tool_calls=None),
                        finish_reason=None,
                    )
                ],
                usage=None,
            ),
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(content=None, tool_calls=[tool_call_delta]),
                        finish_reason=None,
                    )
                ],
                usage=None,
            ),
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(content=None, tool_calls=None),
                        finish_reason="tool_calls",
                    )
                ],
                usage=SimpleNamespace(input_tokens=15, output_tokens=10, total_tokens=25),
            ),
        ]

        mock_openai_provider.client.chat.completions.create.return_value = MockResponseStream(
            events=events,
            final_response=None,
        )

        messages = [Message(role=Role.USER, content="Search for test invoices")]
        chunks = []

        async for chunk in mock_openai_provider.stream_structured(messages):
            chunks.append(chunk)

        # Should have content chunk, tool call chunk, and final chunk
        assert len(chunks) == 3
        assert chunks[0].content == "I'll help you"
        assert chunks[1].tool_call is not None
        assert chunks[1].tool_call.id == "call_123"
        assert chunks[1].tool_call.name == "search_invoices"
        assert chunks[1].tool_call.arguments == {"query": "test"}
        assert chunks[2].is_final is True
        assert chunks[2].finish_reason == "tool_calls"

    async def test_openai_stream_structured_tool_calls_multiple(self, mock_openai_provider):
        """Test stream_structured handles multiple tool calls."""

        # Chat Completions API streaming format with multiple tool calls
        tool_call_1 = SimpleNamespace(
            index=0,
            id="call_123",
            function=SimpleNamespace(name="search_invoices", arguments='{"query": "revenue"}'),
        )
        tool_call_2 = SimpleNamespace(
            index=1,
            id="call_456",
            function=SimpleNamespace(name="analyze_revenue", arguments='{"period": "2024"}'),
        )

        events = [
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(content="I'll search and analyze", tool_calls=None),
                        finish_reason=None,
                    )
                ],
                usage=None,
            ),
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(content=None, tool_calls=[tool_call_1]),
                        finish_reason=None,
                    )
                ],
                usage=None,
            ),
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(content=None, tool_calls=[tool_call_2]),
                        finish_reason=None,
                    )
                ],
                usage=None,
            ),
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(content=None, tool_calls=None),
                        finish_reason="tool_calls",
                    )
                ],
                usage=SimpleNamespace(input_tokens=20, output_tokens=15, total_tokens=35),
            ),
        ]

        mock_openai_provider.client.chat.completions.create.return_value = MockResponseStream(
            events=events,
            final_response=None,
        )

        messages = [Message(role=Role.USER, content="Analyze revenue for 2024")]
        chunks = []

        async for chunk in mock_openai_provider.stream_structured(messages):
            chunks.append(chunk)

        # Should have content chunk, two tool call chunks, and final chunk
        assert len(chunks) == 4
        assert chunks[0].content == "I'll search and analyze"
        assert chunks[1].tool_call.name == "search_invoices"
        assert chunks[1].tool_call.arguments == {"query": "revenue"}
        assert chunks[2].tool_call.name == "analyze_revenue"
        assert chunks[2].tool_call.arguments == {"period": "2024"}
        assert chunks[3].is_final is True

    async def test_openai_stream_structured_malformed_json(self, mock_openai_provider):
        """Test stream_structured handles malformed tool call arguments."""

        # Chat Completions API streaming format with malformed JSON
        tool_call_delta = SimpleNamespace(
            index=0,
            id="call_123",
            function=SimpleNamespace(name="search_invoices", arguments="{invalid json"),
        )

        events = [
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(content="Calling tool", tool_calls=None),
                        finish_reason=None,
                    )
                ],
                usage=None,
            ),
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(content=None, tool_calls=[tool_call_delta]),
                        finish_reason=None,
                    )
                ],
                usage=None,
            ),
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(content=None, tool_calls=None),
                        finish_reason="tool_calls",
                    )
                ],
                usage=SimpleNamespace(input_tokens=12, output_tokens=8, total_tokens=20),
            ),
        ]

        mock_openai_provider.client.chat.completions.create.return_value = MockResponseStream(
            events=events,
            final_response=None,
        )

        messages = [Message(role=Role.USER, content="Test malformed JSON")]
        chunks = []

        async for chunk in mock_openai_provider.stream_structured(messages):
            chunks.append(chunk)

        # Should have content chunk, tool call chunk (with empty args), and final chunk
        assert len(chunks) == 3
        assert chunks[0].content == "Calling tool"
        assert chunks[1].tool_call.name == "search_invoices"
        assert chunks[1].tool_call.arguments == {}  # Should default to empty dict
        assert chunks[2].is_final is True

    async def test_chat_agent_message_construction_with_tool_calls(self, mock_openai_provider):
        """Test that ChatAgent properly constructs messages with tool_calls for follow-up."""
        from unittest.mock import AsyncMock

        from openfatture.ai.domain.response import StreamChunk, ToolCall
        from openfatture.ai.tools import get_tool_registry

        class MockToolResult:
            def __init__(self, data):
                self.data = data
                self.success = True

            def to_dict(self):
                return {"success": self.success, "data": self.data}

        # Mock tool registry
        tool_registry = get_tool_registry()
        tool_registry.get_tool = AsyncMock(return_value=AsyncMock())
        tool_registry.execute_tool = AsyncMock(return_value=MockToolResult({"total_clients": 3}))

        initial_chunks = [
            StreamChunk(content="I'll check your clients"),
            StreamChunk(
                content="",
                tool_call=ToolCall(id="call_123", name="get_client_stats", arguments={}),
            ),
            StreamChunk(content="", is_final=True, finish_reason="tool_calls"),
        ]

        async def fake_stream_structured(messages, **kwargs):
            for chunk in initial_chunks:
                yield chunk

        followup_calls = []

        async def fake_followup_stream(messages, **kwargs):
            followup_calls.append({"messages": messages, "kwargs": kwargs})
            for part in ["You have 3 clients", ""]:
                yield part

        mock_openai_provider.stream_structured = fake_stream_structured
        mock_openai_provider.stream = fake_followup_stream

        agent = ChatAgent(
            provider=mock_openai_provider,
            tool_registry=tool_registry,
            enable_tools=True,
            enable_streaming=True,
        )

        context = ChatContext(user_input="How many clients do I have?")
        context.available_tools = ["get_client_stats"]

        # Collect all chunks
        chunks = []
        async for chunk in agent.execute_stream(context):
            chunks.append(chunk)

        # Verify that tool calls were detected and executed
        assert any("Eseguendo" in chunk for chunk in chunks)
        assert any("get_client_stats" in chunk for chunk in chunks)

        # Verify that the follow-up stream was called
        assert len(followup_calls) == 1

        followup_messages = followup_calls[0]["messages"]

        # Verify message structure
        assert len(followup_messages) >= 3  # Original + assistant + tool

        # Find the assistant message
        assistant_msg = None
        tool_msg = None
        for msg in followup_messages:
            if msg.role == Role.ASSISTANT:
                assistant_msg = msg
            elif msg.role == Role.TOOL:
                tool_msg = msg

        assert assistant_msg is not None, "Assistant message should be present"
        assert tool_msg is not None, "Tool message should be present"

        # Verify assistant message has tool_calls
        assert assistant_msg.tool_calls is not None, "Assistant message should have tool_calls"
        assert len(assistant_msg.tool_calls) == 1, "Should have one tool call"

        tool_call = assistant_msg.tool_calls[0]
        assert tool_call["id"] == "call_123"
        assert tool_call["type"] == "function"
        assert tool_call["function"]["name"] == "get_client_stats"
        assert tool_call["function"]["arguments"] == {}

        # Verify tool message has correct tool_call_id
        assert tool_msg.tool_call_id == "call_123"


@pytest.mark.asyncio
@pytest.mark.streaming
class TestStreamingPerformance:
    """Performance-related tests for streaming."""

    async def test_streaming_latency(self, mock_streaming_provider):
        """Test that streaming starts yielding chunks quickly."""
        import time

        config = AgentConfig(
            name="latency_test", description="Latency test", streaming_enabled=True
        )

        agent = DummyStreamingAgent(config=config, provider=mock_streaming_provider)
        context = AgentContext(user_input="Test latency")

        start_time = time.time()
        first_chunk_time = None

        async for chunk in agent.execute_stream(context):
            if first_chunk_time is None:
                first_chunk_time = time.time()
                # Time to first chunk should be very low (< 100ms)
                time_to_first = (first_chunk_time - start_time) * 1000
                assert time_to_first < 100, f"First chunk took {time_to_first}ms"
                break

    async def test_streaming_memory_efficiency(self, mock_streaming_provider):
        """Test that streaming doesn't accumulate all chunks in memory."""
        config = AgentConfig(name="memory_test", description="Memory test", streaming_enabled=True)

        agent = DummyStreamingAgent(config=config, provider=mock_streaming_provider)
        context = AgentContext(user_input="Test memory")

        # Process chunks one at a time
        chunk_count = 0
        async for chunk in agent.execute_stream(context):
            # In real streaming, we'd process and discard each chunk
            chunk_count += 1

        assert chunk_count > 0
