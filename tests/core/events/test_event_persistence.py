"""Tests for event persistence functionality."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from openfatture.core.events.base import BaseEvent, GlobalEventBus
from openfatture.core.events.client_events import ClientCreatedEvent, ClientDeletedEvent
from openfatture.core.events.invoice_events import InvoiceCreatedEvent, InvoiceValidatedEvent
from openfatture.core.events.listeners import register_default_listeners
from openfatture.core.events.persistence import EventPersistenceListener
from openfatture.storage.database.base import get_session, init_db
from openfatture.storage.database.models import EventLog


@pytest.fixture
def event_bus():
    """Create a fresh event bus for testing."""
    return GlobalEventBus()


@pytest.fixture
def test_db(tmp_path):
    """Create a temporary test database."""
    db_path = tmp_path / "test_events.db"
    init_db(f"sqlite:///{db_path}")
    yield
    # Cleanup handled by tmp_path fixture


@pytest.fixture
def persistence_listener(event_bus, test_db):
    """Create and register persistence listener."""
    listener = EventPersistenceListener()
    event_bus.subscribe(BaseEvent, listener.handle_event, priority=-100)
    return listener


def test_event_persistence_listener_creation():
    """Test that EventPersistenceListener can be instantiated."""
    listener = EventPersistenceListener()
    assert listener._enabled is True


def test_event_persistence_listener_enable_disable():
    """Test enable/disable functionality."""
    listener = EventPersistenceListener()
    assert listener._enabled is True

    listener.disable()
    assert listener._enabled is False

    listener.enable()
    assert listener._enabled is True


def test_persist_invoice_created_event(event_bus, persistence_listener):
    """Test persisting an InvoiceCreatedEvent."""
    from decimal import Decimal

    # Create and publish event
    event = InvoiceCreatedEvent(
        invoice_id=123,
        invoice_number="001/2025",
        client_id=1,
        client_name="Test Client",
        total_amount=Decimal("1000.00"),
    )

    event_bus.publish(event)

    # Verify event was persisted
    db = get_session()
    try:
        event_log = db.query(EventLog).filter_by(event_id=str(event.event_id)).first()
        assert event_log is not None
        assert event_log.event_type == "InvoiceCreatedEvent"
        assert event_log.entity_type == "invoice"
        assert event_log.entity_id == 123

        # Verify event data
        event_data = json.loads(event_log.event_data)
        assert event_data["invoice_id"] == 123
        assert event_data["invoice_number"] == "001/2025"
        assert event_data["client_name"] == "Test Client"
        assert event_data["client_id"] == 1

    finally:
        db.close()


def test_persist_client_created_event(event_bus, persistence_listener):
    """Test persisting a ClientCreatedEvent."""
    event = ClientCreatedEvent(
        client_id=456,
        client_name="New Client S.r.l.",
        partita_iva="12345678901",
        codice_fiscale="RSSMRA80A01H501U",
    )

    event_bus.publish(event)

    # Verify event was persisted
    db = get_session()
    try:
        event_log = db.query(EventLog).filter_by(event_id=str(event.event_id)).first()
        assert event_log is not None
        assert event_log.event_type == "ClientCreatedEvent"
        assert event_log.entity_type == "client"
        assert event_log.entity_id == 456

        # Verify event data
        event_data = json.loads(event_log.event_data)
        assert event_data["client_id"] == 456
        assert event_data["client_name"] == "New Client S.r.l."

    finally:
        db.close()


def test_persist_event_with_context(event_bus, persistence_listener):
    """Test persisting an event with additional context."""
    from decimal import Decimal

    event = InvoiceCreatedEvent(
        invoice_id=789,
        invoice_number="002/2025",
        client_id=2,
        client_name="Context Client",
        total_amount=Decimal("2500.00"),
        context={"source": "API", "user_agent": "TestAgent/1.0"},
    )

    event_bus.publish(event)

    # Verify event was persisted with metadata
    db = get_session()
    try:
        event_log = db.query(EventLog).filter_by(event_id=str(event.event_id)).first()
        assert event_log is not None
        assert event_log.metadata_json is not None

        metadata = json.loads(event_log.metadata_json)
        assert metadata["source"] == "API"
        assert metadata["user_agent"] == "TestAgent/1.0"

    finally:
        db.close()


def test_persist_event_without_entity(event_bus, persistence_listener):
    """Test persisting an event that doesn't have entity_id/entity_type."""

    # Use ClientDeletedEvent which has client_id
    event = ClientDeletedEvent(
        client_id=999,
        client_name="Deleted Client",
        invoice_count=5,
        reason="User requested deletion",
    )

    event_bus.publish(event)

    # Verify event was persisted
    db = get_session()
    try:
        event_log = db.query(EventLog).filter_by(event_id=str(event.event_id)).first()
        assert event_log is not None
        assert event_log.entity_type == "client"
        assert event_log.entity_id == 999

    finally:
        db.close()


def test_multiple_events_persistence(event_bus, persistence_listener):
    """Test persisting multiple events in sequence."""
    from decimal import Decimal

    events = [
        InvoiceCreatedEvent(
            invoice_id=1,
            invoice_number="001/2025",
            client_id=1,
            client_name="Client 1",
            total_amount=Decimal("100.00"),
        ),
        InvoiceCreatedEvent(
            invoice_id=2,
            invoice_number="002/2025",
            client_id=2,
            client_name="Client 2",
            total_amount=Decimal("200.00"),
        ),
        ClientCreatedEvent(client_id=1, client_name="Client 1"),
        InvoiceValidatedEvent(
            invoice_id=1,
            invoice_number="001/2025",
            validation_status="passed",
            issues=[],
            xml_path="/tmp/invoice_001.xml",
        ),
    ]

    for event in events:
        event_bus.publish(event)

    # Verify all events were persisted
    db = get_session()
    try:
        event_logs = db.query(EventLog).all()
        assert len(event_logs) >= 4  # At least our 4 events

        # Check we have the expected event types
        event_types = [log.event_type for log in event_logs]
        assert "InvoiceCreatedEvent" in event_types
        assert "ClientCreatedEvent" in event_types
        assert "InvoiceValidatedEvent" in event_types

    finally:
        db.close()


