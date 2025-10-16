"""Integration tests for formatters with AI commands."""

import json

import pytest

from openfatture.ai.agents.chat_agent import ChatAgent
from openfatture.ai.domain.context import ChatContext
from openfatture.ai.domain.response import AgentResponse, ResponseStatus, UsageMetrics
from openfatture.ai.providers.base import BaseLLMProvider
from openfatture.cli.formatters.factory import get_formatter


class IntegrationMockProvider(BaseLLMProvider):
    """Mock provider for integration testing."""

    def __init__(self):
        super().__init__()
        self._provider_name = "integration-mock"
        self.model = "integration-model"
        self._supports_streaming = True
        self._supports_tools = False

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def supports_streaming(self) -> bool:
        return self._supports_streaming

    @property
    def supports_tools(self) -> bool:
        return self._supports_tools

    async def generate(self, messages, **kwargs):
        """Generate realistic responses."""
        content = "This is a detailed AI-generated response for your query."
        return AgentResponse(
            content=content,
            status=ResponseStatus.SUCCESS,
            provider=self.provider_name,
            model=self.model,
            usage=UsageMetrics(
                prompt_tokens=150,
                completion_tokens=300,
                total_tokens=450,
                estimated_cost_usd=0.0045,
            ),
            latency_ms=750,
        )

    async def stream(self, messages, **kwargs):
        response = await self.generate(messages, **kwargs)
        words = response.content.split()
        for word in words:
            yield word + " "

    def count_tokens(self, text: str) -> int:
        return len(text.split())

    def estimate_cost(self, usage: UsageMetrics) -> float:
        return usage.total_tokens * 0.00001

    async def health_check(self) -> bool:
        return True


@pytest.fixture
def integration_provider():
    """Create integration mock provider."""
    return IntegrationMockProvider()


@pytest.fixture
def sample_agent_response():
    """Create sample AgentResponse for testing."""
    return AgentResponse(
        content="Integration test response content from AI agent.",
        status=ResponseStatus.SUCCESS,
        provider="test-provider",
        model="test-model",
        usage=UsageMetrics(
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300,
            estimated_cost_usd=0.003,
        ),
        latency_ms=500,
    )


@pytest.mark.integration
@pytest.mark.asyncio
class TestFormatterIntegrationWithChatAgent:
    """Integration tests with ChatAgent."""

    async def test_json_formatter_with_chat_agent(self, integration_provider):
        """Test JSON formatter with real ChatAgent execution."""
        agent = ChatAgent(provider=integration_provider, enable_tools=False)
        context = ChatContext(user_input="Test query for AI")

        # Execute agent
        response = await agent.execute(context)

        # Format with JSON formatter
        formatter = get_formatter("json")
        output = formatter.format_response(response)

        # Verify valid JSON
        data = json.loads(output)
        assert data["content"] == response.content
        assert data["status"] == "success"
        assert data["provider"] == "integration-mock"
        assert data["tokens_used"] == 450

    async def test_markdown_formatter_with_chat_agent(self, integration_provider):
        """Test Markdown formatter with real ChatAgent execution."""
        agent = ChatAgent(provider=integration_provider, enable_tools=False)
        context = ChatContext(user_input="Test query")

        response = await agent.execute(context)

        formatter = get_formatter("markdown")
        output = formatter.format_response(response)

        assert "# AI Response" in output
        assert response.content in output
        assert "integration-mock" in output
        assert "450" in output  # tokens

    async def test_html_formatter_with_chat_agent(self, integration_provider):
        """Test HTML formatter with real ChatAgent execution."""
        agent = ChatAgent(provider=integration_provider, enable_tools=False)
        context = ChatContext(user_input="Test query")

        response = await agent.execute(context)

        formatter = get_formatter("html")
        output = formatter.format_response(response)

        assert "<!DOCTYPE html>" in output
        assert response.content in output
        assert "integration-mock" in output

    async def test_stream_json_formatter_with_streaming(self, integration_provider):
        """Test StreamJSON formatter with streaming agent."""
        agent = ChatAgent(provider=integration_provider, enable_streaming=True)
        context = ChatContext(user_input="Stream test")

        formatter = get_formatter("stream-json")

        # Collect streamed chunks
        chunks = []
        async for chunk in agent.execute_stream(context):
            formatted_chunk = formatter.format_stream_chunk(chunk)
            chunks.append(formatted_chunk)

        # Verify chunks are valid JSON Lines
        assert len(chunks) > 0
        for chunk in chunks:
            data = json.loads(chunk.strip())
            assert data["type"] == "chunk"
            assert "content" in data
            assert "index" in data


