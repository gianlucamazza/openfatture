"""Structured streaming events for chat interactions.

This module provides a type-safe event system for streaming AI responses,
tool execution, and status updates. Following 2025 best practices for
observable, testable streaming architectures.

Example:
    async for event in agent.execute_stream(context):
        match event.type:
            case StreamEventType.CONTENT:
                print(event.data, end="", flush=True)
            case StreamEventType.TOOL_START:
                print(f"🔧 {event.data['tool_name']}")
            case StreamEventType.TOOL_RESULT:
                print(f"✅ Result: {event.data['result']}")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class StreamEventType(Enum):
    """Types of streaming events.

    Design: Comprehensive event types for all stages of LLM interaction.
    """

    # Content streaming
    CONTENT = "content"  # Text chunk from LLM
    THINKING = "thinking"  # LLM reasoning/planning (ReAct)

    # Tool calling lifecycle
    TOOL_START = "tool_start"  # Tool execution beginning
    TOOL_PROGRESS = "tool_progress"  # Tool execution progress update
    TOOL_RESULT = "tool_result"  # Tool execution completed
    TOOL_ERROR = "tool_error"  # Tool execution failed

    # System events
    ERROR = "error"  # General error
    WARNING = "warning"  # Non-fatal warning
    STATUS = "status"  # Status update (e.g., "Connecting...")
    DONE = "done"  # Stream completed
    METRICS = "metrics"  # Performance metrics

    def is_content(self) -> bool:
        """Check if event is content-bearing."""
        return self in (
            StreamEventType.CONTENT,
            StreamEventType.THINKING,
        )

    def is_tool_event(self) -> bool:
        """Check if event is tool-related."""
        return self in (
            StreamEventType.TOOL_START,
            StreamEventType.TOOL_PROGRESS,
            StreamEventType.TOOL_RESULT,
            StreamEventType.TOOL_ERROR,
        )

    def is_error(self) -> bool:
        """Check if event indicates error."""
        return self in (StreamEventType.ERROR, StreamEventType.TOOL_ERROR)


@dataclass
class StreamEvent:
    """Structured streaming event.

    Attributes:
        type: Event type
        data: Event payload (string for content, dict for structured data)
        metadata: Additional context (timestamps, IDs, metrics)
        timestamp: Event creation time

    Design Rationale:
    - Type safety via enum prevents typos
    - Generic `data` field allows flexibility
    - Metadata for tracing/debugging
    - Immutable by default (frozen=True would break some use cases)
    """

    type: StreamEventType
    data: str | dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    @classmethod
    def content(cls, text: str, **metadata: Any) -> StreamEvent:
        """Create content event."""
        return cls(type=StreamEventType.CONTENT, data=text, metadata=metadata)

    @classmethod
    def thinking(cls, thought: str, **metadata: Any) -> StreamEvent:
        """Create thinking event (ReAct reasoning)."""
        return cls(type=StreamEventType.THINKING, data=thought, metadata=metadata)

    @classmethod
    def tool_start(
        cls,
        tool_name: str,
        parameters: dict[str, Any] | None = None,
        **metadata: Any,
    ) -> StreamEvent:
        """Create tool start event."""
        return cls(
            type=StreamEventType.TOOL_START,
            data={
                "tool_name": tool_name,
                "parameters": parameters or {},
            },
            metadata=metadata,
        )

    @classmethod
    def tool_progress(
        cls,
        tool_name: str,
        progress: str,
        percentage: float | None = None,
        **metadata: Any,
    ) -> StreamEvent:
        """Create tool progress event."""
        return cls(
            type=StreamEventType.TOOL_PROGRESS,
            data={
                "tool_name": tool_name,
                "progress": progress,
                "percentage": percentage,
            },
            metadata=metadata,
        )

    @classmethod
    def tool_result(
        cls,
        tool_name: str,
        result: Any,
        duration_ms: float | None = None,
        **metadata: Any,
    ) -> StreamEvent:
        """Create tool result event."""
        return cls(
            type=StreamEventType.TOOL_RESULT,
            data={
                "tool_name": tool_name,
                "result": str(result),
                "duration_ms": duration_ms,
            },
            metadata=metadata,
        )

    @classmethod
    def tool_error(
        cls,
        tool_name: str,
        error: str,
        **metadata: Any,
    ) -> StreamEvent:
        """Create tool error event."""
        return cls(
            type=StreamEventType.TOOL_ERROR,
            data={
                "tool_name": tool_name,
                "error": error,
            },
            metadata=metadata,
        )

    @classmethod
    def error(cls, message: str, **metadata: Any) -> StreamEvent:
        """Create error event."""
        return cls(type=StreamEventType.ERROR, data=message, metadata=metadata)

    @classmethod
    def warning(cls, message: str, **metadata: Any) -> StreamEvent:
        """Create warning event."""
        return cls(type=StreamEventType.WARNING, data=message, metadata=metadata)

    @classmethod
    def status(cls, message: str, **metadata: Any) -> StreamEvent:
        """Create status event."""
        return cls(type=StreamEventType.STATUS, data=message, metadata=metadata)

    @classmethod
    def done(cls, **metadata: Any) -> StreamEvent:
        """Create done event."""
        return cls(type=StreamEventType.DONE, data={}, metadata=metadata)

    @classmethod
    def metrics(
        cls,
        total_tokens: int | None = None,
        duration_ms: float | None = None,
        **extra_metrics: Any,
    ) -> StreamEvent:
        """Create metrics event."""
        data: dict[str, Any] = {}
        if total_tokens is not None:
            data["total_tokens"] = total_tokens
        if duration_ms is not None:
            data["duration_ms"] = duration_ms
        data.update(extra_metrics)
        return cls(type=StreamEventType.METRICS, data=data)

    def is_content(self) -> bool:
        """Check if event is content-bearing."""
        return self.type.is_content()

    def is_tool_event(self) -> bool:
        """Check if event is tool-related."""
        return self.type.is_tool_event()

    def is_error(self) -> bool:
        """Check if event indicates error."""
        return self.type.is_error()

    def get_text(self) -> str:
        """Get text content for content events."""
        if isinstance(self.data, str):
            return self.data
        return str(self.data)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "type": self.type.value,
            "data": self.data,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StreamEvent:
        """Create from dictionary."""
        return cls(
            type=StreamEventType(data["type"]),
            data=data["data"],
            metadata=data.get("metadata", {}),
            timestamp=(
                datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now()
            ),
        )

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        if isinstance(self.data, str):
            data_preview = self.data[:50] + "..." if len(self.data) > 50 else self.data
        else:
            data_preview = f"{len(self.data)} fields"
        return f"StreamEvent(type={self.type.value}, data={data_preview})"


__all__ = ["StreamEvent", "StreamEventType"]
