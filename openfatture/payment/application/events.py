"""Domain events for the payment application."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from openfatture.payment.domain.enums import MatchType


@dataclass(frozen=True)
class PaymentEvent:
    """Base event with timestamp metadata."""

    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(UTC),
        init=False,
    )


@dataclass(frozen=True)
class TransactionMatchedEvent(PaymentEvent):
    """Event emitted when a bank transaction is matched to a payment."""

    transaction_id: UUID
    payment_id: int
    matched_amount: Decimal
    match_type: MatchType
    confidence: float | None


@dataclass(frozen=True)
class TransactionUnmatchedEvent(PaymentEvent):
    """Event emitted when a bank transaction reconciliation is reverted."""

    transaction_id: UUID
    payment_id: int | None
    reverted_amount: Decimal | None


class EventBus(Protocol):
    """Protocol for event bus implementations."""

    def publish(self, event: PaymentEvent) -> None:
        """Publish a domain event."""
        ...


class InMemoryEventBus:
    """Simple in-process event bus with synchronous/async listener support."""

    def __init__(self) -> None:
        self._listeners: dict[type[PaymentEvent], list[Callable[[PaymentEvent], object]]] = {}

    def subscribe(
        self,
        event_type: type[PaymentEvent],
        handler: Callable[[PaymentEvent], object],
    ) -> None:
        """Register handler for the given event type."""
        self._listeners.setdefault(event_type, []).append(handler)

    def has_listener(
        self,
        event_type: type[PaymentEvent],
        handler: Callable[[PaymentEvent], object],
    ) -> bool:
        """Check if handler is already registered for the given event type."""
        return handler in self._listeners.get(event_type, [])

    def publish(self, event: PaymentEvent) -> None:
        """Dispatch event to registered handlers."""
        for event_type, handlers in self._listeners.items():
            if isinstance(event, event_type):
                for handler in handlers:
                    handler(event)
