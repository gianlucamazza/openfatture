"""Event repository for querying persisted events."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from ...storage.database.base import get_session
from ...storage.database.models import EventLog


class EventRepository:
    """Repository for querying event audit logs.

    Provides high-level query methods for retrieving and analyzing
    persisted domain events.
    """

    def __init__(self, session: Session | None = None):
        """Initialize repository.

        Args:
            session: Database session. If None, creates new session per query.
        """
        self._session = session
        self._owns_session = session is None

    def _get_session(self) -> Session:
        """Get database session."""
        if self._session is not None:
            return self._session
        return get_session()

    def get_all(
        self,
        event_type: str | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[EventLog]:
        """Get all events with optional filtering.

        Args:
            event_type: Filter by event type (e.g., "InvoiceCreatedEvent")
            entity_type: Filter by entity type (e.g., "invoice")
            entity_id: Filter by entity ID
            start_date: Filter events after this date
            end_date: Filter events before this date
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of EventLog records
        """
        db = self._get_session()
        query = db.query(EventLog)

        # Apply filters
        if event_type:
            query = query.filter(EventLog.event_type == event_type)
        if entity_type:
            query = query.filter(EventLog.entity_type == entity_type)
        if entity_id is not None:
            query = query.filter(EventLog.entity_id == entity_id)
        if start_date:
            query = query.filter(EventLog.occurred_at >= start_date)
        if end_date:
            query = query.filter(EventLog.occurred_at <= end_date)

        # Order by most recent first
        query = query.order_by(EventLog.occurred_at.desc())

        # Apply pagination
        query = query.limit(limit).offset(offset)

        results = query.all()

        if self._owns_session:
            db.close()

        return results

    def get_by_id(self, event_id: str) -> EventLog | None:
        """Get event by UUID.

        Args:
            event_id: Event UUID (as string)

        Returns:
            EventLog record or None if not found
        """
        db = self._get_session()
        result = db.query(EventLog).filter(EventLog.event_id == event_id).first()

        if self._owns_session:
            db.close()

        return result

    def get_by_event_type(self, event_type: str, limit: int = 100) -> list[EventLog]:
        """Get all events of a specific type.

        Args:
            event_type: Event type name (e.g., "InvoiceCreatedEvent")
            limit: Maximum number of results

        Returns:
            List of EventLog records
        """
        return self.get_all(event_type=event_type, limit=limit)

    def get_by_entity(self, entity_type: str, entity_id: int, limit: int = 100) -> list[EventLog]:
        """Get all events for a specific entity.

        Args:
            entity_type: Entity type (e.g., "invoice", "client")
            entity_id: Entity database ID
            limit: Maximum number of results

        Returns:
            List of EventLog records ordered by occurrence time
        """
        return self.get_all(entity_type=entity_type, entity_id=entity_id, limit=limit)

    def get_timeline(self, entity_type: str, entity_id: int) -> list[dict[str, Any]]:
        """Get event timeline for an entity.

        Returns a simplified timeline view with key event information.

        Args:
            entity_type: Entity type (e.g., "invoice", "client")
            entity_id: Entity database ID

        Returns:
            List of event dictionaries with timestamp, type, and summary
        """
        events = self.get_by_entity(entity_type, entity_id, limit=1000)
        timeline = []

        for event in events:
            event_data = json.loads(event.event_data)
            timeline.append(
                {
                    "timestamp": event.occurred_at,
                    "event_type": event.event_type,
                    "event_id": event.event_id,
                    "summary": self._create_event_summary(event.event_type, event_data),
                }
            )

        return timeline

    def get_stats(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Get event statistics.

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Dictionary with statistics
        """
        db = self._get_session()
        query = db.query(EventLog)

        # Apply date filters
        if start_date:
            query = query.filter(EventLog.occurred_at >= start_date)
        if end_date:
            query = query.filter(EventLog.occurred_at <= end_date)

        # Total events
        total_events = query.count()

        # Events by type
        events_by_type = (
            query.with_entities(EventLog.event_type, func.count(EventLog.id))
            .group_by(EventLog.event_type)
            .all()
        )

        # Events by entity type
        events_by_entity = (
            query.filter(EventLog.entity_type.isnot(None))
            .with_entities(EventLog.entity_type, func.count(EventLog.id))
            .group_by(EventLog.entity_type)
            .all()
        )

        # Most recent event
        most_recent = query.order_by(EventLog.occurred_at.desc()).first()

        # Oldest event
        oldest = query.order_by(EventLog.occurred_at.asc()).first()

        if self._owns_session:
            db.close()

        # Convert Row objects to tuples for dict()
        events_by_type_list = [(row[0], row[1]) for row in events_by_type]
        events_by_entity_list = [(row[0], row[1]) for row in events_by_entity]

        return {
            "total_events": total_events,
            "events_by_type": dict(events_by_type_list),
            "events_by_entity": dict(events_by_entity_list),
            "most_recent_event": (
                {
                    "event_type": most_recent.event_type,
                    "occurred_at": most_recent.occurred_at,
                }
                if most_recent
                else None
            ),
            "oldest_event": (
                {
                    "event_type": oldest.event_type,
                    "occurred_at": oldest.occurred_at,
                }
                if oldest
                else None
            ),
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
        }

    def count(
        self,
        event_type: str | None = None,
        entity_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> int:
        """Count events with optional filtering.

        Args:
            event_type: Filter by event type
            entity_type: Filter by entity type
            start_date: Filter events after this date
            end_date: Filter events before this date

        Returns:
            Number of matching events
        """
        db = self._get_session()
        query = db.query(EventLog)

        # Apply filters
        if event_type:
            query = query.filter(EventLog.event_type == event_type)
        if entity_type:
            query = query.filter(EventLog.entity_type == entity_type)
        if start_date:
            query = query.filter(EventLog.occurred_at >= start_date)
        if end_date:
            query = query.filter(EventLog.occurred_at <= end_date)

        count = query.count()

        if self._owns_session:
            db.close()

        return count

    def _create_event_summary(self, event_type: str, event_data: dict[str, Any]) -> str:
        """Create human-readable event summary.

        Args:
            event_type: Event type name
            event_data: Event payload

        Returns:
            Human-readable summary string
        """
        # Create summaries based on event type
        if "InvoiceCreated" in event_type:
            return f"Invoice {event_data.get('invoice_number', 'N/A')} created"
        elif "InvoiceValidated" in event_type:
            status = event_data.get("validation_status", "unknown")
            return f"Invoice validation: {status}"
        elif "InvoiceSent" in event_type:
            return f"Invoice sent via PEC to {event_data.get('recipient', 'N/A')}"
        elif "InvoiceDeleted" in event_type:
            return f"Invoice {event_data.get('invoice_number', 'N/A')} deleted"
        elif "ClientCreated" in event_type:
            return f"Client '{event_data.get('client_name', 'N/A')}' created"
        elif "ClientDeleted" in event_type:
            return f"Client '{event_data.get('client_name', 'N/A')}' deleted"
        elif "BatchImport" in event_type:
            count = event_data.get("records_processed", 0)
            return f"Batch import: {count} records"
        elif "AICommand" in event_type:
            command = event_data.get("command", "N/A")
            return f"AI command: {command}"
        elif "SDINotification" in event_type:
            notification_type = event_data.get("notification_type", "N/A")
            return f"SDI notification: {notification_type}"
        else:
            return event_type.replace("Event", "")

    def search(self, query: str, limit: int = 100) -> list[EventLog]:
        """Search events by text in event_data.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching EventLog records
        """
        db = self._get_session()

        # SQLite full-text search using LIKE
        results = (
            db.query(EventLog)
            .filter(EventLog.event_data.like(f"%{query}%"))
            .order_by(EventLog.occurred_at.desc())
            .limit(limit)
            .all()
        )

        if self._owns_session:
            db.close()

        return results

    def close(self) -> None:
        """Close database session if owned by repository."""
        if self._owns_session and self._session is not None:
            self._session.close()
