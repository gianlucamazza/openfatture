"""Unit tests for batch processor."""

from datetime import datetime

import pytest

from openfatture.core.batch.processor import (
    BatchProcessor,
    BatchResult,
    ProgressTracker,
    chunk_list,
)

pytestmark = pytest.mark.unit


class TestBatchResult:
    """Tests for BatchResult."""

    def test_init(self):
        """Test initialization."""
        result = BatchResult(total=100)

        assert result.total == 100
        assert result.processed == 0
        assert result.succeeded == 0
        assert result.failed == 0
        assert len(result.errors) == 0
        assert len(result.results) == 0

    def test_add_success(self):
        """Test adding successful result."""
        result = BatchResult(total=10)

        result.add_success("result1")

        assert result.processed == 1
        assert result.succeeded == 1
        assert result.failed == 0
        assert "result1" in result.results

    def test_add_failure(self):
        """Test adding failed result."""
        result = BatchResult(total=10)

        result.add_failure("Error occurred")

        assert result.processed == 1
        assert result.succeeded == 0
        assert result.failed == 1
        assert "Error occurred" in result.errors

    def test_success_rate(self):
        """Test success rate calculation."""
        result = BatchResult(total=10)

        result.add_success()
        result.add_success()
        result.add_failure("error")

        assert result.success_rate == 20.0  # 2/10 = 20%

    def test_success_rate_empty(self):
        """Test success rate with zero total."""
        result = BatchResult(total=0)

        assert result.success_rate == 0.0

    def test_duration(self):
        """Test duration calculation."""
        result = BatchResult()
        result.start_time = datetime(2025, 1, 1, 12, 0, 0)
        result.end_time = datetime(2025, 1, 1, 12, 0, 10)

        assert result.duration == 10.0

    def test_duration_none(self):
        """Test duration when times not set."""
        result = BatchResult()

        assert result.duration is None


class TestBatchProcessor:
    """Tests for BatchProcessor."""

    def test_init(self):
        """Test initialization."""
        func = lambda x: x * 2
        processor = BatchProcessor(process_func=func, batch_size=50)

        assert processor.process_func == func
        assert processor.batch_size == 50
        assert processor.fail_fast is False

    def test_process_empty_list(self):
        """Test processing empty list."""
        processor = BatchProcessor(process_func=lambda x: x)

        result = processor.process([])

        assert result.total == 0
        assert result.processed == 0

    def test_process_success(self):
        """Test successful processing."""
        processor = BatchProcessor(process_func=lambda x: x * 2)

        items = [1, 2, 3, 4, 5]
        result = processor.process(items)

        assert result.total == 5
        assert result.processed == 5
        assert result.succeeded == 5
        assert result.failed == 0
        assert result.results == [2, 4, 6, 8, 10]

    def test_process_with_errors(self):
        """Test processing with some errors."""

        def process_func(x):
            if x == 3:
                raise ValueError("Error on 3")
            return x * 2

        processor = BatchProcessor(process_func=process_func, fail_fast=False)

        items = [1, 2, 3, 4, 5]
        result = processor.process(items)

        assert result.total == 5
        assert result.processed == 5
        assert result.succeeded == 4
        assert result.failed == 1
        assert len(result.errors) == 1
        assert "Error on 3" in result.errors[0]

    def test_process_fail_fast(self):
        """Test fail fast mode."""

        def process_func(x):
            if x == 3:
                raise ValueError("Error on 3")
            return x * 2

        processor = BatchProcessor(process_func=process_func, fail_fast=True)

        items = [1, 2, 3, 4, 5]
        result = processor.process(items)

        assert result.total == 5
        assert result.processed == 3  # Stopped at item 3
        assert result.succeeded == 2
        assert result.failed == 1

    def test_process_with_progress_callback(self):
        """Test progress callback."""
        callback_calls = []

        def callback(current, total):
            callback_calls.append((current, total))

        processor = BatchProcessor(process_func=lambda x: x, progress_callback=callback)

        items = [1, 2, 3]
        processor.process(items)

        assert len(callback_calls) == 3
        assert callback_calls[0] == (1, 3)
        assert callback_calls[1] == (2, 3)
        assert callback_calls[2] == (3, 3)

    def test_process_with_filter(self):
        """Test processing with filter."""
        processor = BatchProcessor(process_func=lambda x: x * 2)

        items = [1, 2, 3, 4, 5]
        result = processor.process_with_filter(items, filter_func=lambda x: x % 2 == 0)

        # Only even numbers: 2, 4
        assert result.total == 2
        assert result.succeeded == 2
        assert result.results == [4, 8]


