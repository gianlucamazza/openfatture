"""Tests for EventRepository query methods and filters."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import text

from openfatture.core.events import (
    ClientCreatedEvent,
    GlobalEventBus,
    InvoiceCreatedEvent,
    InvoiceDeletedEvent,
    InvoiceSentEvent,
    InvoiceValidatedEvent,
)
from openfatture.core.events.listeners import register_default_listeners
from openfatture.core.events.repository import EventRepository
from openfatture.storage.database.base import get_session, init_db


@pytest.fixture
def test_db(tmp_path):
    """Initialize test database with event system."""
    db_path = tmp_path / "test_repository.db"
    init_db(f"sqlite:///{db_path}")

    # Create event bus and register listeners
    event_bus = GlobalEventBus()
    register_default_listeners(event_bus)

    return event_bus


@pytest.fixture
def sample_events(test_db):
    """Create sample events for testing."""
    event_bus = test_db

    # Create diverse events with different timestamps
    now = datetime.now(UTC)

    # Invoice events (3 invoices)
    event_bus.publish(
        InvoiceCreatedEvent(
            invoice_id=1,
            invoice_number="001/2025",
            client_id=1,
            client_name="Client A",
            total_amount=Decimal("1000.00"),
        )
    )

    event_bus.publish(
        InvoiceValidatedEvent(
            invoice_id=1,
            invoice_number="001/2025",
            validation_status="passed",
            issues=[],
        )
    )

    event_bus.publish(
        InvoiceSentEvent(
            invoice_id=1,
            invoice_number="001/2025",
            recipient="ABCDEFG",
            pec_address="sdi01@pec.fatturapa.it",
            xml_path="/tmp/invoice001.xml",
        )
    )

    event_bus.publish(
        InvoiceCreatedEvent(
            invoice_id=2,
            invoice_number="002/2025",
            client_id=2,
            client_name="Client B",
            total_amount=Decimal("2000.00"),
        )
    )

    event_bus.publish(
        InvoiceDeletedEvent(
            invoice_id=3,
            invoice_number="003/2025",
            reason="Test deletion",
        )
    )

    # Client events
    event_bus.publish(
        ClientCreatedEvent(
            client_id=1,
            client_name="Client A",
            partita_iva="12345678901",
        )
    )

    event_bus.publish(
        ClientCreatedEvent(
            client_id=2,
            client_name="Client B",
            partita_iva="98765432109",
        )
    )

    return event_bus


def test_get_all_no_filters(sample_events):
    """Test get_all() without filters returns all events."""
    repo = EventRepository()
    try:
        events = repo.get_all(limit=100)

        # Should have all 7 events
        assert len(events) == 7

        # Should be ordered by most recent first
        for i in range(len(events) - 1):
            assert events[i].occurred_at >= events[i + 1].occurred_at

    finally:
        repo.close()


def test_get_all_filter_by_event_type(sample_events):
    """Test get_all() filtering by event_type."""
    repo = EventRepository()
    try:
        # Filter for InvoiceCreatedEvent only
        events = repo.get_all(event_type="InvoiceCreatedEvent", limit=100)

        assert len(events) == 2
        assert all(e.event_type == "InvoiceCreatedEvent" for e in events)

        # Filter for InvoiceSentEvent
        events = repo.get_all(event_type="InvoiceSentEvent", limit=100)
        assert len(events) == 1
        assert events[0].event_type == "InvoiceSentEvent"

    finally:
        repo.close()


def test_get_all_filter_by_entity_type(sample_events):
    """Test get_all() filtering by entity_type."""
    repo = EventRepository()
    try:
        # Filter for invoice entity type
        events = repo.get_all(entity_type="invoice", limit=100)

        assert len(events) == 5  # 3 for invoice 1, 1 for invoice 2, 1 deletion
        assert all(e.entity_type == "invoice" for e in events)

        # Filter for client entity type
        events = repo.get_all(entity_type="client", limit=100)
        assert len(events) == 2
        assert all(e.entity_type == "client" for e in events)

    finally:
        repo.close()


def test_get_all_filter_by_entity_id(sample_events):
    """Test get_all() filtering by entity_id."""
    repo = EventRepository()
    try:
        # Filter for invoice 1
        events = repo.get_all(entity_type="invoice", entity_id=1, limit=100)

        assert len(events) == 3  # Created, Validated, Sent
        assert all(e.entity_id == 1 for e in events)

        # Filter for invoice 2
        events = repo.get_all(entity_type="invoice", entity_id=2, limit=100)
        assert len(events) == 1  # Only Created
        assert events[0].entity_id == 2

    finally:
        repo.close()


def test_get_all_filter_by_date_range(sample_events):
    """Test get_all() filtering by date range."""
    repo = EventRepository()
    try:
        now = datetime.now(UTC)

        # Events from last hour
        start_date = now - timedelta(hours=1)
        events = repo.get_all(start_date=start_date, limit=100)

        # All events should be within the range
        assert len(events) == 7

        # Handle timezone comparison (SQLite returns naive datetime)
        start_date_naive = start_date.replace(tzinfo=None)
        for e in events:
            event_dt = e.occurred_at.replace(tzinfo=None) if e.occurred_at.tzinfo else e.occurred_at
            assert event_dt >= start_date_naive

        # Events from future (should be empty)
        future_date = now + timedelta(days=1)
        events = repo.get_all(start_date=future_date, limit=100)
        assert len(events) == 0

    finally:
        repo.close()


def test_get_all_combined_filters(sample_events):
    """Test get_all() with multiple filters combined."""
    repo = EventRepository()
    try:
        now = datetime.now(UTC)
        start_date = now - timedelta(hours=1)

        # Invoice events for entity 1 from last hour
        events = repo.get_all(
            entity_type="invoice",
            entity_id=1,
            start_date=start_date,
            limit=100,
        )

        assert len(events) == 3
        assert all(e.entity_type == "invoice" for e in events)
        assert all(e.entity_id == 1 for e in events)

        # Handle timezone comparison (SQLite returns naive datetime)
        start_date_naive = start_date.replace(tzinfo=None)
        for e in events:
            event_dt = e.occurred_at.replace(tzinfo=None) if e.occurred_at.tzinfo else e.occurred_at
            assert event_dt >= start_date_naive

    finally:
        repo.close()


def test_get_all_pagination(sample_events):
    """Test get_all() pagination with limit and offset."""
    repo = EventRepository()
    try:
        # Get first 3 events
        page1 = repo.get_all(limit=3, offset=0)
        assert len(page1) == 3

        # Get next 3 events
        page2 = repo.get_all(limit=3, offset=3)
        assert len(page2) == 3

        # Ensure no overlap
        page1_ids = {e.event_id for e in page1}
        page2_ids = {e.event_id for e in page2}
        assert page1_ids.isdisjoint(page2_ids)

        # Get last page (should have 1 event)
        page3 = repo.get_all(limit=3, offset=6)
        assert len(page3) == 1

    finally:
        repo.close()


def test_get_by_id(sample_events):
    """Test get_by_id() retrieves specific event."""
    repo = EventRepository()
    try:
        # Get first event
        all_events = repo.get_all(limit=1)
        assert len(all_events) == 1

        event_id = all_events[0].event_id

        # Retrieve by ID
        event = repo.get_by_id(event_id)

        assert event is not None
        assert event.event_id == event_id

        # Non-existent ID
        event = repo.get_by_id("non-existent-uuid")
        assert event is None

    finally:
        repo.close()


def test_get_by_event_type(sample_events):
    """Test get_by_event_type() method."""
    repo = EventRepository()
    try:
        events = repo.get_by_event_type("InvoiceCreatedEvent", limit=100)

        assert len(events) == 2
        assert all(e.event_type == "InvoiceCreatedEvent" for e in events)

    finally:
        repo.close()


def test_get_by_entity(sample_events):
    """Test get_by_entity() retrieves all events for entity."""
    repo = EventRepository()
    try:
        # Get all events for invoice 1
        events = repo.get_by_entity("invoice", 1, limit=100)

        assert len(events) == 3
        assert all(e.entity_type == "invoice" for e in events)
        assert all(e.entity_id == 1 for e in events)

        # Verify event types (Created, Validated, Sent)
        event_types = {e.event_type for e in events}
        assert "InvoiceCreatedEvent" in event_types
        assert "InvoiceValidatedEvent" in event_types
        assert "InvoiceSentEvent" in event_types

    finally:
        repo.close()


def test_get_timeline(sample_events):
    """Test get_timeline() returns simplified timeline view."""
    repo = EventRepository()
    try:
        timeline = repo.get_timeline("invoice", 1)

        assert len(timeline) == 3

        # Check structure
        for event in timeline:
            assert "timestamp" in event
            assert "event_type" in event
            assert "event_id" in event
            assert "summary" in event

            # Verify timestamp is datetime
            assert isinstance(event["timestamp"], datetime)

            # Verify summary is human-readable
            assert isinstance(event["summary"], str)
            assert len(event["summary"]) > 0

        # Timeline should be ordered by most recent first
        for i in range(len(timeline) - 1):
            assert timeline[i]["timestamp"] >= timeline[i + 1]["timestamp"]

    finally:
        repo.close()


def test_get_timeline_empty(sample_events):
    """Test get_timeline() with non-existent entity."""
    repo = EventRepository()
    try:
        timeline = repo.get_timeline("invoice", 999)

        assert timeline == []

    finally:
        repo.close()


def test_get_stats(sample_events):
    """Test get_stats() returns aggregated statistics."""
    repo = EventRepository()
    try:
        stats = repo.get_stats()

        # Check total events
        assert stats["total_events"] == 7

        # Check events by type
        assert "events_by_type" in stats
        assert stats["events_by_type"]["InvoiceCreatedEvent"] == 2
        assert stats["events_by_type"]["ClientCreatedEvent"] == 2

        # Check events by entity
        assert "events_by_entity" in stats
        assert stats["events_by_entity"]["invoice"] == 5
        assert stats["events_by_entity"]["client"] == 2

        # Check most recent event
        assert stats["most_recent_event"] is not None
        assert "event_type" in stats["most_recent_event"]
        assert "occurred_at" in stats["most_recent_event"]

        # Check oldest event
        assert stats["oldest_event"] is not None
        assert "event_type" in stats["oldest_event"]
        assert "occurred_at" in stats["oldest_event"]

    finally:
        repo.close()


def test_get_stats_with_date_range(sample_events):
    """Test get_stats() with date range filter."""
    repo = EventRepository()
    try:
        now = datetime.now(UTC)
        start_date = now - timedelta(hours=1)

        stats = repo.get_stats(start_date=start_date)

        # Should include all recent events
        assert stats["total_events"] == 7

        # Check date range in stats
        assert stats["date_range"]["start"] is not None

        # Future date range should return 0 events
        future_date = now + timedelta(days=1)
        stats = repo.get_stats(start_date=future_date)
        assert stats["total_events"] == 0

    finally:
        repo.close()


def test_count_no_filters(sample_events):
    """Test count() without filters."""
    repo = EventRepository()
    try:
        count = repo.count()

        assert count == 7

    finally:
        repo.close()


def test_count_with_event_type_filter(sample_events):
    """Test count() with event_type filter."""
    repo = EventRepository()
    try:
        count = repo.count(event_type="InvoiceCreatedEvent")

        assert count == 2

        count = repo.count(event_type="ClientCreatedEvent")
        assert count == 2

    finally:
        repo.close()


def test_count_with_entity_type_filter(sample_events):
    """Test count() with entity_type filter."""
    repo = EventRepository()
    try:
        count = repo.count(entity_type="invoice")

        assert count == 5

        count = repo.count(entity_type="client")
        assert count == 2

    finally:
        repo.close()


def test_count_with_date_range(sample_events):
    """Test count() with date range filter."""
    repo = EventRepository()
    try:
        now = datetime.now(UTC)
        start_date = now - timedelta(hours=1)

        count = repo.count(start_date=start_date)

        assert count == 7

        # Future date
        future_date = now + timedelta(days=1)
        count = repo.count(start_date=future_date)
        assert count == 0

    finally:
        repo.close()


def test_count_with_combined_filters(sample_events):
    """Test count() with multiple filters."""
    repo = EventRepository()
    try:
        now = datetime.now(UTC)
        start_date = now - timedelta(hours=1)

        count = repo.count(
            entity_type="invoice",
            start_date=start_date,
        )

        assert count == 5

    finally:
        repo.close()


def test_search_basic(sample_events):
    """Test search() finds events by content."""
    repo = EventRepository()
    try:
        # Search for client name
        events = repo.search("Client A", limit=100)

        # Should find InvoiceCreatedEvent and ClientCreatedEvent for Client A
        assert len(events) >= 1

        # Search for invoice number
        events = repo.search("001/2025", limit=100)

        # Should find all events for invoice 001
        assert len(events) >= 1

    finally:
        repo.close()


def test_search_case_insensitive(sample_events):
    """Test search() is case-insensitive."""
    repo = EventRepository()
    try:
        # Search with different cases
        events_lower = repo.search("client a", limit=100)
        events_upper = repo.search("CLIENT A", limit=100)
        events_mixed = repo.search("ClIeNt A", limit=100)

        # Should return same results
        assert len(events_lower) == len(events_upper)
        assert len(events_lower) == len(events_mixed)

    finally:
        repo.close()


def test_search_no_results(sample_events):
    """Test search() with no matching results."""
    repo = EventRepository()
    try:
        events = repo.search("NonExistentSearchTerm12345", limit=100)

        assert events == []

    finally:
        repo.close()


def test_search_limit(sample_events):
    """Test search() respects limit parameter."""
    repo = EventRepository()
    try:
        # Search with small limit
        events = repo.search("invoice", limit=2)

        assert len(events) <= 2

    finally:
        repo.close()


def test_repository_with_external_session():
    """Test EventRepository with external session."""
    db = get_session()
    try:
        repo = EventRepository(session=db)

        # Repository should use provided session
        assert repo._session is db
        assert not repo._owns_session

        # Test basic query
        events = repo.get_all(limit=10)
        assert isinstance(events, list)

        # Close should not close external session
        repo.close()

        # Session should still be usable
        db.execute(text("SELECT 1"))

    finally:
        db.close()


def test_create_event_summary_invoice_events():
    """Test _create_event_summary() for invoice events."""
    repo = EventRepository()

    # InvoiceCreatedEvent
    summary = repo._create_event_summary(
        "InvoiceCreatedEvent",
        {"invoice_number": "001/2025", "client_name": "Test Client"},
    )
    assert "001/2025" in summary
    assert "created" in summary.lower()

    # InvoiceValidatedEvent
    summary = repo._create_event_summary(
        "InvoiceValidatedEvent",
        {"validation_status": "passed"},
    )
    assert "passed" in summary
    assert "validation" in summary.lower()

    # InvoiceSentEvent
    summary = repo._create_event_summary(
        "InvoiceSentEvent",
        {"recipient": "ABCDEFG"},
    )
    assert "ABCDEFG" in summary
    assert "sent" in summary.lower()

    # InvoiceDeletedEvent
    summary = repo._create_event_summary(
        "InvoiceDeletedEvent",
        {"invoice_number": "002/2025"},
    )
    assert "002/2025" in summary
    assert "deleted" in summary.lower()


def test_create_event_summary_client_events():
    """Test _create_event_summary() for client events."""
    repo = EventRepository()

    # ClientCreatedEvent
    summary = repo._create_event_summary(
        "ClientCreatedEvent",
        {"client_name": "Test Client S.r.l."},
    )
    assert "Test Client S.r.l." in summary
    assert "created" in summary.lower()

    # ClientDeletedEvent
    summary = repo._create_event_summary(
        "ClientDeletedEvent",
        {"client_name": "Old Client"},
    )
    assert "Old Client" in summary
    assert "deleted" in summary.lower()


def test_create_event_summary_unknown_event():
    """Test _create_event_summary() for unknown event type."""
    repo = EventRepository()

    summary = repo._create_event_summary(
        "UnknownCustomEvent",
        {"some_data": "value"},
    )

    # Should return cleaned event type
    assert "UnknownCustom" in summary
