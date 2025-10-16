"""Change Tracking System for RAG Auto-Update.

Tracks changes to entities (invoices, clients) for automatic reindexing.
Uses in-memory tracking with optional persistence.

Example:
    >>> from openfatture.ai.rag.auto_update import ChangeTracker
    >>> tracker = ChangeTracker()
    >>>
    >>> # Track change
    >>> tracker.track_change("invoice", 123, "update")
    >>>
    >>> # Get pending changes
    >>> changes = tracker.get_pending_changes()
"""

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from openfatture.ai.rag.auto_update.config import get_auto_update_config
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class ChangeType(str, Enum):
    """Type of change operation."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


@dataclass
class EntityChange:
    """Represents a change to an entity.

    Attributes:
        entity_type: Type of entity (invoice, client, product)
        entity_id: Entity ID
        change_type: Type of change (create, update, delete)
        timestamp: When the change occurred
        metadata: Optional metadata about the change
    """

    entity_type: str
    entity_id: int
    change_type: ChangeType
    timestamp: datetime
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "change_type": self.change_type.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata or {},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EntityChange":
        """Create from dictionary."""
        return cls(
            entity_type=data["entity_type"],
            entity_id=data["entity_id"],
            change_type=ChangeType(data["change_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata"),
        )


class ChangeTracker:
    """Tracks entity changes for automatic reindexing.

    Maintains an in-memory queue of pending changes with optional
    persistence to disk for recovery after restart.

    Example:
        >>> tracker = ChangeTracker()
        >>> tracker.track_change("invoice", 123, ChangeType.UPDATE)
        >>> changes = tracker.get_pending_changes(batch_size=50)
        >>> tracker.mark_processed([c.entity_id for c in changes])
    """

    def __init__(self):
        """Initialize change tracker."""
        self.config = get_auto_update_config()

        # Pending changes (entity_type -> entity_id -> EntityChange)
        self._pending: dict[str, dict[int, EntityChange]] = {}

        # Load persisted queue if exists
        if self.config.persist_queue_on_shutdown:
            self._load_from_disk()

        logger.info("change_tracker_initialized", enabled=self.config.enabled)

    def track_change(
        self,
        entity_type: str,
        entity_id: int,
        change_type: ChangeType | str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Track a change to an entity.

        Args:
            entity_type: Type of entity (invoice, client, product)
            entity_id: Entity ID
            change_type: Type of change
            metadata: Optional metadata about the change
        """
        if not self.config.enabled:
            return

        # Convert string to enum if needed
        if isinstance(change_type, str):
            change_type = ChangeType(change_type)

        # Check if this entity type is tracked
        tracked_entities = self.config.get_tracked_entities()
        if entity_type not in tracked_entities:
            logger.debug(
                "entity_type_not_tracked",
                entity_type=entity_type,
                tracked=tracked_entities,
            )
            return

        # Create change entry
        change = EntityChange(
            entity_type=entity_type,
            entity_id=entity_id,
            change_type=change_type,
            timestamp=datetime.now(UTC),
            metadata=metadata,
        )

        # Add to pending (overwrite if exists - keeps latest change)
        if entity_type not in self._pending:
            self._pending[entity_type] = {}

        self._pending[entity_type][entity_id] = change

        # Check queue size limit
        total_pending = sum(len(entities) for entities in self._pending.values())
        if total_pending > self.config.max_queue_size:
            logger.warning(
                "change_queue_size_exceeded",
                size=total_pending,
                max_size=self.config.max_queue_size,
            )
            # Trim oldest changes (simple FIFO)
            self._trim_queue()

        logger.debug(
            "change_tracked",
            entity_type=entity_type,
            entity_id=entity_id,
            change_type=change_type.value,
            queue_size=total_pending,
        )

    def get_pending_changes(
        self,
        entity_type: str | None = None,
        batch_size: int | None = None,
    ) -> list[EntityChange]:
        """Get pending changes for reindexing.

        Args:
            entity_type: Filter by entity type (None for all)
            batch_size: Maximum number of changes to return

        Returns:
            List of pending changes
        """
        changes = []

        # Collect changes
        if entity_type:
            if entity_type in self._pending:
                changes = list(self._pending[entity_type].values())
        else:
            for entity_changes in self._pending.values():
                changes.extend(entity_changes.values())

        # Sort by timestamp (oldest first)
        changes.sort(key=lambda c: c.timestamp)

        # Apply batch size limit
        if batch_size:
            changes = changes[:batch_size]

        return changes

    def mark_processed(
        self,
        entity_type: str,
        entity_ids: list[int],
    ) -> None:
        """Mark changes as processed and remove from queue.

        Args:
            entity_type: Type of entity
            entity_ids: List of entity IDs to mark as processed
        """
        if entity_type not in self._pending:
            return

        count = 0
        for entity_id in entity_ids:
            if entity_id in self._pending[entity_type]:
                del self._pending[entity_type][entity_id]
                count += 1

        # Remove empty entity type dict
        if not self._pending[entity_type]:
            del self._pending[entity_type]

        logger.info(
            "changes_marked_processed",
            entity_type=entity_type,
            count=count,
            remaining=sum(len(e) for e in self._pending.values()),
        )

    def get_queue_stats(self) -> dict[str, Any]:
        """Get statistics about pending changes.

        Returns:
            Dictionary with queue statistics
        """
        stats = {
            "total_pending": sum(len(entities) for entities in self._pending.values()),
            "by_entity_type": {},
            "by_change_type": {},
            "oldest_change": None,
            "newest_change": None,
        }

        all_changes = []
        for entity_type, entities in self._pending.items():
            stats["by_entity_type"][entity_type] = len(entities)

            for change in entities.values():
                all_changes.append(change)

                # Count by change type
                change_type_str = change.change_type.value
                stats["by_change_type"][change_type_str] = (
                    stats["by_change_type"].get(change_type_str, 0) + 1
                )

        # Find oldest and newest
        if all_changes:
            all_changes.sort(key=lambda c: c.timestamp)
            stats["oldest_change"] = all_changes[0].timestamp.isoformat()
            stats["newest_change"] = all_changes[-1].timestamp.isoformat()

        return stats

    def clear_all(self) -> None:
        """Clear all pending changes."""
        count = sum(len(entities) for entities in self._pending.values())
        self._pending.clear()

        logger.info("all_changes_cleared", count=count)

    def persist_to_disk(self) -> None:
        """Persist pending changes to disk for recovery."""
        if not self.config.persist_queue_on_shutdown:
            return

        # Convert to serializable format
        data = {
            entity_type: [change.to_dict() for change in entities.values()]
            for entity_type, entities in self._pending.items()
        }

        # Write to file
        try:
            with self.config.queue_persist_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            total = sum(len(changes) for changes in data.values())
            logger.info(
                "change_queue_persisted",
                path=str(self.config.queue_persist_path),
                count=total,
            )

        except Exception as e:
            logger.error("queue_persist_failed", error=str(e), exc_info=True)

    def _load_from_disk(self) -> None:
        """Load persisted changes from disk."""
        if not self.config.queue_persist_path.exists():
            return

        try:
            with self.config.queue_persist_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            # Reconstruct pending changes
            for entity_type, changes_list in data.items():
                self._pending[entity_type] = {
                    change_dict["entity_id"]: EntityChange.from_dict(change_dict)
                    for change_dict in changes_list
                }

            total = sum(len(entities) for entities in self._pending.values())
            logger.info(
                "change_queue_loaded_from_disk",
                path=str(self.config.queue_persist_path),
                count=total,
            )

        except Exception as e:
            logger.error("queue_load_failed", error=str(e), exc_info=True)

    def _trim_queue(self) -> None:
        """Trim queue to max size by removing oldest changes."""
        all_changes = []

        # Collect all changes
        for entity_type, entities in self._pending.items():
            for change in entities.values():
                all_changes.append((entity_type, change))

        # Sort by timestamp (oldest first)
        all_changes.sort(key=lambda x: x[1].timestamp)

        # Keep only newest max_queue_size items
        to_keep = all_changes[-self.config.max_queue_size :]

        # Rebuild pending dict
        self._pending.clear()
        for entity_type, change in to_keep:
            if entity_type not in self._pending:
                self._pending[entity_type] = {}
            self._pending[entity_type][change.entity_id] = change

        logger.warning(
            "change_queue_trimmed",
            removed=len(all_changes) - len(to_keep),
            remaining=len(to_keep),
        )


# Global tracker instance (singleton pattern)
_tracker: ChangeTracker | None = None


def get_change_tracker() -> ChangeTracker:
    """Get or create global change tracker instance.

    Returns:
        ChangeTracker singleton
    """
    global _tracker

    if _tracker is None:
        _tracker = ChangeTracker()

    return _tracker
