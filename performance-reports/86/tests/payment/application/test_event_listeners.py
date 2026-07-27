"""Tests for payment application event listeners."""

from decimal import Decimal
from uuid import uuid4

import pytest
from structlog.testing import capture_logs

from openfatture.payment.application.events import (
    InMemoryEventBus,
    TransactionMatchedEvent,
    TransactionUnmatchedEvent,
)
from openfatture.payment.application.listeners import (
    audit_log_listener,
    create_event_bus,
    register_default_payment_listeners,
)
from openfatture.payment.domain.enums import MatchType
from openfatture.utils.config import Settings


@pytest.fixture
def event_bus() -> InMemoryEventBus:
    return InMemoryEventBus()


def test_audit_log_listener_logs_matched_event(event_bus: InMemoryEventBus) -> None:
    """Audit listener should emit log entry when transaction matched event is published."""
    register_default_payment_listeners(event_bus)

    with capture_logs() as logs:
        event_bus.publish(
            TransactionMatchedEvent(
                transaction_id=uuid4(),
                payment_id=123,
                matched_amount=Decimal("100.00"),
                match_type=MatchType.EXACT,
                confidence=0.95,
            )
        )

    assert logs, "No audit log entries captured"
    record = logs[0]
    assert record["event"] == "payment_event"
    assert record["event_type"] == "TransactionMatchedEvent"
    assert record["payment_id"] == 123
    assert record["matched_amount"] == Decimal("100.00")


def test_audit_log_listener_handles_unmatched_event(event_bus: InMemoryEventBus) -> None:
    """Listener should also log unmatched events."""
    event_bus.subscribe(TransactionUnmatchedEvent, audit_log_listener)

    with capture_logs() as logs:
        event_bus.publish(
            TransactionUnmatchedEvent(
                transaction_id=uuid4(),
                payment_id=456,
                reverted_amount=Decimal("50.00"),
            )
        )

    assert logs
    record = logs[0]
    assert record["event_type"] == "TransactionUnmatchedEvent"
    assert record["reverted_amount"] == Decimal("50.00")


def test_register_default_payment_listeners_is_idempotent(
    event_bus: InMemoryEventBus,
) -> None:
    """Registering default listeners multiple times should not raise errors."""
    register_default_payment_listeners(event_bus)
    register_default_payment_listeners(event_bus)

    with capture_logs() as logs:
        event_bus.publish(
            TransactionMatchedEvent(
                transaction_id=uuid4(),
                payment_id=999,
                matched_amount=Decimal("1.00"),
                match_type=MatchType.MANUAL,
                confidence=None,
            )
        )

    assert len(logs) == 1


def test_create_event_bus_with_custom_listener(monkeypatch) -> None:
    """create_event_bus attaches custom listeners defined in settings."""
    from tests.payment.application.fake_listeners import captured_events

    captured_events.clear()
    settings = Settings(
        payment_event_listeners="tests.payment.application.fake_listeners.custom_listener"
    )

    bus = create_event_bus(settings)
    event = TransactionMatchedEvent(
        transaction_id=uuid4(),
        payment_id=42,
        matched_amount=Decimal("20.00"),
        match_type=MatchType.MANUAL,
        confidence=None,
    )

    bus.publish(event)

    assert captured_events and captured_events[0] == event
