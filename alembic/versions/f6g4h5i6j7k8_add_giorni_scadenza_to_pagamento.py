"""add_giorni_scadenza_to_pagamento

Revision ID: f6g4h5i6j7k8
Revises: e5f3a2b4c1d1
Create Date: 2026-09-15 07:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f6g4h5i6j7k8"
down_revision: str | Sequence[str] | None = "e5f3a2b4c1d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - Add giorni_scadenza to pagamenti table.

    This field indicates payment terms in days:
    - 0 = immediate payment (rif. termini = data emissione)
    - N = payment due N days from invoice date

    Default: 30 days for backward compatibility.
    """
    with op.batch_alter_table("pagamenti", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("giorni_scadenza", sa.Integer(), nullable=False, server_default="30")
        )


def downgrade() -> None:
    """Downgrade schema - Remove giorni_scadenza field."""
    with op.batch_alter_table("pagamenti", schema=None) as batch_op:
        batch_op.drop_column("giorni_scadenza")
