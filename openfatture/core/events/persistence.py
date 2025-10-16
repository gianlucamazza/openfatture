"""Event persistence listener for audit trail and analytics.

This module provides automatic persistence of all domain events to the database
for compliance, debugging, and analytics purposes.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from typing import Any

from ...storage.database.base import get_session
from ...storage.database.models import EventLog
from .base import BaseEvent

logger = logging.getLogger(__name__)


class EventPersistenceListener:
    """Listens to all domain events and persists them to the database.

    This listener runs with low priority (-100) to ensure it doesn't impact
    the performance of critical event handlers. Failed persistence attempts
    are logged but don't propagate exceptions to avoid breaking the event bus.
    """

    def __init__(self) -> None:
        """Initialize the persistence listener."""
        self._enabled = True

    def handle_event(self, event: BaseEvent) -> None:
        """Persist an event to the database.

        Args:
            event: The domain event to persist

        Note:
            This method catches and logs all exceptions to prevent
            persistence failures from breaking the event bus.
        """
        if not self._enabled:
            return

        try:
            # Serialize event to dict
            event_dict = asdict(event)

            # Extract entity information from event
            entity_type, entity_id = self._extract_entity_info(event, event_dict)

            # Convert datetime objects to ISO format strings for JSON serialization
            event_data = self._prepare_json_data(event_dict)

            # Create EventLog record
            db = get_session()
            try:
                event_log = EventLog(
                    event_id=str(event.event_id),
                    event_type=event.__class__.__name__,
                    event_data=json.dumps(event_data),
                    occurred_at=event.occurred_at,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    metadata_json=json.dumps(event.context) if event.context else None,
                )

                db.add(event_log)
                db.commit()

                logger.debug(
                    f"Persisted event {event.__class__.__name__} "
                    f"(id={event.event_id}, entity={entity_type}:{entity_id})"
                )

            finally:
                db.close()

        except Exception as e:
            logger.error(
                f"Failed to persist event {event.__class__.__name__}: {e}",
                exc_info=True,
            )

    def _extract_entity_info(
        self, event: BaseEvent, event_dict: dict[str, Any]
    ) -> tuple[str | None, int | None]:
        """Extract entity type and ID from event attributes.

        Looks for common patterns in event attributes:
        - invoice_id, fattura_id → invoice
        - client_id, cliente_id → client
        - payment_id, pagamento_id → payment
        - batch_id → batch
        - etc.

        Args:
            event: The domain event
            event_dict: Serialized event dictionary

        Returns:
            Tuple of (entity_type, entity_id) or (None, None) if not found
        """
        # Common entity field patterns (field_name → entity_type)
        entity_mappings = {
            "invoice_id": "invoice",
            "fattura_id": "invoice",
            "client_id": "client",
            "cliente_id": "client",
            "payment_id": "payment",
            "pagamento_id": "payment",
            "product_id": "product",
            "prodotto_id": "product",
            "batch_id": "batch",
            "notification_id": "notification",
            "quote_id": "quote",
            "preventivo_id": "quote",
        }

        for field_name, entity_type in entity_mappings.items():
            if field_name in event_dict:
                entity_id = event_dict[field_name]
                if isinstance(entity_id, int):
                    return entity_type, entity_id

        return None, None

    def _prepare_json_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Prepare event data for JSON serialization.

        Converts datetime objects to ISO format strings and handles
        other non-JSON-serializable types.

        Args:
            data: Event dictionary

        Returns:
            JSON-serializable dictionary
        """
        result: dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, Decimal):
                result[key] = float(value)
            elif isinstance(value, dict):
                result[key] = self._prepare_json_data(value)
            elif isinstance(value, (list, tuple)):
                result[key] = [
                    (
                        self._prepare_json_data(item)
                        if isinstance(item, dict)
                        else (
                            item.isoformat()
                            if isinstance(item, datetime)
                            else float(item) if isinstance(item, Decimal) else item
                        )
                    )
                    for item in value
                ]
            else:
                # For other types, try to convert to string as fallback
                try:
                    json.dumps(value)  # Test if serializable
                    result[key] = value
                except (TypeError, ValueError):
                    result[key] = str(value)

        return result

    def disable(self) -> None:
        """Disable event persistence (useful for testing)."""
        self._enabled = False

    def enable(self) -> None:
        """Enable event persistence."""
        self._enabled = True
