"""Comprehensive tests for streaming accumulator module.

Testing bounded buffer behavior, overflow handling, and statistics tracking
following 2025 best practices.
"""

import pytest

from openfatture.ai.streaming import MultiStreamAccumulator, StreamAccumulator


class TestStreamAccumulatorBasics:
    """Test basic StreamAccumulator operations."""

    def test_initialization_default(self):
        """Test default initialization."""
        acc = StreamAccumulator()
        assert acc.max_size == 1000
        assert len(acc) == 0
        assert acc.total_chunks == 0
        assert acc.overflow_count == 0

    def test_initialization_custom_size(self):
        """Test initialization with custom max_size."""
        acc = StreamAccumulator(max_size=100)
        assert acc.max_size == 100

    def test_add_single_chunk(self):
        """Test adding a single chunk."""
        acc = StreamAccumulator()
        acc.add("Hello")
        assert len(acc) == 1
        assert acc.total_chunks == 1
        assert acc.get_text() == "Hello"

    def test_add_multiple_chunks(self):
        """Test adding multiple chunks."""
        acc = StreamAccumulator()
        acc.add("Hello")
        acc.add(" ")
        acc.add("world")
        assert len(acc) == 3
        assert acc.total_chunks == 3
        assert acc.get_text() == "Hello world"

    def test_add_many(self):
        """Test add_many() batch operation."""
        acc = StreamAccumulator()
        chunks = ["Hello", " ", "world", "!"]
        acc.add_many(chunks)
        assert len(acc) == 4
        assert acc.get_text() == "Hello world!"

    def test_get_chunks(self):
        """Test get_chunks() returns list."""
        acc = StreamAccumulator()
        acc.add("Hello")
        acc.add("world")
        chunks = acc.get_chunks()
        assert isinstance(chunks, list)
        assert chunks == ["Hello", "world"]

    def test_clear(self):
        """Test clear() resets accumulator."""
        acc = StreamAccumulator()
        acc.add("Hello")
        acc.add("world")
        acc.clear()
        assert len(acc) == 0
        assert acc.total_chunks == 0
        assert acc.overflow_count == 0
        assert acc.get_text() == ""

    def test_iteration(self):
        """Test iteration over chunks."""
        acc = StreamAccumulator()
        chunks = ["a", "b", "c"]
        acc.add_many(chunks)

        result = list(acc)
        assert result == chunks


class TestStreamAccumulatorBounded:
    """Test bounded buffer behavior and overflow handling."""

    def test_not_full_initially(self):
        """Test is_full() returns False initially."""
        acc = StreamAccumulator(max_size=10)
        assert not acc.is_full()

    def test_becomes_full(self):
        """Test is_full() returns True when at capacity."""
        acc = StreamAccumulator(max_size=3)
        acc.add("a")
        acc.add("b")
        acc.add("c")
        assert acc.is_full()

    def test_overflow_behavior(self):
        """Test overflow evicts oldest chunks."""
        acc = StreamAccumulator(max_size=3)
        acc.add("1")
        acc.add("2")
        acc.add("3")
        acc.add("4")  # Evicts "1"

        assert len(acc) == 3
        assert acc.get_chunks() == ["2", "3", "4"]

    def test_overflow_count_tracking(self):
        """Test overflow_count tracks evicted chunks."""
        acc = StreamAccumulator(max_size=3)
        acc.add_many(["1", "2", "3", "4", "5"])

        assert acc.overflow_count == 2
        assert acc.total_chunks == 5
        assert len(acc) == 3

    def test_has_overflow(self):
        """Test has_overflow() detection."""
        acc = StreamAccumulator(max_size=2)
        assert not acc.has_overflow()

        acc.add("a")
        acc.add("b")
        assert not acc.has_overflow()

        acc.add("c")
        assert acc.has_overflow()

    def test_large_overflow(self):
        """Test large overflow scenario."""
        acc = StreamAccumulator(max_size=10)
        for i in range(100):
            acc.add(str(i))

        assert len(acc) == 10
        assert acc.overflow_count == 90
        assert acc.total_chunks == 100

    def test_continuous_overflow(self):
        """Test overflow with continuous streaming."""
        acc = StreamAccumulator(max_size=5)
        for i in range(20):
            acc.add(f"chunk_{i}")

        # Should contain last 5 chunks
        chunks = acc.get_chunks()
        assert chunks == ["chunk_15", "chunk_16", "chunk_17", "chunk_18", "chunk_19"]


