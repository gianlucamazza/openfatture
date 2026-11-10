"""Add collection ledger and migrate historical cumulative payment balances."""

from alembic import op
from openfatture.payment.application.collection_migration import upgrade_collections

revision = "20261109_collections"
down_revision = "20261109_status"
branch_labels = None
depends_on = None


def upgrade():
    upgrade_collections(op.get_bind())


def downgrade():
    raise RuntimeError("Restore a pre-upgrade backup; collection history must not be discarded")
