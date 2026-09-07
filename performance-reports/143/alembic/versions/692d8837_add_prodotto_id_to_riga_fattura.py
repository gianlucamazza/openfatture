"""add_prodotto_id_to_riga_fattura

Revision ID: 692d8837
Revises: c5568d1a4226
Create Date: 2025-12-01 12:25:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "692d8837"
down_revision: str | Sequence[str] | None = "c5568d1a4226"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - Add prodotto_id column to righe_fattura table.

    This enables linking invoice line items to products in the product catalog,
    allowing for:
    - Product-based analytics
    - AI product suggestions
    - Inventory tracking
    - Better invoice automation
    """
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table("righe_fattura", schema=None) as batch_op:
        # Add prodotto_id column (nullable to support existing invoices)
        batch_op.add_column(sa.Column("prodotto_id", sa.Integer(), nullable=True))

        # Add foreign key constraint to prodotti table
        batch_op.create_foreign_key(
            "fk_righe_fattura_prodotto_id",
            "prodotti",
            ["prodotto_id"],
            ["id"],
            ondelete="SET NULL",  # If product is deleted, set to NULL (preserve invoice history)
        )

        # Add index for faster product lookups
        batch_op.create_index("ix_righe_fattura_prodotto_id", ["prodotto_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema - Remove prodotto_id column from righe_fattura table."""
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table("righe_fattura", schema=None) as batch_op:
        # Drop index first
        batch_op.drop_index("ix_righe_fattura_prodotto_id")

        # Drop foreign key constraint
        batch_op.drop_constraint("fk_righe_fattura_prodotto_id", type_="foreignkey")

        # Drop column
        batch_op.drop_column("prodotto_id")