class TestStreamAccumulatorStatistics:
    """Test statistics tracking."""

    def test_get_stats_empty(self):
        """Test get_stats() for empty accumulator."""
        acc = StreamAccumulator(max_size=100)
        stats = acc.get_stats()

        assert stats["current_size"] == 0
        assert stats["max_size"] == 100
        assert stats["total_chunks"] == 0
        assert stats["overflow_count"] == 0
        assert stats["overflow_percentage"] == 0.0

    def test_get_stats_partial(self):
        """Test get_stats() for partially filled accumulator."""
        acc = StreamAccumulator(max_size=10)
        acc.add_many(["a", "b", "c"])
        stats = acc.get_stats()

        assert stats["current_size"] == 3
        assert stats["max_size"] == 10
        assert stats["total_chunks"] == 3
        assert stats["overflow_count"] == 0
        assert stats["overflow_percentage"] == 0.0

    def test_get_stats_with_overflow(self):
        """Test get_stats() with overflow."""
        acc = StreamAccumulator(max_size=5)
        acc.add_many([f"{i}" for i in range(10)])
        stats = acc.get_stats()

        assert stats["current_size"] == 5
        assert stats["max_size"] == 5
        assert stats["total_chunks"] == 10
        assert stats["overflow_count"] == 5
        assert stats["overflow_percentage"] == 50.0

    def test_overflow_percentage_calculation(self):
        """Test overflow percentage calculation."""
        acc = StreamAccumulator(max_size=10)
        acc.add_many([f"{i}" for i in range(100)])
        stats = acc.get_stats()

        assert stats["overflow_percentage"] == 90.0  # 90 out of 100

    def test_repr(self):
        """Test __repr__() output."""
        acc = StreamAccumulator(max_size=10)
        acc.add_many(["a", "b", "c"])

        repr_str = repr(acc)
        assert "StreamAccumulator" in repr_str
        assert "3/10" in repr_str  # size/max_size
        assert "total=3" in repr_str


class TestStreamAccumulatorEdgeCases:
    """Test edge cases and corner scenarios."""

    def test_empty_string_chunks(self):
        """Test handling of empty string chunks."""
        acc = StreamAccumulator()
        acc.add("")
        acc.add("")
        assert len(acc) == 2
        assert acc.get_text() == ""

    def test_very_long_chunks(self):
        """Test handling of very long chunks."""
        acc = StreamAccumulator(max_size=3)
        long_chunk = "x" * 10000
        acc.add(long_chunk)
        assert len(acc) == 1
        assert len(acc.get_text()) == 10000

    def test_unicode_chunks(self):
        """Test handling of unicode chunks."""
        acc = StreamAccumulator()
        acc.add("Ciao 🇮🇹")
        acc.add(" ")
        acc.add("Fattura €1.234,56")
        text = acc.get_text()
        assert "🇮🇹" in text
        assert "€" in text

    def test_size_one_accumulator(self):
        """Test accumulator with max_size=1."""
        acc = StreamAccumulator(max_size=1)
        acc.add("a")
        acc.add("b")
        acc.add("c")

        assert len(acc) == 1
        assert acc.get_chunks() == ["c"]
        assert acc.overflow_count == 2

    def test_mixed_chunk_types(self):
        """Test accumulator with various chunk sizes."""
        acc = StreamAccumulator(max_size=100)
        acc.add("")
        acc.add("short")
        acc.add("x" * 1000)
        acc.add("end")

        assert len(acc) == 4
        text = acc.get_text()
        assert text.startswith("short")
        assert text.endswith("end")


