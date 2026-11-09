"""Merge tracked branches and add status/transport journals without changing invoices."""

from alembic import op
from openfatture.storage.database.status_migration import (
    downgrade_status_schema,
    upgrade_status_schema,
)

revision = "20261109_status"
down_revision = ("8cf82bd24752", "f6g4h5i6j7k8")
branch_labels = None
depends_on = None


def upgrade() -> None:
    upgrade_status_schema(op.get_bind())


def downgrade() -> None:
    downgrade_status_schema(op.get_bind())
