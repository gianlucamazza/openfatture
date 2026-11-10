"""Natura on quote lines; drop the redundant bollo flag and unused feedback tables.

- ``righe_preventivo.natura``: quotes carry the VAT natura of their lines so
  that a 0% line converts to a valid invoice line.
- ``fatture.bollo_assolto_virtuale``: electronic invoices always pay the stamp
  duty virtually (``BolloVirtuale=SI``); charging it to the customer is an
  ``N1`` line, so the flag had no meaning.
- ``user_feedback`` and ``model_prediction_feedback``: leftovers of the ML
  stack removed in 2.8.0, never written.
"""

import sqlalchemy as sa
from alembic import op

revision = "20261110_vat_natura"
down_revision = "20261110_uq_numero"
branch_labels = None
depends_on = None


def _columns(table: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    if "natura" not in _columns("righe_preventivo"):
        with op.batch_alter_table("righe_preventivo") as batch_op:
            batch_op.add_column(sa.Column("natura", sa.String(10), nullable=True))
    if "bollo_assolto_virtuale" in _columns("fatture"):
        with op.batch_alter_table("fatture") as batch_op:
            batch_op.drop_column("bollo_assolto_virtuale")
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    for table in ("user_feedback", "model_prediction_feedback"):
        if table in tables:
            op.drop_table(table)


def downgrade() -> None:
    with op.batch_alter_table("fatture") as batch_op:
        batch_op.add_column(
            sa.Column("bollo_assolto_virtuale", sa.Boolean(), nullable=False, server_default="0")
        )
    with op.batch_alter_table("righe_preventivo") as batch_op:
        batch_op.drop_column("natura")
