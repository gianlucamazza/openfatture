"""Comprehensive tests for streaming events module.

Following 2025 best practices:
- Pytest with descriptive test names
- Comprehensive edge case coverage
- Factory pattern testing
- Serialization/deserialization validation
"""

from datetime import datetime

import pytest

from openfatture.ai.streaming import StreamEvent, StreamEventType


class TestStreamEventType:
    """Test StreamEventType enum and helper methods."""

    def test_enum_values(self):
        """Test all enum values are defined."""
        expected_types = {
            "content",
            "thinking",
            "tool_start",
            "tool_progress",
            "tool_result",
            "tool_error",
            "error",
            "warning",
            "status",
            "done",
            "metrics",
        }
        actual_types = {e.value for e in StreamEventType}
        assert actual_types == expected_types

    def test_is_content(self):
        """Test is_content() identifies content-bearing events."""
        assert StreamEventType.CONTENT.is_content()
        assert StreamEventType.THINKING.is_content()
        assert not StreamEventType.TOOL_START.is_content()
        assert not StreamEventType.ERROR.is_content()

    def test_is_tool_event(self):
        """Test is_tool_event() identifies tool-related events."""
        assert StreamEventType.TOOL_START.is_tool_event()
        assert StreamEventType.TOOL_PROGRESS.is_tool_event()
        assert StreamEventType.TOOL_RESULT.is_tool_event()
        assert StreamEventType.TOOL_ERROR.is_tool_event()
        assert not StreamEventType.CONTENT.is_tool_event()
        assert not StreamEventType.ERROR.is_tool_event()

    def test_is_error(self):
        """Test is_error() identifies error events."""
        assert StreamEventType.ERROR.is_error()
        assert StreamEventType.TOOL_ERROR.is_error()
        assert not StreamEventType.CONTENT.is_error()
        assert not StreamEventType.WARNING.is_error()


