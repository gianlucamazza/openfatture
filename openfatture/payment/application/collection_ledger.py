"""Transactional incoming-money ledger. Callers own commit/rollback."""

from datetime import date
from decimal import Decimal, DecimalException
from typing import Any, cast

from sqlalchemy import func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from openfatture.storage.database.models import (
    CollectionEntry,
    CollectionReceipt,
    CollectionStatement,
    Fattura,
    Pagamento,
)


def money(value: Decimal | str | int) -> Decimal:
    try:
        amount = Decimal(str(value))
        if (
            not amount.is_finite()
            or amount <= 0
            or amount > Decimal("9999999999.99")
            or amount != amount.quantize(Decimal("0.01"))
        ):
            raise ValueError("Require a positive finite cent amount within ledger capacity")
        return amount
    except DecimalException as exc:
        raise ValueError("Invalid money amount") from exc


def total_paid(session: Session, invoice_id: int) -> Decimal:
    return session.scalar(
        select(func.coalesce(func.sum(CollectionEntry.amount), 0)).where(
            CollectionEntry.invoice_id == invoice_id
        )
    ) or Decimal("0.00")


def record(
    session: Session,
    *,
    request_id: str,
    amount: str,
    origin: str = "manual",
    effective_date: date | None = None,
    bank_transaction_id: str | None = None,
    notes: str | None = None,
) -> CollectionReceipt:
    if not request_id.strip() or origin not in {"manual", "bank", "opening"}:
        raise ValueError("Require request ID and valid receipt origin")
    value = money(amount)
    existing = session.scalar(
        select(CollectionReceipt).where(CollectionReceipt.request_id == request_id)
    )
    if existing:
        if (
            existing.notes,
            existing.amount,
            existing.origin,
            existing.effective_date,
            existing.bank_transaction_id,
        ) != (notes, value, origin, effective_date, bank_transaction_id):
            raise ValueError("Request ID already identifies another operation")
        return existing
    if (origin == "bank") != bool(bank_transaction_id):
        raise ValueError(
            "Bank receipts require a transaction identity; other origins cannot supply one"
        )
    receipt = CollectionReceipt(
        request_id=request_id,
        amount=value,
        origin=origin,
        effective_date=effective_date,
        bank_transaction_id=bank_transaction_id,
        notes=notes,
        allocated=Decimal("0"),
    )
    session.add(receipt)
    session.flush()
    return receipt


def allocate(
    session: Session,
    *,
    request_id: str,
    receipt_id: int,
    invoice_id: int,
    amount: str,
    payment_id: int | None = None,
) -> CollectionEntry:
    if not request_id.strip():
        raise ValueError("Request ID is required")
    from openfatture.payment.application.collection_migration import ensure_balances

    ensure_balances(session)
    value = money(amount)
    existing = session.scalar(
        select(CollectionEntry).where(CollectionEntry.request_id == request_id)
    )
    if existing:
        if (
            existing.receipt_id,
            existing.invoice_id,
            existing.payment_id,
            existing.amount,
            existing.reverses_id,
        ) != (receipt_id, invoice_id, payment_id, value, None):
            raise ValueError("Conflicting allocation request ID")
        return existing
    invoice = session.get(Fattura, invoice_id)
    receipt = session.get(CollectionReceipt, receipt_id)
    if invoice is None or receipt is None:
        raise ValueError("Invoice or receipt not found")
    payment = session.get(Pagamento, payment_id) if payment_id is not None else None
    if payment_id is not None and (payment is None or payment.fattura_id != invoice_id):
        raise ValueError("Payment must belong to the selected invoice")
    # Conditional writes lock both budget owners before computing remaining balances.
    locked = session.execute(
        update(Fattura)
        .where(Fattura.id == invoice_id, Fattura.updated_at == invoice.updated_at)
        .values(updated_at=Fattura.updated_at)
        .execution_options(synchronize_session=False)
    )
    if cast(CursorResult[Any], locked).rowcount != 1:
        raise ValueError("Invoice changed concurrently")
    paid = total_paid(session, invoice_id)
    if paid + value > invoice.totale:
        raise ValueError("Allocation exceeds invoice balance")
    if payment:
        session.refresh(payment)
    if payment and payment.importo_pagato + value > payment.importo:
        raise ValueError("Allocation exceeds installment balance")
    updated = session.execute(
        update(CollectionReceipt)
        .where(
            CollectionReceipt.id == receipt_id,
            CollectionReceipt.allocated + value <= CollectionReceipt.amount,
        )
        .values(allocated=CollectionReceipt.allocated + value)
        .execution_options(synchronize_session=False)
    )
    if cast(CursorResult[Any], updated).rowcount != 1:
        raise ValueError("Allocation exceeds available receipt amount")
    entry = CollectionEntry(
        request_id=request_id,
        receipt_id=receipt_id,
        invoice_id=invoice_id,
        payment_id=payment_id,
        amount=value,
    )
    session.add(entry)
    if payment:
        payment.apply_payment(value, pagamento_effective_date=receipt.effective_date)
    session.flush()
    session.expire(receipt)
    session.expire(invoice, ["collection_entries"])
    refresh_bank_state(session, receipt)
    return entry


