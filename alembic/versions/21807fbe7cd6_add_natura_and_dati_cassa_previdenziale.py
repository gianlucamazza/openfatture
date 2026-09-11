"""add_natura_and_dati_cassa_previdenziale

Revision ID: 21807fbe7cd6
Revises: 692d8837
Create Date: 2026-09-11 12:24:06.697789

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "21807fbe7cd6"
down_revision: str | Sequence[str] | None = "692d8837"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - Add natura field to righe_fattura and create dati_cassa_previdenziale table.

    These changes enable:
    - Proper handling of zero-rated, exempt, and out-of-scope VAT transactions (natura codes)
    - Support for social security contributions (e.g., INPS for professionals)
    - Full compliance with FatturaPA v1.2.2 XSD schema
    """
    # Add natura column to righe_fattura
    with op.batch_alter_table("righe_fattura", schema=None) as batch_op:
        batch_op.add_column(sa.Column("natura", sa.String(length=10), nullable=True))

    # Create dati_cassa_previdenziale table
    op.create_table(
        "dati_cassa_previdenziale",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fattura_id", sa.Integer(), nullable=False),
        sa.Column("tipo_cassa", sa.String(length=4), nullable=False),
        sa.Column("al_cassa", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("importo_contributo_cassa", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("imponibile_cassa", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("aliquota_iva", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("ritenuta", sa.String(length=2), nullable=True),
        sa.Column("natura", sa.String(length=10), nullable=True),
        sa.Column("riferimento_amministrazione", sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(
            ["fattura_id"],
            ["fatture.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema - Remove natura field and dati_cassa_previdenziale table."""
    # Drop dati_cassa_previdenziale table
    op.drop_table("dati_cassa_previdenziale")

    # Remove natura column from righe_fattura
    with op.batch_alter_table("righe_fattura", schema=None) as batch_op:
        batch_op.drop_column("natura")