class TestStreamEventFactoryMethods:
    """Test StreamEvent factory methods."""

    def test_content_factory(self):
        """Test content() factory method."""
        event = StreamEvent.content("Hello world")
        assert event.type == StreamEventType.CONTENT
        assert event.data == "Hello world"
        assert isinstance(event.timestamp, datetime)

    def test_content_with_metadata(self):
        """Test content() with custom metadata."""
        event = StreamEvent.content("Hello", model="gpt-4", tokens=10)
        assert event.metadata["model"] == "gpt-4"
        assert event.metadata["tokens"] == 10

    def test_thinking_factory(self):
        """Test thinking() factory method."""
        event = StreamEvent.thinking("I need to search for invoices")
        assert event.type == StreamEventType.THINKING
        assert event.data == "I need to search for invoices"

    def test_tool_start_factory(self):
        """Test tool_start() factory method."""
        event = StreamEvent.tool_start(
            tool_name="search_invoices",
            parameters={"query": "2024", "limit": 10},
        )
        assert event.type == StreamEventType.TOOL_START
        assert event.data["tool_name"] == "search_invoices"
        assert event.data["parameters"]["query"] == "2024"
        assert event.data["parameters"]["limit"] == 10

    def test_tool_start_without_parameters(self):
        """Test tool_start() without parameters defaults to empty dict."""
        event = StreamEvent.tool_start(tool_name="health_check")
        assert event.data["parameters"] == {}

    def test_tool_progress_factory(self):
        """Test tool_progress() factory method."""
        event = StreamEvent.tool_progress(
            tool_name="search_invoices",
            progress="Searching database...",
            percentage=50.0,
        )
        assert event.type == StreamEventType.TOOL_PROGRESS
        assert event.data["tool_name"] == "search_invoices"
        assert event.data["progress"] == "Searching database..."
        assert event.data["percentage"] == 50.0

    def test_tool_progress_without_percentage(self):
        """Test tool_progress() without percentage."""
        event = StreamEvent.tool_progress(
            tool_name="test",
            progress="Working...",
        )
        assert event.data["percentage"] is None

    def test_tool_result_factory(self):
        """Test tool_result() factory method."""
        event = StreamEvent.tool_result(
            tool_name="search_invoices",
            result=["INV-001", "INV-002"],
            duration_ms=150.5,
        )
        assert event.type == StreamEventType.TOOL_RESULT
        assert event.data["tool_name"] == "search_invoices"
        assert "INV-001" in event.data["result"]
        assert event.data["duration_ms"] == 150.5

    def test_tool_error_factory(self):
        """Test tool_error() factory method."""
        event = StreamEvent.tool_error(
            tool_name="search_invoices",
            error="Database connection failed",
        )
        assert event.type == StreamEventType.TOOL_ERROR
        assert event.data["tool_name"] == "search_invoices"
        assert event.data["error"] == "Database connection failed"

    def test_error_factory(self):
        """Test error() factory method."""
        event = StreamEvent.error("API timeout")
        assert event.type == StreamEventType.ERROR
        assert event.data == "API timeout"

    def test_warning_factory(self):
        """Test warning() factory method."""
        event = StreamEvent.warning("Rate limit approaching")
        assert event.type == StreamEventType.WARNING
        assert event.data == "Rate limit approaching"

    def test_status_factory(self):
        """Test status() factory method."""
        event = StreamEvent.status("Connecting to API...")
        assert event.type == StreamEventType.STATUS
        assert event.data == "Connecting to API..."

    def test_done_factory(self):
        """Test done() factory method."""
        event = StreamEvent.done()
        assert event.type == StreamEventType.DONE
        assert event.data == {}

    def test_done_with_metadata(self):
        """Test done() with metadata."""
        event = StreamEvent.done(total_time=5.2, success=True)
        assert event.metadata["total_time"] == 5.2
        assert event.metadata["success"] is True

    def test_metrics_factory(self):
        """Test metrics() factory method."""
        event = StreamEvent.metrics(
            total_tokens=1500,
            duration_ms=2500.5,
            cache_hits=3,
        )
        assert event.type == StreamEventType.METRICS
        assert event.data["total_tokens"] == 1500
        assert event.data["duration_ms"] == 2500.5
        assert event.data["cache_hits"] == 3

    def test_metrics_optional_fields(self):
        """Test metrics() with only some fields."""
        event = StreamEvent.metrics(total_tokens=1000)
        assert event.data["total_tokens"] == 1000
        assert "duration_ms" not in event.data


class TestStreamEventMethods:
    """Test StreamEvent instance methods."""

    def test_is_content_method(self):
        """Test is_content() instance method."""
        content_event = StreamEvent.content("Hello")
        thinking_event = StreamEvent.thinking("Reasoning...")
        tool_event = StreamEvent.tool_start("search")

        assert content_event.is_content()
        assert thinking_event.is_content()
        assert not tool_event.is_content()

    def test_is_tool_event_method(self):
        """Test is_tool_event() instance method."""
        tool_start = StreamEvent.tool_start("search")
        tool_result = StreamEvent.tool_result("search", "result")
        content = StreamEvent.content("Hello")

        assert tool_start.is_tool_event()
        assert tool_result.is_tool_event()
        assert not content.is_tool_event()

    def test_is_error_method(self):
        """Test is_error() instance method."""
        error = StreamEvent.error("Failed")
        tool_error = StreamEvent.tool_error("search", "Error")
        warning = StreamEvent.warning("Warning")

        assert error.is_error()
        assert tool_error.is_error()
        assert not warning.is_error()

    def test_get_text_string_data(self):
        """Test get_text() with string data."""
        event = StreamEvent.content("Hello world")
        assert event.get_text() == "Hello world"

    def test_get_text_dict_data(self):
        """Test get_text() with dict data converts to string."""
        event = StreamEvent.tool_start("search", {"query": "test"})
        text = event.get_text()
        assert "search" in text
        assert "query" in text