@pytest.mark.integration
class TestFormatterBackwardCompatibility:
    """Test backward compatibility with existing --json flag."""

    def test_json_output_maintains_structure(self, sample_agent_response):
        """Test that JSON output structure is maintained."""
        formatter = get_formatter("json")
        output = formatter.format_response(sample_agent_response)

        data = json.loads(output)

        # Verify all expected keys are present
        assert "content" in data
        assert "status" in data
        assert "provider" in data
        assert "model" in data
        assert "tokens_used" in data
        assert "cost_usd" in data

    def test_json_formatter_matches_to_dict(self, sample_agent_response):
        """Test that JSON formatter output matches AgentResponse.to_dict()."""
        formatter = get_formatter("json")
        json_output = json.loads(formatter.format_response(sample_agent_response))

        to_dict_output = sample_agent_response.to_dict()

        # Core fields should match
        assert json_output["content"] == to_dict_output["content"]
        assert json_output["status"] == to_dict_output["status"]
        assert json_output["provider"] == to_dict_output["provider"]
        assert json_output["tokens_used"] == to_dict_output["tokens_used"]


@pytest.mark.integration
class TestFormatterErrorHandling:
    """Test error handling across all formatters."""

    def test_json_formatter_handles_error_response(self):
        """Test JSON formatter with error response."""
        error_response = AgentResponse(
            content="",
            status=ResponseStatus.ERROR,
            error="Test error message",
            provider="test",
            model="test",
        )

        formatter = get_formatter("json")
        output = formatter.format_response(error_response)

        data = json.loads(output)
        assert data["status"] == "error"
        assert data["error"] == "Test error message"

    def test_markdown_formatter_handles_error_response(self):
        """Test Markdown formatter with error response."""
        error_response = AgentResponse(
            content="",
            status=ResponseStatus.ERROR,
            error="Test error",
            provider="test",
            model="test",
        )

        formatter = get_formatter("markdown")
        output = formatter.format_response(error_response)

        assert "## Error" in output
        assert "❌" in output
        assert "Test error" in output

    def test_html_formatter_handles_error_response(self):
        """Test HTML formatter with error response."""
        error_response = AgentResponse(
            content="",
            status=ResponseStatus.ERROR,
            error="Test error",
            provider="test",
            model="test",
        )

        formatter = get_formatter("html")
        output = formatter.format_response(error_response)

        assert "<!DOCTYPE html>" in output
        assert "Error" in output
        assert "Test error" in output


@pytest.mark.integration
class TestFormatterWithDifferentContentTypes:
    """Test formatters with various content types."""

    def test_formatters_handle_multiline_content(self):
        """Test all formatters handle multiline content correctly."""
        multiline_content = """Line 1
Line 2
Line 3"""
        response = AgentResponse(
            content=multiline_content,
            status=ResponseStatus.SUCCESS,
            provider="test",
            model="test",
        )

        for format_type in ["json", "markdown", "html", "stream-json", "rich"]:
            formatter = get_formatter(format_type)
            output = formatter.format_response(response)
            assert len(output) > 0  # Should not crash

    def test_formatters_handle_special_characters(self):
        """Test formatters handle special characters."""
        special_content = 'Content with "quotes" and <tags> and €symbols€'
        response = AgentResponse(
            content=special_content,
            status=ResponseStatus.SUCCESS,
            provider="test",
            model="test",
        )

        # JSON should escape properly
        json_formatter = get_formatter("json")
        json_output = json_formatter.format_response(response)
        json.loads(json_output)  # Should not raise

        # HTML should escape properly
        html_formatter = get_formatter("html")
        html_output = html_formatter.format_response(response)
        assert "&lt;" not in special_content  # But HTML should escape
        assert "<!DOCTYPE html>" in html_output
