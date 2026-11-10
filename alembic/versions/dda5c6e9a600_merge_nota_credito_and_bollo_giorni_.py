"""merge_nota_credito_and_bollo_giorni_branches

Revision ID: dda5c6e9a600
Revises: 8cf82bd24752, f6g4h5i6j7k8
Create Date: 2026-09-30 17:58:15.479375

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "dda5c6e9a600"
down_revision: str | Sequence[str] | None = ("8cf82bd24752", "f6g4h5i6j7k8")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
