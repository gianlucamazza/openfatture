"""Payment events are global domain events."""

from decimal import Decimal
from uuid import uuid4

from openfatture.events import GlobalEventBus
from openfatture.events.base import BaseEvent
from openfatture.events.listeners import audit_log_listener
from openfatture.payment.application.events import (
    PaymentEvent,
    TransactionMatchedEvent,
    TransactionUnmatchedEvent,
)
from openfatture.payment.domain.enums import MatchType


def _matched(payment_id: int = 123) -> TransactionMatchedEvent:
    return TransactionMatchedEvent(
        transaction_id=uuid4(),
        payment_id=payment_id,
        matched_amount=Decimal("100.00"),
        match_type=MatchType.EXACT,
        confidence=0.95,
    )


def test_payment_events_carry_global_event_metadata() -> None:
    event = _matched()

    assert isinstance(event, BaseEvent)
    assert event.event_id
    assert event.occurred_at.tzinfo is not None


def test_global_listeners_receive_payment_events() -> None:
    bus = GlobalEventBus()
    received: list[BaseEvent] = []
    bus.subscribe(BaseEvent, received.append)
    bus.subscribe(BaseEvent, audit_log_listener)

    bus.publish(_matched())
    bus.publish(
        TransactionUnmatchedEvent(
            transaction_id=uuid4(), payment_id=456, reverted_amount=Decimal("50.00")
        )
    )

    assert [type(event).__name__ for event in received] == [
        "TransactionMatchedEvent",
        "TransactionUnmatchedEvent",
    ]


def test_payment_listeners_subscribe_by_payment_event_type() -> None:
    bus = GlobalEventBus()
    received: list[PaymentEvent] = []
    bus.subscribe(PaymentEvent, received.append)

    event = _matched()
    bus.publish(event)

    assert received == [event]
