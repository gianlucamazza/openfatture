"""Idempotent migration of pre-ledger cumulative balances into opening evidence."""

from decimal import Decimal
from typing import cast

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import Table, func, inspect, select
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session

from openfatture.storage.database.models import (
    CollectionEntry,
    CollectionOperation,
    CollectionReceipt,
    CollectionStatement,
    Fattura,
    Pagamento,
)


def migrate_balances(session: Session) -> None:
    """Append only unexplained legacy balances; abort rather than alter financial totals."""
    from openfatture.payment.application.collection_ledger import record
    from openfatture.payment.domain.models import BankTransaction
    from openfatture.payment.domain.payment_allocation import PaymentAllocation

    inspector = inspect(session.connection())
    for payment in session.scalars(select(Pagamento).order_by(Pagamento.id)).all():
        if not payment.importo_pagato:
            continue
        if payment.importo_pagato < 0 or payment.importo_pagato > payment.importo:
            raise ValueError(f"Invalid historical payment balance {payment.id}")
        existing = session.scalar(
            select(func.coalesce(func.sum(CollectionEntry.amount), 0)).where(
                CollectionEntry.payment_id == payment.id
            )
        ) or Decimal("0")
        if existing > payment.importo_pagato:
            raise ValueError(f"Ledger/cache mismatch for payment {payment.id}")
        if existing == payment.importo_pagato:
            continue
        if existing != 0:
            raise ValueError(f"Unexplained payment change {payment.id}; reconcile explicitly")
        explained = Decimal("0")
        allocations = (
            session.scalars(
                select(PaymentAllocation).where(PaymentAllocation.payment_id == payment.id)
            ).all()
            if inspector.has_table("payment_allocations")
            else []
        )
        for allocation in allocations:
            transaction = session.get(BankTransaction, allocation.transaction_id)
            if transaction is None or transaction.amount <= 0 or allocation.amount <= 0:
                raise ValueError(f"Invalid historical bank allocation {allocation.id}")
            if transaction.account.currency != "EUR":
                raise ValueError("Historical non-EUR allocation requires explicit review")
            receipt = session.scalar(
                select(CollectionReceipt).where(
                    CollectionReceipt.bank_transaction_id == str(transaction.id)
                )
            )
            if receipt is None:
                receipt = record(
                    session,
                    request_id=f"bank-opening:{transaction.id}",
                    amount=str(transaction.amount),
                    origin="bank",
                    bank_transaction_id=str(transaction.id),
                    effective_date=transaction.date,
                )
            if receipt.allocated + allocation.amount > receipt.amount:
                raise ValueError(f"Historical bank allocation exceeds transaction {transaction.id}")
            session.add(
                CollectionEntry(
                    request_id=f"legacy-allocation:{allocation.id}",
                    receipt_id=receipt.id,
                    invoice_id=payment.fattura_id,
                    payment_id=payment.id,
                    amount=allocation.amount,
                )
            )
            receipt.allocated += allocation.amount
            explained += allocation.amount
        remainder = payment.importo_pagato - explained
        if remainder < 0:
            raise ValueError(f"Historical allocations exceed cumulative balance {payment.id}")
        if remainder:
            receipt = record(
                session,
                request_id=f"opening-payment:{payment.id}",
                amount=str(remainder),
                origin="opening",
                notes="Migrated cumulative balance; individual receipt dates not attested",
            )
            receipt.allocated = remainder
            session.add(
                CollectionEntry(
                    request_id=f"opening-allocation:{payment.id}",
                    receipt_id=receipt.id,
                    invoice_id=payment.fattura_id,
                    payment_id=payment.id,
                    amount=remainder,
                )
            )
        session.flush()
    session.flush()
    for receipt in session.scalars(select(CollectionReceipt)).all():
        net = session.scalar(
            select(func.coalesce(func.sum(CollectionEntry.amount), 0)).where(
                CollectionEntry.receipt_id == receipt.id
            )
        ) or Decimal("0")
        if net != receipt.allocated or net < 0 or net > receipt.amount:
            raise ValueError(f"Ledger/cache mismatch for receipt {receipt.id}")
        if receipt.bank_transaction_id:
            from openfatture.payment.application.collection_ledger import refresh_bank_state

            refresh_bank_state(session, receipt)
    for invoice in session.scalars(select(Fattura)).all():
        paid = session.scalar(
            select(func.coalesce(func.sum(CollectionEntry.amount), 0)).where(
                CollectionEntry.invoice_id == invoice.id
            )
        ) or Decimal("0")
        if paid < 0 or paid > invoice.totale:
            raise ValueError(f"Historical invoice {invoice.id} has inconsistent collections")


def ensure_balances(session: Session) -> None:
    """Prepare legacy balances once, in the same transaction as the first operation."""
    from openfatture.storage.database.models import CollectionOperation

    marker = session.scalar(
        select(CollectionOperation).where(CollectionOperation.request_id == "ledger:migrated-v1")
    )
    if marker is not None:
        return
    migrate_balances(session)
    session.add(
        CollectionOperation(request_id="ledger:migrated-v1", fingerprint="schema-v1", result="{}")
    )
    session.flush()


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


def upgrade_collection_database(engine: Engine) -> None:
    """Run the collection upgrade in one transaction with foreign-key validation."""
    with engine.connect() as connection:
        sqlite = connection.dialect.name == "sqlite"
        if sqlite:
            connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
            connection.commit()
            connection.exec_driver_sql("BEGIN IMMEDIATE")
        try:
            upgrade_collections(connection)
            if sqlite and connection.exec_driver_sql("PRAGMA foreign_key_check").fetchall():
                raise ValueError("Foreign-key validation failed")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            if sqlite:
                connection.exec_driver_sql("PRAGMA foreign_keys=ON")
                connection.commit()
