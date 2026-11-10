"""Merge the empty dda5c6e9a600 branch merge into the collection ledger head.

Databases stamped at ``dda5c6e9a600`` upgrade through the status journals and
collection ledger revisions; both are idempotent (``checkfirst``) so tables
already present from ``create_all`` are preserved.
"""

revision = "20261110_merge"
down_revision = ("dda5c6e9a600", "20261109_collections")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
