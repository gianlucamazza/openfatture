"""Events service adapter for Streamlit web interface.

Provides simplified API for event tracking and audit trails.
"""

from datetime import datetime, timedelta
from typing import Any

import streamlit as st

from openfatture.storage.database.models import EventLog
from openfatture.utils.config import Settings, get_settings
from openfatture.web.utils.cache import get_db_session


class StreamlitEventsService:
    """Adapter service for events management in Streamlit."""

    def __init__(self) -> None:
        """Initialize service with settings."""
        self.settings: Settings = get_settings()

    @st.cache_data(ttl=30, show_spinner=False)  # 30 seconds cache for events
    def get_recent_events(self, limit: int = 50) -> list[dict[str, Any]]:
        """
        Get recent events from the audit trail.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries
        """
        db = get_db_session()

        try:
            events = db.query(EventLog).order_by(EventLog.created_at.desc()).limit(limit).all()

            event_list = []
            for event in events:
                event_dict = {
                    "id": event.id,
                    "event_type": event.event_type,
                    "entity_type": event.entity_type,
                    "entity_id": event.entity_id,
                    "user_id": event.user_id,
                    "timestamp": event.created_at,
                    "description": self._format_event_description(event),
                    "metadata": event.metadata or {},
                    "ip_address": event.ip_address,
                    "user_agent": event.user_agent,
                }
                event_list.append(event_dict)

            return event_list

        finally:
            db.close()

    @st.cache_data(ttl=60, show_spinner=False)  # 1 minute cache for filtered events
    def get_events_filtered(
        self,
        event_type: str | None = None,
        entity_type: str | None = None,
        days: int = 7,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Get filtered events from the audit trail.

        Args:
            event_type: Filter by event type
            entity_type: Filter by entity type
            days: Number of days to look back
            limit: Maximum number of events to return

        Returns:
            List of filtered event dictionaries
        """
        db = get_db_session()

        try:
            # Build query
            query = db.query(EventLog)

            # Date filter
            since_date = datetime.now() - timedelta(days=days)
            query = query.filter(EventLog.created_at >= since_date)

            # Type filters
            if event_type:
                query = query.filter(EventLog.event_type == event_type)
            if entity_type:
                query = query.filter(EventLog.entity_type == entity_type)

            # Execute query
            events = query.order_by(EventLog.created_at.desc()).limit(limit).all()

            event_list = []
            for event in events:
                event_dict = {
                    "id": event.id,
                    "event_type": event.event_type,
                    "entity_type": event.entity_type,
                    "entity_id": event.entity_id,
                    "user_id": event.user_id,
                    "timestamp": event.created_at,
                    "description": self._format_event_description(event),
                    "metadata": event.metadata or {},
                    "ip_address": event.ip_address,
                    "user_agent": event.user_agent,
                }
                event_list.append(event_dict)

            return event_list

        finally:
            db.close()

    def search_events(self, search_term: str, limit: int = 50) -> list[dict[str, Any]]:
        """
        Search events by description or metadata.

        Args:
            search_term: Term to search for
            limit: Maximum number of results

        Returns:
            List of matching events
        """
        db = get_db_session()

        try:
            # Simple text search in event types and descriptions
            # Note: This is a basic implementation. A full-text search would be better
            events = (
                db.query(EventLog)
                .filter(
                    (EventLog.event_type.contains(search_term))
                    | (EventLog.entity_type.contains(search_term))
                )
                .order_by(EventLog.created_at.desc())
                .limit(limit)
                .all()
            )

            event_list = []
            for event in events:
                event_dict = {
                    "id": event.id,
                    "event_type": event.event_type,
                    "entity_type": event.entity_type,
                    "entity_id": event.entity_id,
                    "user_id": event.user_id,
                    "timestamp": event.created_at,
                    "description": self._format_event_description(event),
                    "metadata": event.metadata or {},
                    "ip_address": event.ip_address,
                    "user_agent": event.user_agent,
                }
                event_list.append(event_dict)

            return event_list

        finally:
            db.close()

    def get_event_statistics(self, days: int = 30) -> dict[str, Any]:
        """
        Get event statistics for dashboard.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with event statistics
        """
        db = get_db_session()

        try:
            since_date = datetime.now() - timedelta(days=days)

            # Total events
            total_events = db.query(EventLog).filter(EventLog.created_at >= since_date).count()

            # Events by type
            event_types = (
                db.query(EventLog.event_type, db.func.count(EventLog.id).label("count"))
                .filter(EventLog.created_at >= since_date)
                .group_by(EventLog.event_type)
                .all()
            )

            # Events by entity type
            entity_types = (
                db.query(EventLog.entity_type, db.func.count(EventLog.id).label("count"))
                .filter(EventLog.created_at >= since_date)
                .group_by(EventLog.entity_type)
                .all()
            )

            # Daily activity (last 7 days)
            daily_stats = []
            for i in range(7):
                day = datetime.now() - timedelta(days=i)
                day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)

                day_count = (
                    db.query(EventLog)
                    .filter(EventLog.created_at >= day_start, EventLog.created_at <= day_end)
                    .count()
                )

                daily_stats.append({"date": day.date(), "count": day_count})

            return {
                "total_events": total_events,
                "period_days": days,
                "event_types": dict(event_types),
                "entity_types": dict(entity_types),
                "daily_activity": daily_stats,
                "avg_daily_events": total_events / days if days > 0 else 0,
            }

        finally:
            db.close()

    def get_entity_timeline(
        self, entity_type: str, entity_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        Get timeline of events for a specific entity.

        Args:
            entity_type: Type of entity (e.g., 'fattura', 'cliente')
            entity_id: ID of the entity
            limit: Maximum number of events

        Returns:
            List of events for the entity
        """
        db = get_db_session()

        try:
            events = (
                db.query(EventLog)
                .filter(EventLog.entity_type == entity_type, EventLog.entity_id == entity_id)
                .order_by(EventLog.created_at.desc())
                .limit(limit)
                .all()
            )

            event_list = []
            for event in events:
                event_dict = {
                    "id": event.id,
                    "event_type": event.event_type,
                    "timestamp": event.created_at,
                    "description": self._format_event_description(event),
                    "metadata": event.metadata or {},
                    "user_id": event.user_id,
                }
                event_list.append(event_dict)

            return event_list

        finally:
            db.close()

    def get_available_event_types(self) -> list[str]:
        """
        Get list of available event types.

        Returns:
            List of unique event types
        """
        db = get_db_session()

        try:
            event_types = db.query(EventLog.event_type).distinct().all()
            return sorted([et[0] for et in event_types])

        finally:
            db.close()

    def get_available_entity_types(self) -> list[str]:
        """
        Get list of available entity types.

        Returns:
            List of unique entity types
        """
        db = get_db_session()

        try:
            entity_types = db.query(EventLog.entity_type).distinct().all()
            return sorted([et[0] for et in entity_types if et[0]])

        finally:
            db.close()

    def _format_event_description(self, event: EventLog) -> str:
        """
        Format a human-readable description for an event.

        Args:
            event: EventLog instance

        Returns:
            Human-readable description
        """
        event_type = event.event_type
        entity_type = event.entity_type or "sistema"
        entity_id = event.entity_id or "N/A"

        # Basic descriptions based on event type
        descriptions = {
            "invoice_created": f"Fattura {entity_id} creata",
            "invoice_updated": f"Fattura {entity_id} modificata",
            "invoice_sent": f"Fattura {entity_id} inviata a SDI",
            "invoice_paid": f"Fattura {entity_id} pagata",
            "client_created": f"Cliente {entity_id} creato",
            "client_updated": f"Cliente {entity_id} aggiornato",
            "payment_reconciled": f"Pagamento riconciliato per {entity_type} {entity_id}",
            "user_login": f"Accesso utente {event.user_id or 'sistema'}",
            "system_backup": "Backup sistema eseguito",
            "config_changed": "Configurazione modificata",
        }

        return descriptions.get(event_type, f"Evento {event_type} su {entity_type} {entity_id}")
