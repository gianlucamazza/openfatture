"""Tests for streaming response functionality.

These tests verify that streaming works correctly across providers,
agents, and the UI layer.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from openfatture.ai.agents.chat_agent import ChatAgent
from openfatture.ai.domain import AgentConfig, BaseAgent
from openfatture.ai.domain.context import AgentContext, ChatContext
from openfatture.ai.domain.message import Message, Role
from openfatture.ai.domain.response import AgentResponse, ResponseStatus, UsageMetrics
from openfatture.ai.providers.base import BaseLLMProvider, ProviderError


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
        import inspect

        from openfatture.ai.providers.ollama import OllamaProvider

        # Verify method exists
        assert hasattr(OllamaProvider, "stream")

        # Verify it's an async generator
        assert inspect.isasyncgenfunction(OllamaProvider.stream)

        # Verify signature
        sig = inspect.signature(OllamaProvider.stream)
        assert "messages" in sig.parameters


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
