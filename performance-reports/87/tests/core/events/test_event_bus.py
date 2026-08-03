"""Unit tests for GlobalEventBus."""

import asyncio
from dataclasses import dataclass
from decimal import Decimal

import pytest

from openfatture.core.events.base import BaseEvent, GlobalEventBus, get_global_event_bus
from openfatture.core.events.invoice_events import InvoiceCreatedEvent


# Test event for unit testing
@dataclass(frozen=True)
class TestEvent(BaseEvent):
    """Simple test event."""

    message: str = "test"


@dataclass(frozen=True)
class ChildTestEvent(TestEvent):
    """Child test event for inheritance testing."""

    child_data: str = "child"


@pytest.fixture
def event_bus():
    """Create a fresh event bus for each test."""
    return GlobalEventBus()


@pytest.fixture
def test_event():
    """Create a test event."""
    return TestEvent(message="Hello Event Bus")


def test_subscribe_handler(event_bus):
    """Test that handlers can be registered."""
    handler_called = []

    def handler(event: TestEvent):
        handler_called.append(event)

    event_bus.subscribe(TestEvent, handler)

    # Verify handler is registered
    assert TestEvent in event_bus._handlers
    assert len(event_bus._handlers[TestEvent]) == 1
    assert event_bus._handlers[TestEvent][0].handler == handler


def test_publish_sync(event_bus, test_event):
    """Test synchronous event publishing."""
    received_events = []

    def handler(event: TestEvent):
        received_events.append(event)

    event_bus.subscribe(TestEvent, handler)
    event_bus.publish(test_event)

    # Handler should have been called
    assert len(received_events) == 1
    assert received_events[0] == test_event
    assert received_events[0].message == "Hello Event Bus"


@pytest.mark.asyncio
async def test_publish_async(event_bus, test_event):
    """Test asynchronous event publishing."""
    received_events = []

    async def async_handler(event: TestEvent):
        await asyncio.sleep(0.01)  # Simulate async work
        received_events.append(event)

    event_bus.subscribe(TestEvent, async_handler)
    await event_bus.publish_async(test_event)

    # Handler should have been called
    assert len(received_events) == 1
    assert received_events[0] == test_event


def test_handler_priority(event_bus, test_event):
    """Test that handlers are executed in priority order (higher first)."""
    execution_order = []

    def low_priority(event: TestEvent):
        execution_order.append("low")

    def medium_priority(event: TestEvent):
        execution_order.append("medium")

    def high_priority(event: TestEvent):
        execution_order.append("high")

    # Register in random order with explicit priorities
    event_bus.subscribe(TestEvent, medium_priority, priority=5)
    event_bus.subscribe(TestEvent, low_priority, priority=1)
    event_bus.subscribe(TestEvent, high_priority, priority=10)

    event_bus.publish(test_event)

    # Should execute in priority order: high, medium, low
    assert execution_order == ["high", "medium", "low"]


def test_handler_error_isolation(event_bus, test_event):
    """Test that one handler failure doesn't affect others."""
    successful_handlers = []

    def failing_handler(event: TestEvent):
        raise ValueError("Handler failed!")

    def successful_handler_1(event: TestEvent):
        successful_handlers.append(1)

    def successful_handler_2(event: TestEvent):
        successful_handlers.append(2)

    # Register handlers
    event_bus.subscribe(TestEvent, successful_handler_1)
    event_bus.subscribe(TestEvent, failing_handler)
    event_bus.subscribe(TestEvent, successful_handler_2)

    # Publish should not raise despite failing handler
    event_bus.publish(test_event)

    # Both successful handlers should have executed
    assert len(successful_handlers) == 2
    assert 1 in successful_handlers
    assert 2 in successful_handlers


