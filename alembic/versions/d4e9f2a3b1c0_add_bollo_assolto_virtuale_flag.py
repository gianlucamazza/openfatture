"""add_bollo_assolto_virtuale_flag

Revision ID: d4e9f2a3b1c0
Revises: 21807fbe7cd6
Create Date: 2026-09-15 06:50:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e9f2a3b1c0"
down_revision: str | Sequence[str] | None = "21807fbe7cd6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - Add bollo_assolto_virtuale flag to fatture table.

    This field indicates whether the stamp duty (bollo) is "assolto virtuale"
    (paid separately by the provider and not charged to the client).

    When True: bollo amount is not added to the client's payable total.
    When False (default): bollo is charged to the client (added to total).
    """
    with op.batch_alter_table("fatture", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("bollo_assolto_virtuale", sa.Boolean(), nullable=False, server_default="0")
        )


def downgrade() -> None:
    """Downgrade schema - Remove bollo_assolto_virtuale flag."""
    with op.batch_alter_table("fatture", schema=None) as batch_op:
        batch_op.drop_column("bollo_assolto_virtuale")
