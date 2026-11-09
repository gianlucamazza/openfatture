"""Explicit bank allocations. No debit is ever converted into an incoming amount."""

from decimal import Decimal
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from openfatture.payment.application import collection_ledger as ledger
from openfatture.payment.application.collection_migration import ensure_balances
from openfatture.payment.domain.enums import TransactionStatus
from openfatture.payment.domain.models import BankTransaction
from openfatture.storage.database.models import CollectionEntry, CollectionReceipt, Pagamento


def bank_receipt(session: Session, transaction: BankTransaction) -> CollectionReceipt:
    if transaction.amount <= 0:
        raise ValueError("Only positive incoming bank movements can settle an invoice")
    if transaction.account.currency != "EUR":
        raise ValueError("Only EUR bank movements are supported by the EUR collection ledger")
    receipt = session.scalar(
        select(CollectionReceipt).where(
            CollectionReceipt.bank_transaction_id == str(transaction.id)
        )
    )
    if receipt is None:
        receipt = ledger.record(
            session,
            request_id=f"bank:{transaction.id}",
            amount=str(transaction.amount),
            origin="bank",
            effective_date=transaction.date,
            bank_transaction_id=str(transaction.id),
        )
    if receipt.amount != transaction.amount:
        raise ValueError("Bank movement changed after collection registration")
    return receipt


def reconcile_bank(
    session: Session,
    transaction: BankTransaction,
    payment: Pagamento,
    request_id: str | None = None,
    amount: Decimal | None = None,
) -> CollectionEntry:
    if transaction.status not in {TransactionStatus.UNMATCHED, TransactionStatus.PARTIALLY_MATCHED}:
        raise ValueError(f"Transaction cannot be reconciled in state: {transaction.status}")
    if payment.saldo_residuo <= 0:
        raise ValueError("Payment is already fully paid")
    if payment.id is None:
        raise ValueError("Persist payment schedule before reconciling")
    ensure_balances(session)
    receipt = bank_receipt(session, transaction)
    value = (
        amount
        if amount is not None
        else min(receipt.amount - receipt.allocated, payment.saldo_residuo)
    )
    entry = ledger.allocate(
        session,
        request_id=request_id or str(uuid4()),
        receipt_id=receipt.id,
        invoice_id=payment.fattura_id,
        payment_id=payment.id,
        amount=str(value),
    )
    transaction.raw_data = {
        **(transaction.raw_data or {}),
        "reconciliation": {
            "receipt_id": receipt.id,
            "allocated_amount": str(receipt.allocated),
            "unallocated_amount": str(receipt.amount - receipt.allocated),
        },
    }
    return entry


def reset_bank(
    session: Session, transaction: BankTransaction, request_id: str | None = None
) -> Decimal:
    ensure_balances(session)
    receipt = session.scalar(
        select(CollectionReceipt).where(
            CollectionReceipt.bank_transaction_id == str(transaction.id)
        )
    )
    if receipt is None:
        raise ValueError("Transaction is not matched: no collection evidence exists")
    entries = session.scalars(
        select(CollectionEntry)
        .where(CollectionEntry.receipt_id == receipt.id, CollectionEntry.amount > 0)
        .order_by(CollectionEntry.id)
    ).all()
    key = request_id or str(uuid4())
    reverted = Decimal("0")
    for entry in entries:
        reversals = session.scalar(
            select(func.coalesce(func.sum(CollectionEntry.amount), 0)).where(
                CollectionEntry.reverses_id == entry.id
            )
        ) or Decimal("0")
        active = entry.amount + reversals
        if active:
            ledger.reverse(
                session,
                request_id=f"{key}:{entry.id}",
                entry_id=entry.id,
                amount=str(active),
                reason="Bank reconciliation reset",
            )
            reverted += active
    transaction.status = TransactionStatus.UNMATCHED
    transaction.matched_payment_id = None
    transaction.match_type = transaction.match_confidence = transaction.matched_at = None
    return reverted
