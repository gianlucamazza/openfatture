"""
Batch processor for bulk operations.

Provides framework for processing multiple items with progress tracking.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, TypeVar

T = TypeVar("T")
R = TypeVar("R")


@dataclass
class BatchResult:
    """
    Result of batch operation.

    Tracks success, failures, and errors.
    """

    total: int = 0
    processed: int = 0
    succeeded: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)
    results: list[Any] = field(default_factory=list)
    start_time: datetime | None = None
    end_time: datetime | None = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total == 0:
            return 0.0
        return (self.succeeded / self.total) * 100

    @property
    def duration(self) -> float | None:
        """Calculate operation duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def add_success(self, result: Any = None) -> None:
        """Record successful operation."""
        self.processed += 1
        self.succeeded += 1
        if result is not None:
            self.results.append(result)

    def add_failure(self, error: str) -> None:
        """Record failed operation."""
        self.processed += 1
        self.failed += 1
        self.errors.append(error)


class BatchProcessor(Generic[T, R]):
    """
    Generic batch processor.

    Processes items in batches with error handling and progress tracking.

    Usage:
        processor = BatchProcessor(
            process_func=lambda item: process_invoice(item),
            batch_size=100
        )
        result = processor.process(invoice_list)
    """

    def __init__(
        self,
        process_func: Callable[[T], R],
        batch_size: int = 100,
        fail_fast: bool = False,
        progress_callback: Callable[[int, int], None] | None = None,
    ):
        """
        Initialize batch processor.

        Args:
            process_func: Function to process each item
            batch_size: Number of items to process in each batch
            fail_fast: If True, stop on first error
            progress_callback: Optional callback for progress updates (current, total)
        """
        self.process_func = process_func
        self.batch_size = batch_size
        self.fail_fast = fail_fast
        self.progress_callback = progress_callback

    def process(self, items: list[T]) -> BatchResult:
        """
        Process list of items in batches.

        Args:
            items: List of items to process

        Returns:
            BatchResult with operation summary
        """
        result = BatchResult(
            total=len(items),
            start_time=datetime.now(),
        )

        for i, item in enumerate(items):
            try:
                # Process item
                item_result = self.process_func(item)
                result.add_success(item_result)

                # Update progress
                if self.progress_callback:
                    self.progress_callback(i + 1, len(items))

            except Exception as e:
                # Record error
                error_msg = f"Item {i + 1}: {str(e)}"
                result.add_failure(error_msg)

                # Stop if fail_fast enabled
                if self.fail_fast:
                    result.end_time = datetime.now()
                    return result

        result.end_time = datetime.now()
        return result

    def process_with_filter(
        self,
        items: list[T],
        filter_func: Callable[[T], bool],
    ) -> BatchResult:
        """
        Process items with pre-filtering.

        Args:
            items: List of items
            filter_func: Function to filter items (return True to process)

        Returns:
            BatchResult
        """
        filtered_items = [item for item in items if filter_func(item)]
        return self.process(filtered_items)


def chunk_list(items: list[T], chunk_size: int) -> list[list[T]]:
    """
    Split list into chunks.

    Args:
        items: List to split
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]


class ProgressTracker:
    """
    Track progress of long-running operations.

    Usage:
        tracker = ProgressTracker(total=1000)
        for item in items:
            # ... process item
            tracker.update(1)
            print(tracker.get_status())
    """

    def __init__(self, total: int, description: str = "Processing"):
        """
        Initialize progress tracker.

        Args:
            total: Total number of items
            description: Description of operation
        """
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = datetime.now()

    def update(self, increment: int = 1) -> None:
        """
        Update progress.

        Args:
            increment: Amount to increment by
        """
        self.current += increment

    def get_percentage(self) -> float:
        """Get completion percentage."""
        if self.total == 0:
            return 100.0
        return (self.current / self.total) * 100

    def get_eta_seconds(self) -> float | None:
        """
        Estimate time remaining in seconds.

        Returns:
            Estimated seconds remaining, or None if cannot estimate
        """
        if self.current == 0:
            return None

        elapsed = (datetime.now() - self.start_time).total_seconds()
        rate = self.current / elapsed
        remaining = self.total - self.current

        return remaining / rate if rate > 0 else None

    def get_status(self) -> str:
        """
        Get formatted status string.

        Returns:
            Status string like "Processing: 50/100 (50.0%)"
        """
        percentage = self.get_percentage()
        return f"{self.description}: {self.current}/{self.total} ({percentage:.1f}%)"

    def is_complete(self) -> bool:
        """Check if operation is complete."""
        return self.current >= self.total