def test_event_type_filtering(event_bus):
    """Test that only handlers matching event type receive events."""
    test_event_received = []
    child_event_received = []

    def test_handler(event: TestEvent):
        test_event_received.append(event)

    def child_handler(event: ChildTestEvent):
        child_event_received.append(event)

    event_bus.subscribe(TestEvent, test_handler)
    event_bus.subscribe(ChildTestEvent, child_handler)

    # Publish TestEvent
    test_evt = TestEvent(message="test")
    event_bus.publish(test_evt)

    # Only test_handler should receive it
    assert len(test_event_received) == 1
    assert len(child_event_received) == 0

    # Clear
    test_event_received.clear()
    child_event_received.clear()

    # Publish ChildTestEvent
    child_evt = ChildTestEvent(message="child", child_data="data")
    event_bus.publish(child_evt)

    # Both handlers should receive it (inheritance)
    assert len(test_event_received) == 1
    assert len(child_event_received) == 1


def test_multiple_handlers_same_event(event_bus, test_event):
    """Test multiple handlers for the same event type."""
    handler1_called = []
    handler2_called = []
    handler3_called = []

    def handler1(event: TestEvent):
        handler1_called.append(event)

    def handler2(event: TestEvent):
        handler2_called.append(event)

    def handler3(event: TestEvent):
        handler3_called.append(event)

    event_bus.subscribe(TestEvent, handler1)
    event_bus.subscribe(TestEvent, handler2)
    event_bus.subscribe(TestEvent, handler3)

    event_bus.publish(test_event)

    # All handlers should have been called
    assert len(handler1_called) == 1
    assert len(handler2_called) == 1
    assert len(handler3_called) == 1


def test_unsubscribe_handler(event_bus, test_event):
    """Test handler removal."""
    handler_called = []

    def handler(event: TestEvent):
        handler_called.append(event)

    event_bus.subscribe(TestEvent, handler)
    event_bus.publish(test_event)

    assert len(handler_called) == 1

    # Unsubscribe
    event_bus.unsubscribe(TestEvent, handler)

    # Publish again
    event_bus.publish(test_event)

    # Handler should not be called again
    assert len(handler_called) == 1  # Still 1, not 2


@pytest.mark.asyncio
async def test_async_handler_execution(event_bus, test_event):
    """Test that async handlers are detected and awaited."""
    async_handler_called = []

    async def async_handler(event: TestEvent):
        await asyncio.sleep(0.01)
        async_handler_called.append(event)

    event_bus.subscribe(TestEvent, async_handler)
    await event_bus.publish_async(test_event)

    assert len(async_handler_called) == 1


def test_get_stats(event_bus):
    """Test event bus statistics."""

    def handler1(event: TestEvent):
        pass

    def handler2(event: TestEvent):
        pass

    event_bus.subscribe(TestEvent, handler1)
    event_bus.subscribe(TestEvent, handler2)
    event_bus.subscribe(InvoiceCreatedEvent, handler1)

    # Publish some events
    event_bus.publish(TestEvent(message="test1"))
    event_bus.publish(TestEvent(message="test2"))
    event_bus.publish(
        InvoiceCreatedEvent(
            invoice_id=1,
            invoice_number="001/2025",
            client_id=1,
            client_name="Test",
            total_amount=Decimal("1000"),
        )
    )

    stats = event_bus.get_stats()

    assert stats["total_handlers"] == 3  # 2 for TestEvent, 1 for InvoiceCreatedEvent
    assert stats["event_types"] == 2
    assert stats["events_published"]["TestEvent"] == 2
    assert stats["events_published"]["InvoiceCreatedEvent"] == 1
    assert stats["total_events"] == 3


def test_singleton_instance():
    """Test that get_global_event_bus returns singleton instance."""
    bus1 = get_global_event_bus()
    bus2 = get_global_event_bus()

    assert bus1 is bus2


def test_event_inheritance(event_bus):
    """Test that BaseEvent subscribers receive all event types."""
    all_events_received = []

    def base_handler(event: BaseEvent):
        all_events_received.append(event)

    event_bus.subscribe(BaseEvent, base_handler)

    # Publish different event types
    event_bus.publish(TestEvent(message="test"))
    event_bus.publish(
        InvoiceCreatedEvent(
            invoice_id=1,
            invoice_number="001/2025",
            client_id=1,
            client_name="Test",
            total_amount=Decimal("1000"),
        )
    )

    # Base handler should receive all events
    assert len(all_events_received) == 2