class TestChunkList:
    """Tests for chunk_list function."""

    def test_chunk_list_exact(self):
        """Test chunking with exact division."""
        items = [1, 2, 3, 4, 5, 6]
        chunks = chunk_list(items, chunk_size=2)

        assert len(chunks) == 3
        assert chunks[0] == [1, 2]
        assert chunks[1] == [3, 4]
        assert chunks[2] == [5, 6]

    def test_chunk_list_remainder(self):
        """Test chunking with remainder."""
        items = [1, 2, 3, 4, 5]
        chunks = chunk_list(items, chunk_size=2)

        assert len(chunks) == 3
        assert chunks[0] == [1, 2]
        assert chunks[1] == [3, 4]
        assert chunks[2] == [5]

    def test_chunk_list_single_chunk(self):
        """Test chunking into single chunk."""
        items = [1, 2, 3]
        chunks = chunk_list(items, chunk_size=10)

        assert len(chunks) == 1
        assert chunks[0] == [1, 2, 3]

    def test_chunk_list_empty(self):
        """Test chunking empty list."""
        items = []
        chunks = chunk_list(items, chunk_size=5)

        assert len(chunks) == 0


class TestProgressTracker:
    """Tests for ProgressTracker."""

    def test_init(self):
        """Test initialization."""
        tracker = ProgressTracker(total=100, description="Test")

        assert tracker.total == 100
        assert tracker.current == 0
        assert tracker.description == "Test"

    def test_update(self):
        """Test updating progress."""
        tracker = ProgressTracker(total=100)

        tracker.update(10)
        assert tracker.current == 10

        tracker.update(5)
        assert tracker.current == 15

    def test_get_percentage(self):
        """Test percentage calculation."""
        tracker = ProgressTracker(total=100)

        assert tracker.get_percentage() == 0.0

        tracker.update(25)
        assert tracker.get_percentage() == 25.0

        tracker.update(25)
        assert tracker.get_percentage() == 50.0

    def test_get_percentage_zero_total(self):
        """Test percentage with zero total."""
        tracker = ProgressTracker(total=0)

        assert tracker.get_percentage() == 100.0

    def test_get_eta_seconds(self):
        """Test ETA calculation."""
        import time

        tracker = ProgressTracker(total=100)

        # No ETA if no progress
        assert tracker.get_eta_seconds() is None

        # Make some progress
        tracker.update(50)
        time.sleep(0.1)

        eta = tracker.get_eta_seconds()
        assert eta is not None
        assert eta > 0

    def test_get_status(self):
        """Test status string."""
        tracker = ProgressTracker(total=100, description="Processing")

        status = tracker.get_status()
        assert "Processing" in status
        assert "0/100" in status
        assert "0.0%" in status

        tracker.update(50)
        status = tracker.get_status()
        assert "50/100" in status
        assert "50.0%" in status

    def test_is_complete(self):
        """Test completion check."""
        tracker = ProgressTracker(total=10)

        assert tracker.is_complete() is False

        tracker.update(5)
        assert tracker.is_complete() is False

        tracker.update(5)
        assert tracker.is_complete() is True

        tracker.update(1)  # Over 100%
        assert tracker.is_complete() is True
