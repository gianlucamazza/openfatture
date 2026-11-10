"""Enforce unique invoice numbers per year.

Refuses to run while duplicates exist, listing them, so they can be renumbered
deliberately instead of being silently altered.
"""

import sqlalchemy as sa

from alembic import op

revision = "20261110_uq_numero"
down_revision = "20261110_merge"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    duplicates = bind.execute(
        sa.text(
            "SELECT anno, numero, COUNT(*) FROM fatture "
            "GROUP BY anno, numero HAVING COUNT(*) > 1 ORDER BY anno, numero"
        )
    ).all()
    if duplicates:
        listed = ", ".join(f"{numero}/{anno} (x{count})" for anno, numero, count in duplicates)
        raise RuntimeError(f"Duplicate invoice numbers must be resolved before upgrading: {listed}")
    if "uq_fatture_numero_anno" not in {i["name"] for i in sa.inspect(bind).get_indexes("fatture")}:
        op.create_index("uq_fatture_numero_anno", "fatture", ["numero", "anno"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_fatture_numero_anno", table_name="fatture")
