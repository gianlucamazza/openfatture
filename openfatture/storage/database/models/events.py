"""Domain event audit log model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from openfatture.platform.datetime import utc_now

from ..base import Base, IntPKMixin


class EventLog(IntPKMixin, Base):
    """Event audit log - stores all domain events for compliance and analytics.

    Captures every domain event published through the event bus for:
    - Audit trail and compliance
    - Historical analysis and reporting
    - Debugging and troubleshooting
    - Analytics and metrics
    """

    __tablename__ = "event_log"
    __table_args__ = (
        # Composite index for queries filtering by event_type and sorting by occurred_at
        Index("ix_event_log_type_occurred", "event_type", "occurred_at"),
        # Composite index for queries filtering by entity
        Index("ix_event_log_entity", "entity_type", "entity_id"),
    )

    # Event identification
    event_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, index=True
    )  # UUID as string
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Event payload (JSON serialized)
    event_data: Mapped[str] = mapped_column(Text, nullable=False)

    # Timestamps
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    # Entity tracking (for filtering by entity)
    entity_type: Mapped[str | None] = mapped_column(String(50), index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, index=True)

    # Additional metadata
    user_id: Mapped[int | None] = mapped_column(Integer)  # For future user tracking
    metadata_json: Mapped[str | None] = mapped_column(Text)  # JSON for additional context

    def __repr__(self) -> str:
        return f"<EventLog(id={self.id}, event_type='{self.event_type}', entity={self.entity_type}:{self.entity_id}, occurred_at='{self.occurred_at}')>"
