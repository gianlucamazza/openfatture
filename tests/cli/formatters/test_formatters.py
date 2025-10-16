"""Unit tests for all output formatters."""

import json

import pytest

from openfatture.ai.domain.response import AgentResponse, ResponseStatus, UsageMetrics
from openfatture.cli.formatters.factory import FormatterFactory, get_formatter
from openfatture.cli.formatters.html import HTMLFormatter
from openfatture.cli.formatters.json import JSONFormatter
from openfatture.cli.formatters.markdown import MarkdownFormatter
from openfatture.cli.formatters.rich_formatter import RichFormatter
from openfatture.cli.formatters.stream_json import StreamJSONFormatter


@pytest.fixture
def sample_response():
    """Create a sample AgentResponse for testing."""
    return AgentResponse(
        content="This is a test response from the AI assistant.",
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


@pytest.fixture
def error_response():
    """Create an error AgentResponse for testing."""
    return AgentResponse(
        content="",
        status=ResponseStatus.ERROR,
        error="Test error message",
        provider="test-provider",
        model="test-model",
    )


class TestJSONFormatter:
    """Tests for JSONFormatter."""

    def test_format_response(self, sample_response):
        """Test formatting a successful response as JSON."""
        formatter = JSONFormatter()
        output = formatter.format_response(sample_response)

        # Parse JSON to verify it's valid
        data = json.loads(output)
        assert data["content"] == "This is a test response from the AI assistant."
        assert data["status"] == "success"
        assert data["provider"] == "test-provider"
        assert data["model"] == "test-model"
        assert data["tokens_used"] == 300
        assert data["cost_usd"] == 0.003

    def test_format_error_response(self, error_response):
        """Test formatting an error response."""
        formatter = JSONFormatter()
        output = formatter.format_response(error_response)

        data = json.loads(output)
        assert data["status"] == "error"
        assert data["error"] == "Test error message"

    def test_streaming_not_supported(self):
        """Test that standard JSON doesn't support streaming."""
        formatter = JSONFormatter()
        assert formatter.supports_streaming() is False

    def test_format_stream_chunk(self):
        """Test chunk formatting (returns as-is for buffering)."""
        formatter = JSONFormatter()
        chunk = "test chunk"
        result = formatter.format_stream_chunk(chunk)
        assert result == chunk

    def test_format_error(self):
        """Test error formatting."""
        formatter = JSONFormatter()
        output = formatter.format_error("Test error")
        data = json.loads(output)
        assert data["error"] == "Test error"
        assert data["status"] == "error"

    def test_format_metadata(self):
        """Test metadata formatting."""
        formatter = JSONFormatter()
        metadata = {"key1": "value1", "key2": 42}
        output = formatter.format_metadata(metadata)
        data = json.loads(output)
        assert data["key1"] == "value1"
        assert data["key2"] == 42


class TestMarkdownFormatter:
    """Tests for MarkdownFormatter."""

    def test_format_response(self, sample_response):
        """Test formatting a successful response as Markdown."""
        formatter = MarkdownFormatter()
        output = formatter.format_response(sample_response)

        assert "# AI Response" in output
        assert "## Response" in output
        assert "This is a test response from the AI assistant." in output
        assert "## Metadata" in output
        assert "**Provider:** test-provider" in output
        assert "**Model:** test-model" in output
        assert "**Tokens Used:** 300" in output
        assert "**Cost:** $0.0030" in output
        assert "**Latency:** 500ms" in output

    def test_format_response_without_metadata(self, sample_response):
        """Test formatting without metadata section."""
        formatter = MarkdownFormatter(include_metadata=False)
        output = formatter.format_response(sample_response)

        assert "# AI Response" in output
        assert "This is a test response from the AI assistant." in output
        assert "## Metadata" not in output

    def test_format_error_response(self, error_response):
        """Test formatting an error response."""
        formatter = MarkdownFormatter()
        output = formatter.format_response(error_response)

        assert "# AI Response" in output
        assert "## Error" in output
        assert "❌ Test error message" in output

    def test_streaming_not_supported(self):
        """Test that Markdown doesn't support true streaming."""
        formatter = MarkdownFormatter()
        assert formatter.supports_streaming() is False

    def test_format_error(self):
        """Test error formatting."""
        formatter = MarkdownFormatter()
        output = formatter.format_error("Test error")
        assert "# Error" in output
        assert "❌ Test error" in output


class TestStreamJSONFormatter:
    """Tests for StreamJSONFormatter."""

    def test_format_response(self, sample_response):
        """Test formatting a complete response as JSON Lines."""
        formatter = StreamJSONFormatter()
        output = formatter.format_response(sample_response)

        lines = output.strip().split("\n")
        assert len(lines) == 3  # content, metadata, complete

        # Parse first line (content)
        content_obj = json.loads(lines[0])
        assert content_obj["type"] == "chunk"
        assert content_obj["content"] == "This is a test response from the AI assistant."
        assert content_obj["index"] == 0

        # Parse second line (metadata)
        metadata_obj = json.loads(lines[1])
        assert metadata_obj["type"] == "metadata"
        assert metadata_obj["provider"] == "test-provider"
        assert metadata_obj["model"] == "test-model"
        assert metadata_obj["tokens"] == 300

        # Parse third line (complete)
        complete_obj = json.loads(lines[2])
        assert complete_obj["type"] == "complete"
        assert complete_obj["status"] == "success"
        assert complete_obj["total_chunks"] == 1

    def test_format_stream_chunk(self):
        """Test streaming chunk formatting."""
        formatter = StreamJSONFormatter()

        chunk1 = formatter.format_stream_chunk("first")
        chunk2 = formatter.format_stream_chunk("second")

        obj1 = json.loads(chunk1.strip())
        obj2 = json.loads(chunk2.strip())

        assert obj1["type"] == "chunk"
        assert obj1["content"] == "first"
        assert obj1["index"] == 0

        assert obj2["type"] == "chunk"
        assert obj2["content"] == "second"
        assert obj2["index"] == 1

    def test_format_stream_complete(self):
        """Test stream completion marker."""
        formatter = StreamJSONFormatter()

        # Simulate streaming
        formatter.format_stream_chunk("chunk1")
        formatter.format_stream_chunk("chunk2")

        complete = formatter.format_stream_complete(status="success", metadata={"provider": "test"})

        obj = json.loads(complete.strip())
        assert obj["type"] == "complete"
        assert obj["status"] == "success"
        assert obj["total_chunks"] == 2
        assert obj["metadata"]["provider"] == "test"

    def test_streaming_supported(self):
        """Test that StreamJSON supports streaming."""
        formatter = StreamJSONFormatter()
        assert formatter.supports_streaming() is True

    def test_error_response(self, error_response):
        """Test formatting error response."""
        formatter = StreamJSONFormatter()
        output = formatter.format_response(error_response)

        data = json.loads(output)
        assert data["type"] == "error"
        assert data["error"] == "Test error message"
        assert data["status"] == "error"


class TestHTMLFormatter:
    """Tests for HTMLFormatter."""

    def test_format_response(self, sample_response):
        """Test formatting a successful response as HTML."""
        formatter = HTMLFormatter()
        output = formatter.format_response(sample_response)

        assert "<!DOCTYPE html>" in output
        assert "<html" in output
        assert "🤖 AI Response" in output
        assert "This is a test response from the AI assistant." in output
        assert "test-provider" in output
        assert "test-model" in output
        assert "300" in output  # tokens
        assert "$0.0030" in output  # cost
        assert "500ms" in output  # latency

    def test_format_response_without_metadata(self, sample_response):
        """Test formatting without metadata section."""
        formatter = HTMLFormatter(include_metadata=False)
        output = formatter.format_response(sample_response)

        assert "<!DOCTYPE html>" in output
        assert "This is a test response from the AI assistant." in output
        assert "Metadata" not in output

    def test_format_response_dark_mode(self, sample_response):
        """Test formatting with dark mode."""
        formatter = HTMLFormatter(dark_mode=True)
        output = formatter.format_response(sample_response)

        assert "<!DOCTYPE html>" in output
        assert "#1e1e1e" in output  # Dark background color
        assert "This is a test response from the AI assistant." in output

    def test_format_error_response(self, error_response):
        """Test formatting an error response."""
        formatter = HTMLFormatter()
        output = formatter.format_response(error_response)

        assert "<!DOCTYPE html>" in output
        assert "Error" in output
        assert "❌" in output
        assert "Test error message" in output

    def test_streaming_not_supported(self):
        """Test that HTML doesn't support true streaming."""
        formatter = HTMLFormatter()
        assert formatter.supports_streaming() is False

    def test_format_error(self):
        """Test error formatting."""
        formatter = HTMLFormatter()
        output = formatter.format_error("Test error")
        assert "<!DOCTYPE html>" in output
        assert "Error" in output
        assert "❌" in output
        assert "Test error" in output


class TestRichFormatter:
    """Tests for RichFormatter."""

    def test_format_response(self, sample_response):
        """Test formatting a successful response."""
        formatter = RichFormatter()
        output = formatter.format_response(sample_response)

        assert "This is a test response from the AI assistant." in output

    def test_format_error_response(self, error_response):
        """Test formatting an error response."""
        formatter = RichFormatter()
        output = formatter.format_response(error_response)

        assert "❌ Error:" in output
        assert "Test error message" in output

    def test_streaming_supported(self):
        """Test that Rich supports streaming."""
        formatter = RichFormatter()
        assert formatter.supports_streaming() is True

    def test_format_stream_chunk(self):
        """Test streaming chunk formatting."""
        formatter = RichFormatter()
        chunk = "test chunk"
        result = formatter.format_stream_chunk(chunk)
        assert result == chunk

    def test_format_error(self):
        """Test error formatting."""
        formatter = RichFormatter()
        output = formatter.format_error("Test error")
        assert "❌ Error:" in output
        assert "Test error" in output


class TestFormatterFactory:
    """Tests for FormatterFactory."""

    def test_get_formatter_json(self):
        """Test getting JSON formatter."""
        formatter = FormatterFactory.get_formatter("json")
        assert isinstance(formatter, JSONFormatter)

    def test_get_formatter_markdown(self):
        """Test getting Markdown formatter."""
        formatter = FormatterFactory.get_formatter("markdown")
        assert isinstance(formatter, MarkdownFormatter)

    def test_get_formatter_stream_json(self):
        """Test getting StreamJSON formatter."""
        formatter = FormatterFactory.get_formatter("stream-json")
        assert isinstance(formatter, StreamJSONFormatter)

    def test_get_formatter_html(self):
        """Test getting HTML formatter."""
        formatter = FormatterFactory.get_formatter("html")
        assert isinstance(formatter, HTMLFormatter)

    def test_get_formatter_rich(self):
        """Test getting Rich formatter."""
        formatter = FormatterFactory.get_formatter("rich")
        assert isinstance(formatter, RichFormatter)

    def test_get_formatter_case_insensitive(self):
        """Test that formatter type is case-insensitive."""
        formatter1 = FormatterFactory.get_formatter("JSON")
        formatter2 = FormatterFactory.get_formatter("Json")
        assert isinstance(formatter1, JSONFormatter)
        assert isinstance(formatter2, JSONFormatter)

    def test_get_formatter_unsupported(self):
        """Test getting unsupported formatter raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            FormatterFactory.get_formatter("unsupported")
        assert "Unsupported format type" in str(exc_info.value)
        assert "unsupported" in str(exc_info.value)

    def test_get_supported_formats(self):
        """Test getting list of supported formats."""
        formats = FormatterFactory.get_supported_formats()
        assert "json" in formats
        assert "markdown" in formats
        assert "stream-json" in formats
        assert "html" in formats
        assert "rich" in formats

    def test_get_formatter_function(self):
        """Test convenience get_formatter function."""
        formatter = get_formatter("json")
        assert isinstance(formatter, JSONFormatter)

    def test_get_formatter_default(self):
        """Test get_formatter with default (rich)."""
        formatter = get_formatter()
        assert isinstance(formatter, RichFormatter)
