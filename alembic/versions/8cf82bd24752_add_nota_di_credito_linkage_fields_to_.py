"""Add nota di credito linkage fields to Fattura

Revision ID: 8cf82bd24752
Revises: 21807fbe7cd6
Create Date: 2026-09-11 17:33:29.903102

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8cf82bd24752"
down_revision: str | Sequence[str] | None = "21807fbe7cd6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - Add nota di credito linkage fields to fatture table.

    These changes enable:
    - Linking credit notes (TD04) to their source invoices
    - Emitting FatturaPA DatiFattureCollegate XML elements
    - Full compliance with FatturaPA v1.2.2 credit note requirements

    The three fields added:
    - fattura_collegata_id: Foreign key to source invoice
    - fattura_collegata_numero: Source invoice number (for XML)
    - fattura_collegata_data: Source invoice date (for XML)
    """
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table("fatture", schema=None) as batch_op:
        # Add linkage columns for nota di credito (credit note) support
        batch_op.add_column(sa.Column("fattura_collegata_id", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column("fattura_collegata_numero", sa.String(length=20), nullable=True)
        )
        batch_op.add_column(sa.Column("fattura_collegata_data", sa.Date(), nullable=True))

        # Add foreign key constraint to link back to source fattura
        batch_op.create_foreign_key(
            "fk_fatture_fattura_collegata_id_fatture",
            "fatture",
            ["fattura_collegata_id"],
            ["id"],
        )

        # Add index for faster lookups of credit notes by source invoice
        batch_op.create_index(
            "ix_fatture_fattura_collegata_id",
            ["fattura_collegata_id"],
            unique=False,
        )


def downgrade() -> None:
    """Downgrade schema - Remove nota di credito linkage fields from fatture table."""
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table("fatture", schema=None) as batch_op:
        # Drop index first
        batch_op.drop_index("ix_fatture_fattura_collegata_id")

        # Drop foreign key constraint
        batch_op.drop_constraint("fk_fatture_fattura_collegata_id_fatture", type_="foreignkey")

        # Drop columns
        batch_op.drop_column("fattura_collegata_data")
        batch_op.drop_column("fattura_collegata_numero")
        batch_op.drop_column("fattura_collegata_id")
