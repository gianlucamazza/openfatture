"""add_composite_indexes_for_performance

Revision ID: c5568d1a4226
Revises: 
Create Date: 2025-11-11 17:03:17.994550

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = 'c5568d1a4226'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add composite indexes for performance optimization."""
    # Composite index for event_log: filter by event_type and sort by occurred_at
    # Optimizes queries like: "SELECT * FROM event_log WHERE event_type = ? ORDER BY occurred_at"
    op.create_index('ix_event_log_type_occurred', 'event_log', ['event_type', 'occurred_at'], unique=False)

    # Composite index for event_log: filter by entity
    # Optimizes queries like: "SELECT * FROM event_log WHERE entity_type = ? AND entity_id = ?"
    op.create_index('ix_event_log_entity', 'event_log', ['entity_type', 'entity_id'], unique=False)

    # Composite index for bank_transactions: filter by status and sort by date
    # Optimizes queries like: "SELECT * FROM bank_transactions WHERE status = ? ORDER BY date"
    op.create_index('ix_bank_transactions_status_date', 'bank_transactions', ['status', 'date'], unique=False)


def downgrade() -> None:
    """Downgrade schema - Remove composite indexes."""
    op.drop_index('ix_bank_transactions_status_date', table_name='bank_transactions')
    op.drop_index('ix_event_log_entity', table_name='event_log')
    op.drop_index('ix_event_log_type_occurred', table_name='event_log')
