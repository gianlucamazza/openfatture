"""Collection ledger upgrade is idempotent on an initialized database."""

import openfatture.storage.database.base as db_base
from openfatture.payment.application.collection_migration import upgrade_collection_database


def test_upgrade_collection_database_is_idempotent(runtime_db):
    assert db_base.engine is not None
    upgrade_collection_database(db_base.engine)
    upgrade_collection_database(db_base.engine)