def reverse(
    session: Session, *, request_id: str, entry_id: int, amount: str, reason: str
) -> CollectionEntry:
    from openfatture.payment.application.collection_migration import ensure_balances

    ensure_balances(session)
    value = money(amount)
    if not reason.strip():
        raise ValueError("Reversal reason is required")
    existing = session.scalar(
        select(CollectionEntry).where(CollectionEntry.request_id == request_id)
    )
    if existing:
        if (
            existing.reverses_id != entry_id
            or existing.amount != -value
            or existing.notes != reason
        ):
            raise ValueError("Conflicting reversal request ID")
        return existing
    original = session.get(CollectionEntry, entry_id)
    if original is None or original.amount <= 0:
        raise ValueError("Only positive original allocations can be reversed")
    session.execute(
        update(Fattura)
        .where(Fattura.id == original.invoice_id)
        .values(updated_at=Fattura.updated_at)
        .execution_options(synchronize_session=False)
    )
    session.execute(
        update(CollectionReceipt)
        .where(CollectionReceipt.id == original.receipt_id)
        .values(allocated=CollectionReceipt.allocated)
        .execution_options(synchronize_session=False)
    )
    reversed_amount = -(
        session.scalar(
            select(func.coalesce(func.sum(CollectionEntry.amount), 0)).where(
                CollectionEntry.reverses_id == entry_id
            )
        )
        or Decimal("0")
    )
    if reversed_amount + value > original.amount:
        raise ValueError("Reversal exceeds active allocation")
    entry = CollectionEntry(
        request_id=request_id,
        receipt_id=original.receipt_id,
        invoice_id=original.invoice_id,
        payment_id=original.payment_id,
        amount=-value,
        reverses_id=original.id,
        notes=reason,
    )
    session.execute(
        update(CollectionReceipt)
        .where(CollectionReceipt.id == original.receipt_id)
        .values(allocated=CollectionReceipt.allocated - value)
        .execution_options(synchronize_session=False)
    )
    if original.payment_id:
        payment = session.get(Pagamento, original.payment_id)
        if payment is None:
            raise ValueError("Installment not found")
        session.refresh(payment)
        payment.revert_payment(value)
    session.add(entry)
    session.flush()
    session.expire_all()
    receipt = session.get(CollectionReceipt, original.receipt_id)
    if receipt is None:
        raise ValueError("Receipt not found")
    refresh_bank_state(session, receipt)
    return entry


def refresh_bank_state(session: Session, receipt: CollectionReceipt) -> None:
    if not receipt.bank_transaction_id:
        return
    from uuid import UUID

    from openfatture.payment.domain.enums import TransactionStatus
    from openfatture.payment.domain.models import BankTransaction

    transaction = session.get(BankTransaction, UUID(receipt.bank_transaction_id))
    if transaction is None:
        raise ValueError("Bank transaction no longer exists")
    transaction.status = (
        TransactionStatus.UNMATCHED
        if receipt.allocated == 0
        else TransactionStatus.MATCHED
        if receipt.allocated == receipt.amount
        else TransactionStatus.PARTIALLY_MATCHED
    )
    payment_ids = session.execute(
        select(CollectionEntry.payment_id, func.sum(CollectionEntry.amount))
        .where(CollectionEntry.receipt_id == receipt.id)
        .group_by(CollectionEntry.payment_id)
    ).all()
    active = [pid for pid, amount in payment_ids if amount > 0]
    transaction.matched_payment_id = active[0] if len(active) == 1 else None


def declare_status(
    session: Session,
    *,
    request_id: str,
    invoice_id: int,
    value: str,
    source: str,
    declared_on: date | None = None,
    notes: str | None = None,
) -> CollectionStatement:
    from openfatture.storage.database.models import CollectionStatement

    if not request_id.strip() or value not in {"not_settled", "unknown"} or not source.strip():
        raise ValueError("Invalid declaration or missing provenance")
    if session.get(Fattura, invoice_id) is None:
        raise ValueError("Invoice not found")
    existing = session.scalar(
        select(CollectionStatement).where(CollectionStatement.request_id == request_id)
    )
    if existing:
        if (
            existing.invoice_id,
            existing.value,
            existing.source,
            existing.declared_on,
            existing.notes,
        ) != (invoice_id, value, source, declared_on, notes):
            raise ValueError("Conflicting declaration request ID")
        return existing
    statement = CollectionStatement(
        request_id=request_id,
        invoice_id=invoice_id,
        value=value,
        source=source,
        declared_on=declared_on,
        notes=notes,
    )
    session.add(statement)
    session.flush()
    return statement
