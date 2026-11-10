"""Domain events for the payment application.

Payment events are global domain events: they flow through
``openfatture.events.GlobalEventBus`` and therefore reach the audit log,
``EventLog`` persistence, hooks and custom ``event_listeners``.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from openfatture.events.base import BaseEvent
from openfatture.payment.domain.enums import MatchType


@dataclass(frozen=True)
class PaymentEvent(BaseEvent):
    """Base class for payment domain events."""


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
