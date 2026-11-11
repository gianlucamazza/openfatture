"""Idempotent migration of pre-ledger cumulative balances into opening evidence."""

from collections.abc import Sequence
from decimal import Decimal
from typing import TYPE_CHECKING, cast

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import Table, func, inspect, select
from sqlalchemy.engine import Connection, Inspector
from sqlalchemy.orm import InstrumentedAttribute, Session

from openfatture.storage.database.models import (
    CollectionEntry,
    CollectionOperation,
    CollectionReceipt,
    CollectionStatement,
    Fattura,
    Pagamento,
)

if TYPE_CHECKING:
    from openfatture.payment.domain.models import BankTransaction
    from openfatture.payment.domain.payment_allocation import PaymentAllocation


def _ledger_total(
    session: Session,
    column: InstrumentedAttribute[int] | InstrumentedAttribute[int | None],
    key: int,
) -> Decimal:
    """Sum the ledger entries whose ``column`` equals ``key``."""
    return session.scalar(
        select(func.coalesce(func.sum(CollectionEntry.amount), 0)).where(column == key)
    ) or Decimal("0")


def _needs_opening(session: Session, payment: Pagamento) -> bool:
    """Validate the cached balance and tell whether the ledger still has to explain it."""
    if payment.importo_pagato < 0 or payment.importo_pagato > payment.importo:
        raise ValueError(f"Invalid historical payment balance {payment.id}")
    existing = _ledger_total(session, CollectionEntry.payment_id, payment.id)
    if existing > payment.importo_pagato:
        raise ValueError(f"Ledger/cache mismatch for payment {payment.id}")
    if existing == payment.importo_pagato:
        return False
    if existing != 0:
        raise ValueError(f"Unexplained payment change {payment.id}; reconcile explicitly")
    return True


def _legacy_allocations(
    session: Session, payment: Pagamento, inspector: Inspector
) -> Sequence["PaymentAllocation"]:
    from openfatture.payment.domain.payment_allocation import PaymentAllocation

    if not inspector.has_table("payment_allocations"):
        return []
    return session.scalars(
        select(PaymentAllocation).where(PaymentAllocation.payment_id == payment.id)
    ).all()


def _bank_receipt(session: Session, transaction: "BankTransaction") -> CollectionReceipt:
    """Return the receipt of a bank transaction, recording it on first use."""
    from openfatture.payment.application.collection_ledger import record

    receipt = session.scalar(
        select(CollectionReceipt).where(
            CollectionReceipt.bank_transaction_id == str(transaction.id)
        )
    )
    if receipt is not None:
        return receipt
    return record(
        session,
        request_id=f"bank-opening:{transaction.id}",
        amount=str(transaction.amount),
        origin="bank",
        bank_transaction_id=str(transaction.id),
        effective_date=transaction.date,
    )


def _migrate_allocation(
    session: Session, payment: Pagamento, allocation: "PaymentAllocation"
) -> Decimal:
    """Turn one legacy bank allocation into a ledger entry; return the amount explained."""
    from openfatture.payment.domain.models import BankTransaction

    transaction = session.get(BankTransaction, allocation.transaction_id)
    if transaction is None or transaction.amount <= 0 or allocation.amount <= 0:
        raise ValueError(f"Invalid historical bank allocation {allocation.id}")
    if transaction.account.currency != "EUR":
        raise ValueError("Historical non-EUR allocation requires explicit review")
    receipt = _bank_receipt(session, transaction)
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
    return allocation.amount


def _record_opening(session: Session, payment: Pagamento, remainder: Decimal) -> None:
    """Record the unexplained part of a cumulative balance as opening evidence."""
    from openfatture.payment.application.collection_ledger import record

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


def _migrate_payment(session: Session, payment: Pagamento, inspector: Inspector) -> None:
    if not payment.importo_pagato or not _needs_opening(session, payment):
        return
    explained = Decimal("0")
    for allocation in _legacy_allocations(session, payment, inspector):
        explained += _migrate_allocation(session, payment, allocation)
    remainder = payment.importo_pagato - explained
    if remainder < 0:
        raise ValueError(f"Historical allocations exceed cumulative balance {payment.id}")
    if remainder:
        _record_opening(session, payment, remainder)
    session.flush()


def _verify_receipts(session: Session) -> None:
    from openfatture.payment.application.collection_ledger import refresh_bank_state

    for receipt in session.scalars(select(CollectionReceipt)).all():
        net = _ledger_total(session, CollectionEntry.receipt_id, receipt.id)
        if net != receipt.allocated or net < 0 or net > receipt.amount:
            raise ValueError(f"Ledger/cache mismatch for receipt {receipt.id}")
        if receipt.bank_transaction_id:
            refresh_bank_state(session, receipt)


def _verify_invoices(session: Session) -> None:
    for invoice in session.scalars(select(Fattura)).all():
        paid = _ledger_total(session, CollectionEntry.invoice_id, invoice.id)
        if paid < 0 or paid > invoice.totale:
            raise ValueError(f"Historical invoice {invoice.id} has inconsistent collections")


def migrate_balances(session: Session) -> None:
    """Append only unexplained legacy balances; abort rather than alter financial totals."""
    inspector = inspect(session.connection())
    for payment in session.scalars(select(Pagamento).order_by(Pagamento.id)).all():
        _migrate_payment(session, payment, inspector)
    session.flush()
    _verify_receipts(session)
    _verify_invoices(session)


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
