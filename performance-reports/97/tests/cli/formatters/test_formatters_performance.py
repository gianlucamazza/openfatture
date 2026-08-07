"""Performance benchmarks for formatters."""

import pytest

from openfatture.ai.domain.response import AgentResponse, ResponseStatus, UsageMetrics
from openfatture.cli.formatters.factory import get_formatter


@pytest.fixture
def small_response():
    """Small response for benchmarking."""
    return AgentResponse(
        content="Short response text.",
        status=ResponseStatus.SUCCESS,
        provider="test",
        model="test-model",
        usage=UsageMetrics(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        latency_ms=100,
    )


@pytest.fixture
def medium_response():
    """Medium response for benchmarking."""
    content = " ".join(["This is a longer response text"] * 50)
    return AgentResponse(
        content=content,
        status=ResponseStatus.SUCCESS,
        provider="test",
        model="test-model",
        usage=UsageMetrics(prompt_tokens=100, completion_tokens=200, total_tokens=300),
        latency_ms=500,
    )


@pytest.fixture
def large_response():
    """Large response for benchmarking."""
    content = " ".join(["This is a very long response text that simulates real-world usage"] * 500)
    return AgentResponse(
        content=content,
        status=ResponseStatus.SUCCESS,
        provider="test",
        model="test-model",
        usage=UsageMetrics(prompt_tokens=500, completion_tokens=1000, total_tokens=1500),
        latency_ms=2000,
    )


@pytest.mark.benchmark
class TestJSONFormatterPerformance:
    """Performance tests for JSONFormatter."""

    def test_json_format_small_response(self, benchmark, small_response):
        """Benchmark JSON formatting of small response (target: <10ms)."""
        formatter = get_formatter("json")
        result = benchmark(formatter.format_response, small_response)
        assert len(result) > 0

    def test_json_format_medium_response(self, benchmark, medium_response):
        """Benchmark JSON formatting of medium response."""
        formatter = get_formatter("json")
        result = benchmark(formatter.format_response, medium_response)
        assert len(result) > 0

    def test_json_format_large_response(self, benchmark, large_response):
        """Benchmark JSON formatting of large response."""
        formatter = get_formatter("json")
        result = benchmark(formatter.format_response, large_response)
        assert len(result) > 0


@pytest.mark.benchmark
class TestMarkdownFormatterPerformance:
    """Performance tests for MarkdownFormatter."""

    def test_markdown_format_small_response(self, benchmark, small_response):
        """Benchmark Markdown formatting of small response (target: <50ms)."""
        formatter = get_formatter("markdown")
        result = benchmark(formatter.format_response, small_response)
        assert len(result) > 0

    def test_markdown_format_large_response(self, benchmark, large_response):
        """Benchmark Markdown formatting of large response."""
        formatter = get_formatter("markdown")
        result = benchmark(formatter.format_response, large_response)
        assert len(result) > 0


@pytest.mark.benchmark
class TestHTMLFormatterPerformance:
    """Performance tests for HTMLFormatter."""

    def test_html_format_small_response(self, benchmark, small_response):
        """Benchmark HTML formatting of small response (target: <100ms)."""
        formatter = get_formatter("html")
        result = benchmark(formatter.format_response, small_response)
        assert len(result) > 0

    def test_html_format_large_response(self, benchmark, large_response):
        """Benchmark HTML formatting of large response."""
        formatter = get_formatter("html")
        result = benchmark(formatter.format_response, large_response)
        assert len(result) > 0


@pytest.mark.benchmark
class TestStreamJSONFormatterPerformance:
    """Performance tests for StreamJSON formatter."""

    def test_stream_json_chunk_throughput(self, benchmark):
        """Benchmark StreamJSON chunk formatting (target: >100 chunks/sec)."""
        formatter = get_formatter("stream-json")
        chunks = ["chunk " + str(i) for i in range(100)]

        def format_chunks():
            return [formatter.format_stream_chunk(chunk) for chunk in chunks]

        result = benchmark(format_chunks)
        assert len(result) == 100


@pytest.mark.benchmark
class TestFormatterFactoryPerformance:
    """Performance tests for FormatterFactory."""

    def test_formatter_instantiation(self, benchmark):
        """Benchmark formatter creation via factory."""
        result = benchmark(get_formatter, "json")
        assert result is not None

    def test_formatter_lookup_speed(self, benchmark):
        """Benchmark formatter lookup performance."""
        formats = ["json", "markdown", "html", "stream-json", "rich"]

        def lookup_all():
            return [get_formatter(fmt) for fmt in formats]

        result = benchmark(lookup_all)
        assert len(result) == 5
