"""Streaming infrastructure for AI interactions.

This module provides structured events and bounded accumulators for
safe, observable streaming of AI responses.

Key Components:
- StreamEvent: Type-safe events for all streaming stages
- StreamEventType: Event type enumeration
- StreamAccumulator: Bounded buffer for content accumulation
- MultiStreamAccumulator: Multiple named streams

Example Usage:
    from openfatture.ai.streaming import StreamEvent, StreamAccumulator

    # Create accumulator
    acc = StreamAccumulator(max_size=1000)

    # Process stream events
    async for event in agent.execute_stream(context):
        if event.is_content():
            acc.add(event.get_text())
            print(event.get_text(), end="", flush=True)
        elif event.type == StreamEventType.TOOL_START:
            print(f"🔧 {event.data['tool_name']}")

    # Get accumulated text
    full_text = acc.get_text()

Best Practices (2025):
- Use StreamEvent for all streaming interactions
- Prefer bounded accumulators over unbounded lists
- Monitor overflow with accumulator.get_stats()
- Use factory methods (e.g., StreamEvent.content()) for clarity
"""

from openfatture.ai.streaming.accumulator import (
    MultiStreamAccumulator,
    StreamAccumulator,
)
from openfatture.ai.streaming.events import StreamEvent, StreamEventType

__all__ = [
    # Events
    "StreamEvent",
    "StreamEventType",
    # Accumulators
    "StreamAccumulator",
    "MultiStreamAccumulator",
]

__version__ = "1.0.0"