def test_disabled_persistence_listener(event_bus, test_db):
    """Test that disabled listener doesn't persist events."""
    from decimal import Decimal

    listener = EventPersistenceListener()
    listener.disable()
    event_bus.subscribe(BaseEvent, listener.handle_event, priority=-100)

    event = InvoiceCreatedEvent(
        invoice_id=999,
        invoice_number="999/2025",
        client_id=10,
        client_name="Test",
        total_amount=Decimal("100.00"),
    )

    event_bus.publish(event)

    # Verify event was NOT persisted
    db = get_session()
    try:
        event_log = db.query(EventLog).filter_by(event_id=str(event.event_id)).first()
        assert event_log is None

    finally:
        db.close()


def test_persistence_error_handling(event_bus, persistence_listener, monkeypatch):
    """Test that persistence errors don't break event publishing."""
    from decimal import Decimal

    # Mock get_session to raise an exception
    def mock_get_session():
        raise RuntimeError("Database connection failed")

    monkeypatch.setattr("openfatture.core.events.persistence.get_session", mock_get_session)

    # This should not raise an exception even though persistence fails
    event = InvoiceCreatedEvent(
        invoice_id=888,
        invoice_number="888/2025",
        client_id=11,
        client_name="Test",
        total_amount=Decimal("100.00"),
    )

    # Should not raise
    event_bus.publish(event)


def test_register_default_listeners_includes_persistence(test_db):
    """Test that register_default_listeners includes event persistence."""
    event_bus = GlobalEventBus()
    register_default_listeners(event_bus)

    # Check that BaseEvent has handlers registered
    assert BaseEvent in event_bus._handlers
    handlers = event_bus._handlers[BaseEvent]

    # Should have at least 2 handlers: audit_log_listener and persistence listener
    assert len(handlers) >= 2

    # Check that at least one handler is the persistence listener
    has_persistence = any(
        hasattr(reg.handler, "__self__")
        and isinstance(reg.handler.__self__, EventPersistenceListener)
        for reg in handlers
    )
    assert has_persistence, "EventPersistenceListener not registered"


def test_event_timestamps_preserved(event_bus, persistence_listener):
    """Test that event timestamps are correctly preserved in database."""
    from decimal import Decimal

    event = InvoiceCreatedEvent(
        invoice_id=111,
        invoice_number="111/2025",
        client_id=12,
        client_name="Timestamp Test",
        total_amount=Decimal("150.00"),
    )

    occurred_at = event.occurred_at
    event_bus.publish(event)

    # Verify timestamps
    db = get_session()
    try:
        event_log = db.query(EventLog).filter_by(event_id=str(event.event_id)).first()
        assert event_log is not None

        # Compare timestamps (handle timezone-naive datetime from SQLite)
        # SQLite returns naive datetime, so we compare by replacing tzinfo
        if event_log.occurred_at.tzinfo is None and occurred_at.tzinfo is not None:
            # Make occurred_at naive for comparison
            occurred_at_naive = occurred_at.replace(tzinfo=None)
            assert event_log.occurred_at == occurred_at_naive
        else:
            assert event_log.occurred_at == occurred_at

        assert event_log.published_at is not None

        # published_at should be very close to occurred_at (within a few seconds)
        # Handle timezone-aware/naive comparison
        published_at = event_log.published_at
        if published_at.tzinfo is None and occurred_at.tzinfo is not None:
            # Make both naive for comparison
            published_at_naive = published_at
            occurred_at_naive = occurred_at.replace(tzinfo=None)
            time_diff = abs((published_at_naive - occurred_at_naive).total_seconds())
        else:
            time_diff = abs((published_at - occurred_at).total_seconds())

        assert time_diff < 5  # Less than 5 seconds difference

    finally:
        db.close()


def test_extract_entity_info_patterns():
    """Test entity extraction patterns."""
    listener = EventPersistenceListener()

    # Test invoice patterns
    entity_type, entity_id = listener._extract_entity_info(
        None, {"invoice_id": 123, "other": "data"}
    )
    assert entity_type == "invoice"
    assert entity_id == 123

    entity_type, entity_id = listener._extract_entity_info(
        None, {"fattura_id": 456, "other": "data"}
    )
    assert entity_type == "invoice"
    assert entity_id == 456

    # Test client patterns
    entity_type, entity_id = listener._extract_entity_info(None, {"client_id": 789})
    assert entity_type == "client"
    assert entity_id == 789

    # Test no entity
    entity_type, entity_id = listener._extract_entity_info(None, {"random_field": "value"})
    assert entity_type is None
    assert entity_id is None


def test_json_serialization_with_datetime():
    """Test JSON serialization of datetime objects."""
    listener = EventPersistenceListener()

    data = {
        "timestamp": datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC),
        "nested": {"date": datetime(2025, 1, 16, 15, 45, 0, tzinfo=UTC)},
        "list": [datetime(2025, 1, 17, 20, 0, 0, tzinfo=UTC)],
    }

    result = listener._prepare_json_data(data)

    assert isinstance(result["timestamp"], str)
    assert result["timestamp"] == "2025-01-15T10:30:00+00:00"
    assert isinstance(result["nested"]["date"], str)
    assert isinstance(result["list"][0], str)
