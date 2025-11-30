"""Bounded accumulator for safe streaming buffer management.

This module provides memory-safe accumulators for streaming content,
preventing unbounded growth that can lead to OOM errors.

Key Features:
- Automatic overflow handling with configurable maxlen
- Efficient deque-based implementation
- Statistics tracking for monitoring
- Thread-safe operations (via GIL)

Design Rationale (2025 Best Practices):
- Use collections.deque(maxlen=N) instead of manual list slicing
- Track overflow for observability
- Provide clear API for common operations
- O(1) append and automatic eviction
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass, field


@dataclass
class StreamAccumulator:
    """Bounded accumulator with automatic overflow handling.

    Attributes:
        max_size: Maximum number of chunks to retain
        buffer: Internal deque (bounded)
        overflow_count: Number of chunks evicted
        total_chunks: Total chunks added (including overflowed)

    Example:
        >>> acc = StreamAccumulator(max_size=1000)
        >>> for chunk in stream:
        ...     acc.add(chunk)
        >>> text = acc.get_text()
        >>> if acc.overflow_count > 0:
        ...     print(f"Warning: {acc.overflow_count} chunks lost")
    """

    max_size: int = 1000
    buffer: deque[str] = field(init=False)
    overflow_count: int = field(default=0, init=False)
    total_chunks: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        """Initialize bounded deque."""
        self.buffer = deque(maxlen=self.max_size)

    def add(self, chunk: str) -> None:
        """Add chunk to buffer.

        If buffer is full, oldest chunk is automatically evicted.

        Args:
            chunk: Text chunk to add
        """
        if len(self.buffer) == self.max_size:
            self.overflow_count += 1

        self.buffer.append(chunk)
        self.total_chunks += 1

    def add_many(self, chunks: list[str]) -> None:
        """Add multiple chunks efficiently.

        Args:
            chunks: List of text chunks
        """
        for chunk in chunks:
            self.add(chunk)

    def get_text(self) -> str:
        """Get accumulated text.

        Returns:
            Concatenated text from all chunks in buffer
        """
        return "".join(self.buffer)

    def get_chunks(self) -> list[str]:
        """Get list of chunks.

        Returns:
            List of chunks currently in buffer
        """
        return list(self.buffer)

    def clear(self) -> None:
        """Clear buffer and reset counters."""
        self.buffer.clear()
        self.overflow_count = 0
        self.total_chunks = 0

    def is_full(self) -> bool:
        """Check if buffer is at capacity."""
        return len(self.buffer) == self.max_size

    def has_overflow(self) -> bool:
        """Check if any chunks were lost to overflow."""
        return self.overflow_count > 0

    def get_stats(self) -> dict[str, int | float]:
        """Get accumulator statistics.

        Returns:
            Dictionary with buffer stats (int and float values)
        """
        return {
            "current_size": len(self.buffer),
            "max_size": self.max_size,
            "total_chunks": self.total_chunks,
            "overflow_count": self.overflow_count,
            "overflow_percentage": (
                (self.overflow_count / self.total_chunks * 100) if self.total_chunks > 0 else 0.0
            ),
        }

    def __len__(self) -> int:
        """Get current buffer size."""
        return len(self.buffer)

    def __iter__(self) -> Iterator[str]:
        """Iterate over chunks."""
        return iter(self.buffer)

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        stats = self.get_stats()
        return (
            f"StreamAccumulator("
            f"size={stats['current_size']}/{stats['max_size']}, "
            f"total={stats['total_chunks']}, "
            f"overflow={stats['overflow_count']})"
        )


@dataclass
class MultiStreamAccumulator:
    """Multiple accumulators for different content types.

    Useful for separating content from progress messages or multiple
    concurrent streams.

    Example:
        >>> acc = MultiStreamAccumulator()
        >>> acc.add("content", "Hello ")
        >>> acc.add("progress", "Tool 1 executing...")
        >>> acc.add("content", "world!")
        >>> content = acc.get_text("content")  # "Hello world!"
        >>> progress = acc.get_text("progress")  # "Tool 1 executing..."
    """

    max_size: int = 1000
    accumulators: dict[str, StreamAccumulator] = field(default_factory=dict)

    def add(self, stream_name: str, chunk: str) -> None:
        """Add chunk to named stream.

        Args:
            stream_name: Stream identifier
            chunk: Text chunk to add
        """
        if stream_name not in self.accumulators:
            self.accumulators[stream_name] = StreamAccumulator(max_size=self.max_size)

        self.accumulators[stream_name].add(chunk)

    def add_many(self, stream_name: str, chunks: list[str]) -> None:
        """Add multiple chunks to named stream.

        Args:
            stream_name: Stream identifier
            chunks: List of text chunks to add
        """
        if stream_name not in self.accumulators:
            self.accumulators[stream_name] = StreamAccumulator(max_size=self.max_size)

        self.accumulators[stream_name].add_many(chunks)

    def get_text(self, stream_name: str) -> str:
        """Get accumulated text from named stream.

        Args:
            stream_name: Stream identifier

        Returns:
            Concatenated text or empty string if stream doesn't exist
        """
        if stream_name in self.accumulators:
            return self.accumulators[stream_name].get_text()
        return ""

    def get_accumulator(self, stream_name: str) -> StreamAccumulator | None:
        """Get accumulator for named stream.

        Args:
            stream_name: Stream identifier

        Returns:
            StreamAccumulator or None if stream doesn't exist
        """
        return self.accumulators.get(stream_name)

    def get_all_stats(self) -> dict[str, dict[str, int | float]]:
        """Get statistics for all streams.

        Returns:
            Dictionary mapping stream names to their stats
        """
        return {name: acc.get_stats() for name, acc in self.accumulators.items()}

    def clear_all(self) -> None:
        """Clear all accumulators."""
        for acc in self.accumulators.values():
            acc.clear()

    def stream_names(self) -> list[str]:
        """Get list of active stream names."""
        return list(self.accumulators.keys())

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        stream_info = ", ".join(f"{name}={len(acc)}" for name, acc in self.accumulators.items())
        return f"MultiStreamAccumulator(streams={len(self.accumulators)}: {stream_info})"


__all__ = ["StreamAccumulator", "MultiStreamAccumulator"]
