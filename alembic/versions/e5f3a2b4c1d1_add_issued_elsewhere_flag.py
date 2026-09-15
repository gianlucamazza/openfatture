"""add_issued_elsewhere_flag

Revision ID: e5f3a2b4c1d1
Revises: d4e9f2a3b1c0
Create Date: 2026-09-15 07:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f3a2b4c1d1"
down_revision: str | Sequence[str] | None = "d4e9f2a3b1c0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - Add issued_elsewhere flag to fatture table.

    This field indicates whether the invoice was issued outside the system
    (e.g., by another person or service) and is stored here only for
    reference/calibration purposes.

    When True: blocks XML generation, SDI sending, and all emit flows.
    When False (default): normal invoice processing allowed.
    """
    with op.batch_alter_table("fatture", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("issued_elsewhere", sa.Boolean(), nullable=False, server_default="0")
        )


def downgrade() -> None:
    """Downgrade schema - Remove issued_elsewhere flag."""
    with op.batch_alter_table("fatture", schema=None) as batch_op:
        batch_op.drop_column("issued_elsewhere")