class TestMultiStreamAccumulator:
    """Test MultiStreamAccumulator for named streams."""

    def test_initialization(self):
        """Test default initialization."""
        multi = MultiStreamAccumulator()
        assert multi.max_size == 1000
        assert len(multi.accumulators) == 0

    def test_add_single_stream(self):
        """Test adding to a single stream."""
        multi = MultiStreamAccumulator()
        multi.add("content", "Hello")
        multi.add("content", " world")

        assert multi.get_text("content") == "Hello world"

    def test_add_multiple_streams(self):
        """Test adding to multiple streams."""
        multi = MultiStreamAccumulator()
        multi.add("content", "Hello")
        multi.add("progress", "Tool 1 executing...")
        multi.add("content", " world")
        multi.add("progress", "Tool 1 complete")

        assert multi.get_text("content") == "Hello world"
        assert "Tool 1 executing" in multi.get_text("progress")

    def test_get_nonexistent_stream(self):
        """Test getting text from nonexistent stream returns empty."""
        multi = MultiStreamAccumulator()
        assert multi.get_text("nonexistent") == ""

    def test_get_accumulator(self):
        """Test get_accumulator() returns correct accumulator."""
        multi = MultiStreamAccumulator()
        multi.add("test", "data")

        acc = multi.get_accumulator("test")
        assert acc is not None
        assert isinstance(acc, StreamAccumulator)
        assert acc.get_text() == "data"

    def test_get_accumulator_nonexistent(self):
        """Test get_accumulator() returns None for nonexistent stream."""
        multi = MultiStreamAccumulator()
        assert multi.get_accumulator("nonexistent") is None

    def test_stream_names(self):
        """Test stream_names() returns active streams."""
        multi = MultiStreamAccumulator()
        multi.add("a", "1")
        multi.add("b", "2")
        multi.add("c", "3")

        names = multi.stream_names()
        assert set(names) == {"a", "b", "c"}

    def test_get_all_stats(self):
        """Test get_all_stats() returns all stream statistics."""
        multi = MultiStreamAccumulator(max_size=5)
        multi.add("stream1", "data")
        multi.add_many("stream2", ["a", "b", "c"])

        all_stats = multi.get_all_stats()
        assert "stream1" in all_stats
        assert "stream2" in all_stats
        assert all_stats["stream1"]["current_size"] == 1
        assert all_stats["stream2"]["current_size"] == 3

    def test_clear_all(self):
        """Test clear_all() clears all streams."""
        multi = MultiStreamAccumulator()
        multi.add("a", "1")
        multi.add("b", "2")
        multi.add("c", "3")

        multi.clear_all()

        # Accumulators still exist but are empty
        assert len(multi.accumulators) == 3
        for name in ["a", "b", "c"]:
            acc = multi.get_accumulator(name)
            assert len(acc) == 0

    def test_bounded_per_stream(self):
        """Test each stream has independent bounded buffer."""
        multi = MultiStreamAccumulator(max_size=3)

        # Fill stream1 beyond capacity
        multi.add_many("stream1", ["1", "2", "3", "4", "5"])

        # Fill stream2 partially
        multi.add_many("stream2", ["a", "b"])

        # Check independent bounds
        acc1 = multi.get_accumulator("stream1")
        acc2 = multi.get_accumulator("stream2")

        assert len(acc1) == 3
        assert acc1.overflow_count == 2
        assert len(acc2) == 2
        assert acc2.overflow_count == 0

    def test_repr(self):
        """Test __repr__() output."""
        multi = MultiStreamAccumulator()
        multi.add("content", "hello")
        multi.add("progress", "working")

        repr_str = repr(multi)
        assert "MultiStreamAccumulator" in repr_str
        assert "streams=2" in repr_str


class TestMultiStreamAccumulatorAdvanced:
    """Test advanced MultiStreamAccumulator scenarios."""

    def test_dynamic_stream_creation(self):
        """Test streams are created on-the-fly."""
        multi = MultiStreamAccumulator()

        # Add to new streams without pre-creation
        multi.add("stream1", "data1")
        multi.add("stream2", "data2")
        multi.add("stream3", "data3")

        assert len(multi.stream_names()) == 3

    def test_independent_overflow_tracking(self):
        """Test overflow tracking is independent per stream."""
        multi = MultiStreamAccumulator(max_size=2)

        # Stream1 overflows
        multi.add_many("stream1", ["a", "b", "c", "d"])

        # Stream2 doesn't overflow
        multi.add("stream2", "x")

        stats = multi.get_all_stats()
        assert stats["stream1"]["overflow_count"] == 2
        assert stats["stream2"]["overflow_count"] == 0

    def test_mixed_stream_usage(self):
        """Test realistic mixed stream usage."""
        multi = MultiStreamAccumulator(max_size=100)

        # Simulate chat with content and tool calls
        multi.add("content", "Let me search for invoices...")
        multi.add("tool_calls", "🔧 search_invoices(query='2024')")
        multi.add("tool_results", "✅ Found 5 invoices")
        multi.add("content", "\n\nI found 5 invoices for 2024.")

        content = multi.get_text("content")
        assert "Let me search" in content
        assert "I found 5 invoices" in content

        tools = multi.get_text("tool_calls")
        assert "search_invoices" in tools


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
