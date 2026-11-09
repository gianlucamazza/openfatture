"""Packaged schema/data migration for collection ledger and unknown due dates."""

from typing import cast

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import Table, inspect
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session

from openfatture.payment.application.collection_migration import migrate_balances
from openfatture.storage.database.models import (
    CollectionEntry,
    CollectionOperation,
    CollectionReceipt,
    CollectionStatement,
)


def upgrade_collections(connection: Connection) -> None:
    for model in (CollectionReceipt, CollectionEntry, CollectionStatement, CollectionOperation):
        cast(Table, model.__table__).create(connection, checkfirst=True)
    columns = inspect(connection).get_columns("pagamenti")
    if any(c["name"] == "data_scadenza" and not c["nullable"] for c in columns):
        import sqlalchemy as sa

        operations = Operations(MigrationContext.configure(connection))
        with operations.batch_alter_table("pagamenti") as batch:
            batch.alter_column("data_scadenza", existing_type=sa.Date(), nullable=True)
    if connection.dialect.name == "postgresql" and inspect(connection).has_table(
        "bank_transactions"
    ):
        connection.exec_driver_sql(
            "ALTER TABLE bank_transactions ALTER COLUMN status TYPE VARCHAR(32) USING status::text"
        )
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        migrate_balances(session)
        session.flush()
        session.commit()
    finally:
        session.close()