class TestStreamEventSerialization:
    """Test StreamEvent serialization and deserialization."""

    def test_to_dict_content_event(self):
        """Test to_dict() for content event."""
        event = StreamEvent.content("Hello", source="user")
        data = event.to_dict()

        assert data["type"] == "content"
        assert data["data"] == "Hello"
        assert data["metadata"]["source"] == "user"
        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)

    def test_to_dict_tool_event(self):
        """Test to_dict() for tool event."""
        event = StreamEvent.tool_start("search", {"query": "test"})
        data = event.to_dict()

        assert data["type"] == "tool_start"
        assert data["data"]["tool_name"] == "search"
        assert data["data"]["parameters"]["query"] == "test"

    def test_from_dict_content_event(self):
        """Test from_dict() for content event."""
        original = StreamEvent.content("Hello", source="user")
        data = original.to_dict()
        restored = StreamEvent.from_dict(data)

        assert restored.type == original.type
        assert restored.data == original.data
        assert restored.metadata == original.metadata

    def test_from_dict_tool_event(self):
        """Test from_dict() for tool event."""
        original = StreamEvent.tool_result("search", "Found 5 items", duration_ms=123.4)
        data = original.to_dict()
        restored = StreamEvent.from_dict(data)

        assert restored.type == original.type
        assert restored.data["tool_name"] == original.data["tool_name"]
        assert restored.data["result"] == original.data["result"]

    def test_from_dict_without_timestamp(self):
        """Test from_dict() without timestamp uses current time."""
        data = {
            "type": "content",
            "data": "Hello",
            "metadata": {},
        }
        event = StreamEvent.from_dict(data)

        assert event.type == StreamEventType.CONTENT
        assert event.data == "Hello"
        assert isinstance(event.timestamp, datetime)

    def test_roundtrip_serialization(self):
        """Test complete serialization roundtrip preserves data."""
        original = StreamEvent.metrics(
            total_tokens=1500,
            duration_ms=2500.5,
            custom_metric=42,
        )

        # Roundtrip
        data = original.to_dict()
        restored = StreamEvent.from_dict(data)

        # Verify
        assert restored.type == original.type
        assert restored.data == original.data
        assert restored.metadata == original.metadata


class TestStreamEventEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_string_content(self):
        """Test event with empty string content."""
        event = StreamEvent.content("")
        assert event.data == ""
        assert event.get_text() == ""

    def test_very_long_content(self):
        """Test event with very long content."""
        long_text = "x" * 10000
        event = StreamEvent.content(long_text)
        assert len(event.data) == 10000

    def test_unicode_content(self):
        """Test event with unicode content."""
        event = StreamEvent.content("Fattura 🧾 €1.234,56")
        assert "🧾" in event.data
        assert "€" in event.data

    def test_nested_dict_data(self):
        """Test event with nested dictionary data."""
        event = StreamEvent.tool_start(
            "search",
            {
                "query": "test",
                "filters": {
                    "date": {"from": "2024-01-01", "to": "2024-12-31"},
                    "status": ["draft", "sent"],
                },
            },
        )
        assert event.data["parameters"]["filters"]["date"]["from"] == "2024-01-01"
        assert "draft" in event.data["parameters"]["filters"]["status"]

    def test_repr_string_data_short(self):
        """Test __repr__() with short string data."""
        event = StreamEvent.content("Hello")
        repr_str = repr(event)
        assert "StreamEvent" in repr_str
        assert "content" in repr_str
        assert "Hello" in repr_str

    def test_repr_string_data_long(self):
        """Test __repr__() with long string data truncates."""
        event = StreamEvent.content("x" * 100)
        repr_str = repr(event)
        assert "..." in repr_str
        assert len(repr_str) < 200  # Truncated

    def test_repr_dict_data(self):
        """Test __repr__() with dict data shows field count."""
        event = StreamEvent.tool_start("search", {"a": 1, "b": 2, "c": 3})
        repr_str = repr(event)
        assert "fields" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
