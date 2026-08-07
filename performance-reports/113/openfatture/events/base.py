"""Base event system infrastructure.

Provides the core event classes and event bus implementation for OpenFatture's
global event system.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID, uuid4

import structlog

logger = structlog.get_logger("events")


@dataclass(frozen=True)
class BaseEvent:
    """Base class for all domain events.

    All events are immutable (frozen dataclass) and include standard metadata:
    - event_id: Unique identifier for this event instance
    - occurred_at: Timestamp when the event occurred (UTC)
    - context: Optional additional context data

    Subclass this to create domain-specific events.
    """

    event_id: UUID = field(default_factory=uuid4, init=False)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC), init=False)
    context: dict[str, Any] | None = field(default=None, kw_only=True)


class EventBus(Protocol):
    """Protocol for event bus implementations.

    Defines the contract for event bus systems that support publish/subscribe
    patterns with both synchronous and asynchronous handlers.
    """

    def subscribe(
        self,
        event_type: type[BaseEvent],
        handler: Callable[[BaseEvent], Any],
        priority: int = 0,
    ) -> None:
        """Register a handler for the given event type.

        Args:
            event_type: The event class to listen for
            handler: Callable that processes the event (sync or async)
            priority: Handler priority (higher = executed first). Default: 0
        """
        ...

    def unsubscribe(
        self,
        event_type: type[BaseEvent],
        handler: Callable[[BaseEvent], Any],
    ) -> None:
        """Remove a handler for the given event type.

        Args:
            event_type: The event class
            handler: The handler to remove
        """
        ...

    def publish(self, event: BaseEvent) -> None:
        """Publish an event to all registered handlers.

        Args:
            event: The event to publish
        """
        ...

    async def publish_async(self, event: BaseEvent) -> None:
        """Publish an event asynchronously to all handlers.

        Args:
            event: The event to publish
        """
        ...


@dataclass
class _HandlerRegistration:
    """Internal registration data for event handlers."""

    handler: Callable[[BaseEvent], Any]
    priority: int
    is_async: bool


class GlobalEventBus:
    """Global in-memory event bus with sync/async handler support.

    Features:
    - Synchronous and asynchronous event handlers
    - Priority-based handler execution (higher priority = executed first)
    - Event type filtering (handlers only receive matching events)
    - Error isolation (one handler failure doesn't affect others)
    - Structured logging of all events and handler execution

    Example:
        >>> bus = GlobalEventBus()
        >>> bus.subscribe(InvoiceCreatedEvent, my_handler, priority=10)
        >>> bus.publish(InvoiceCreatedEvent(invoice_id=123))
    """

    def __init__(self) -> None:
        """Initialize the event bus."""
        self._handlers: dict[type[BaseEvent], list[_HandlerRegistration]] = defaultdict(list)
        self._event_count: dict[str, int] = defaultdict(int)

    def subscribe(
        self,
        event_type: type[BaseEvent],
        handler: Callable[[BaseEvent], Any],
        priority: int = 0,
    ) -> None:
        """Register a handler for the given event type.

        Args:
            event_type: The event class to listen for
            handler: Callable that processes the event (can be sync or async)
            priority: Handler priority (higher = executed first). Default: 0

        Example:
            >>> def my_handler(event: InvoiceCreatedEvent):
            ...     print(f"Invoice {event.invoice_id} created")
            >>> bus.subscribe(InvoiceCreatedEvent, my_handler, priority=10)
        """
        # Detect if handler is async
        is_async = asyncio.iscoroutinefunction(handler)

        registration = _HandlerRegistration(
            handler=handler,
            priority=priority,
            is_async=is_async,
        )

        self._handlers[event_type].append(registration)

        # Sort handlers by priority (descending)
        self._handlers[event_type].sort(key=lambda r: r.priority, reverse=True)

        logger.debug(
            "handler_registered",
            event_type=event_type.__name__,
            handler=handler.__name__,
            priority=priority,
            is_async=is_async,
        )

    def unsubscribe(
        self,
        event_type: type[BaseEvent],
        handler: Callable[[BaseEvent], Any],
    ) -> None:
        """Remove a handler for the given event type.

        Args:
            event_type: The event class
            handler: The handler to remove
        """
        if event_type in self._handlers:
            self._handlers[event_type] = [
                reg for reg in self._handlers[event_type] if reg.handler != handler
            ]

            logger.debug(
                "handler_unregistered",
                event_type=event_type.__name__,
                handler=handler.__name__,
            )

    def publish(self, event: BaseEvent) -> None:
        """Publish an event synchronously to all registered handlers.

        Executes all synchronous handlers immediately. Async handlers are
        scheduled but not awaited (fire-and-forget).

        Args:
            event: The event to publish

        Example:
            >>> bus.publish(InvoiceCreatedEvent(invoice_id=123, ...))
        """
        event_type = type(event)
        event_name = event_type.__name__

        self._event_count[event_name] += 1

        logger.info(
            "event_published",
            event_type=event_name,
            event_id=str(event.event_id),
            occurred_at=event.occurred_at.isoformat(),
        )

        # Find matching handlers
        handlers = self._get_handlers_for_event(event)

        if not handlers:
            logger.debug("no_handlers_found", event_type=event_name)
            return

        # Execute handlers by priority
        for registration in handlers:
            try:
                if registration.is_async:
                    # Schedule async handler (fire-and-forget)
                    asyncio.create_task(self._execute_async_handler(registration, event))
                else:
                    # Execute sync handler immediately
                    registration.handler(event)

                logger.debug(
                    "handler_executed",
                    event_type=event_name,
                    handler=registration.handler.__name__,
                    priority=registration.priority,
                )

            except Exception as e:
                # Isolate handler failures - log but don't propagate
                logger.error(
                    "handler_failed",
                    event_type=event_name,
                    handler=registration.handler.__name__,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )

    async def publish_async(self, event: BaseEvent) -> None:
        """Publish an event asynchronously to all registered handlers.

        Awaits all handlers (both sync and async) before returning.

        Args:
            event: The event to publish

        Example:
            >>> await bus.publish_async(InvoiceCreatedEvent(invoice_id=123, ...))
        """
        event_type = type(event)
        event_name = event_type.__name__

        self._event_count[event_name] += 1

        logger.info(
            "event_published_async",
            event_type=event_name,
            event_id=str(event.event_id),
            occurred_at=event.occurred_at.isoformat(),
        )

        # Find matching handlers
        handlers = self._get_handlers_for_event(event)

        if not handlers:
            logger.debug("no_handlers_found", event_type=event_name)
            return

        # Execute all handlers (await async, run sync in executor)
        tasks = []
        for registration in handlers:
            try:
                if registration.is_async:
                    task = asyncio.create_task(self._execute_async_handler(registration, event))
                else:
                    # Run sync handler in executor to avoid blocking
                    task = asyncio.create_task(asyncio.to_thread(registration.handler, event))
                tasks.append(task)

            except Exception as e:
                logger.error(
                    "handler_schedule_failed",
                    event_type=event_name,
                    handler=registration.handler.__name__,
                    error=str(e),
                    error_type=type(e).__name__,
                )

        # Await all handlers
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_async_handler(
        self,
        registration: _HandlerRegistration,
        event: BaseEvent,
    ) -> None:
        """Execute an async handler with error handling."""
        try:
            await registration.handler(event)
            logger.debug(
                "async_handler_executed",
                event_type=type(event).__name__,
                handler=registration.handler.__name__,
            )
        except Exception as e:
            logger.error(
                "async_handler_failed",
                event_type=type(event).__name__,
                handler=registration.handler.__name__,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )

    def _get_handlers_for_event(self, event: BaseEvent) -> list[_HandlerRegistration]:
        """Get all handlers that should receive this event.

        Checks for exact type match and inheritance (subclasses).
        """
        handlers: list[_HandlerRegistration] = []

        for event_type, registrations in self._handlers.items():
            if isinstance(event, event_type):
                handlers.extend(registrations)

        # Sort by priority (should already be sorted per event type, but ensure global order)
        handlers.sort(key=lambda r: r.priority, reverse=True)

        return handlers

    def get_stats(self) -> dict[str, Any]:
        """Get event bus statistics.

        Returns:
            Dictionary with event counts, handler counts, etc.
        """
        handler_count = sum(len(regs) for regs in self._handlers.values())

        return {
            "total_handlers": handler_count,
            "event_types": len(self._handlers),
            "events_published": dict(self._event_count),
            "total_events": sum(self._event_count.values()),
        }


# Global singleton instance
_global_event_bus: GlobalEventBus | None = None


def get_global_event_bus() -> GlobalEventBus:
    """Get the global event bus singleton instance.

    Returns:
        The global GlobalEventBus instance

    Example:
        >>> bus = get_global_event_bus()
        >>> bus.publish(InvoiceCreatedEvent(...))
    """
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = GlobalEventBus()
        logger.info("global_event_bus_initialized")
    return _global_event_bus
