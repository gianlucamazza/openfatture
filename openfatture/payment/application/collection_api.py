"""Public transactional collection use cases shared by CLI and AI tools."""

import hashlib
import json
from datetime import date
from decimal import Decimal
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from openfatture.payment.application import collection_ledger as ledger
from openfatture.payment.application.collection_migration import ensure_balances
from openfatture.platform.errors import describe_error
from openfatture.storage.database.models import (
    CollectionEntry,
    CollectionOperation,
    CollectionReceipt,
    CollectionStatement,
    Fattura,
    Pagamento,
    StatoPagamento,
)
from openfatture.storage.session import db_session


def run_operation(
    name: str, request_id: str, arguments: dict[str, Any], action: Any
) -> dict[str, Any]:
    if not request_id.strip() or len(request_id) > 64 or request_id.startswith("ledger:"):
        return {"error": "Invalid operation identifier", "error_code": "invalid_request"}
    fingerprint = hashlib.sha256(
        json.dumps([name, arguments], sort_keys=True, default=str).encode()
    ).hexdigest()
    with db_session() as session:
        try:
            previous = session.scalar(
                select(CollectionOperation).where(CollectionOperation.request_id == request_id)
            )
            if previous:
                if previous.fingerprint != fingerprint:
                    raise ValueError("Operation identifier already used with different parameters")
                return cast(dict[str, Any], json.loads(previous.result))
            operation = CollectionOperation(
                request_id=request_id, fingerprint=fingerprint, result="{}"
            )
            session.add(operation)
            session.flush()
            ensure_balances(session)
            result = {"success": True, "request_id": request_id, **action(session)}
            operation.result = json.dumps(result, default=str)
            session.commit()
            return result
        except Exception as exc:
            session.rollback()
            # A parallel identical request may have committed while we waited.
            previous = session.scalar(
                select(CollectionOperation).where(CollectionOperation.request_id == request_id)
            )
            if previous and previous.fingerprint == fingerprint:
                return cast(dict[str, Any], json.loads(previous.result))
            return {
                "success": False,
                "request_id": request_id,
                "error": describe_error(exc),
                "error_code": "collection_operation_failed",
            }


def record_collection(
    amount: str,
    request_id: str,
    invoice_id: int | None = None,
    payment_id: int | None = None,
    effective_date: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    def action(session: Session) -> dict[str, Any]:
        receipt = ledger.record(
            session,
            request_id=request_id + ":receipt",
            amount=amount,
            effective_date=date.fromisoformat(effective_date) if effective_date else None,
            notes=notes,
        )
        if invoice_id is not None:
            ledger.allocate(
                session,
                request_id=request_id + ":allocation",
                receipt_id=receipt.id,
                invoice_id=invoice_id,
                payment_id=payment_id,
                amount=amount,
            )
        elif payment_id is not None:
            raise ValueError("An invoice is required when selecting an installment")
        return {
            "receipt_id": receipt.id,
            "amount": str(receipt.amount),
            "allocated": str(receipt.allocated),
            "available": str(receipt.amount - receipt.allocated),
        }

    return run_operation(
        "record",
        request_id,
        {
            "amount": amount,
            "invoice_id": invoice_id,
            "payment_id": payment_id,
            "effective_date": effective_date,
            "notes": notes,
        },
        action,
    )


def allocate_collection(
    receipt_id: int, invoice_id: int, amount: str, request_id: str, payment_id: int | None = None
) -> dict[str, Any]:
    return run_operation(
        "allocate",
        request_id,
        {
            "receipt_id": receipt_id,
            "invoice_id": invoice_id,
            "amount": amount,
            "payment_id": payment_id,
        },
        lambda s: {
            "entry_id": ledger.allocate(
                s,
                request_id=request_id + ":entry",
                receipt_id=receipt_id,
                invoice_id=invoice_id,
                payment_id=payment_id,
                amount=amount,
            ).id
        },
    )


def reverse_collection(entry_id: int, amount: str, reason: str, request_id: str) -> dict[str, Any]:
    return run_operation(
        "reverse",
        request_id,
        {"entry_id": entry_id, "amount": amount, "reason": reason},
        lambda s: {
            "entry_id": ledger.reverse(
                s, request_id=request_id + ":entry", entry_id=entry_id, amount=amount, reason=reason
            ).id
        },
    )


def declare_collection_status(
    invoice_id: int,
    value: str,
    source: str,
    request_id: str,
    declared_on: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    return run_operation(
        "declare",
        request_id,
        {
            "invoice_id": invoice_id,
            "value": value,
            "source": source,
            "declared_on": declared_on,
            "notes": notes,
        },
        lambda s: {
            "statement_id": ledger.declare_status(
                s,
                request_id=request_id + ":statement",
                invoice_id=invoice_id,
                value=value,
                source=source,
                declared_on=date.fromisoformat(declared_on) if declared_on else None,
                notes=notes,
            ).id
        },
    )


def get_collections(invoice_id: int | None = None) -> dict[str, Any]:
    with db_session() as session:
        receipt_query = select(CollectionReceipt).order_by(CollectionReceipt.id)
        if invoice_id is not None:
            receipt_query = receipt_query.where(
                CollectionReceipt.id.in_(
                    select(CollectionEntry.receipt_id).where(
                        CollectionEntry.invoice_id == invoice_id
                    )
                )
            )
        receipts = session.scalars(receipt_query).all()
        entries_query = select(CollectionEntry).order_by(CollectionEntry.id)
        statements_query = select(CollectionStatement).order_by(CollectionStatement.id)
        if invoice_id is not None:
            entries_query = entries_query.where(CollectionEntry.invoice_id == invoice_id)
            statements_query = statements_query.where(CollectionStatement.invoice_id == invoice_id)
        return {
            "receipts": [
                {
                    "id": r.id,
                    "amount": str(r.amount),
                    "allocated": str(r.allocated),
                    "available": str(r.amount - r.allocated),
                    "origin": r.origin,
                    "date": r.effective_date.isoformat() if r.effective_date else None,
                }
                for r in receipts
            ],
            "entries": [
                {
                    "id": e.id,
                    "receipt_id": e.receipt_id,
                    "invoice_id": e.invoice_id,
                    "payment_id": e.payment_id,
                    "amount": str(e.amount),
                    "reverses_id": e.reverses_id,
                    "notes": e.notes,
                }
                for e in session.scalars(entries_query)
            ],
            "statements": [
                {
                    "id": st.id,
                    "invoice_id": st.invoice_id,
                    "value": st.value,
                    "source": st.source,
                    "declared_on": st.declared_on.isoformat() if st.declared_on else None,
                }
                for st in session.scalars(statements_query)
            ],
        }


def create_payment(
    fattura_id: int,
    importo: float,
    data_scadenza: str | None = None,
    importo_pagato: float = 0.0,
    data_pagamento: str | None = None,
    modalita: str = "bonifico",
    request_id: str | None = None,
) -> dict[str, Any]:
    try:
        due, paid = ledger.money(str(importo)), Decimal(str(importo_pagato))
        if not paid.is_finite() or paid < 0 or paid > due or paid != paid.quantize(Decimal(".01")):
            raise ValueError("Invalid paid amount")
    except Exception as exc:
        return {"error": describe_error(exc)}
    key = request_id or str(uuid4())

    def action(session: Session) -> dict[str, Any]:
        due, paid = ledger.money(str(importo)), Decimal(str(importo_pagato))
        if not paid.is_finite() or paid < 0 or paid > due or paid != paid.quantize(Decimal(".01")):
            raise ValueError("Invalid paid amount")
        invoice = session.get(Fattura, fattura_id)
        if invoice is None:
            raise ValueError("Invoice not found")
        scheduled = session.scalar(
            select(func.coalesce(func.sum(Pagamento.importo), 0)).where(
                Pagamento.fattura_id == fattura_id
            )
        ) or Decimal("0")
        if scheduled + due > invoice.totale:
            raise ValueError("Installments exceed invoice total")
        deadline = date.fromisoformat(data_scadenza) if data_scadenza else None
        payment = Pagamento(
            fattura_id=fattura_id,
            importo=due,
            importo_pagato=Decimal("0"),
            data_scadenza=deadline,
            modalita=modalita,
            giorni_scadenza=max((deadline - invoice.data_emissione).days, 0) if deadline else 0,
        )
        session.add(payment)
        session.flush()
        if paid:
            receipt = ledger.record(
                session,
                request_id=key + ":receipt",
                amount=str(paid),
                effective_date=date.fromisoformat(data_pagamento) if data_pagamento else None,
            )
            ledger.allocate(
                session,
                request_id=key + ":entry",
                receipt_id=receipt.id,
                invoice_id=fattura_id,
                payment_id=payment.id,
                amount=str(paid),
            )
        set_payment_status(payment)
        return {
            "payment_id": payment.id,
            "fattura_id": fattura_id,
            "importo": float(due),
            "importo_pagato": float(paid),
            "saldo_residuo": float(due - paid),
            "stato": payment.stato.value,
            "message": "Payment schedule created",
        }

    return run_operation("create-payment", key, locals_without_action(locals()), action)


def locals_without_action(values: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in values.items() if k not in {"action", "key", "request_id"}}


def set_payment_status(payment: Pagamento) -> None:
    if payment.importo_pagato >= payment.importo:
        payment.stato = StatoPagamento.PAGATO
    elif payment.importo_pagato > 0:
        payment.stato = StatoPagamento.PAGATO_PARZIALE
    elif payment.data_scadenza and payment.data_scadenza < date.today():
        payment.stato = StatoPagamento.SCADUTO
    else:
        payment.stato = StatoPagamento.DA_PAGARE


def update_payment(
    payment_id: int,
    importo: float | None = None,
    importo_pagato: float | None = None,
    data_scadenza: str | None = None,
    data_pagamento: str | None = None,
    modalita: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    try:
        due = ledger.money(str(importo)) if importo is not None else None
        paid = Decimal(str(importo_pagato)) if importo_pagato is not None else None
        if paid is not None and (
            not paid.is_finite()
            or paid < 0
            or paid != paid.quantize(Decimal(".01"))
            or (due is not None and paid > due)
        ):
            raise ValueError("Invalid paid amount")
    except Exception as exc:
        return {"error": describe_error(exc)}
    key = request_id or str(uuid4())

    def action(session: Session) -> dict[str, Any]:
        payment = session.get(Pagamento, payment_id)
        if payment is None:
            raise ValueError("Payment not found")
        if importo is not None:
            due = ledger.money(str(importo))
            if due < payment.importo_pagato:
                raise ValueError("Installment amount cannot be lower than active receipts")
            other = session.scalar(
                select(func.coalesce(func.sum(Pagamento.importo), 0)).where(
                    Pagamento.fattura_id == payment.fattura_id, Pagamento.id != payment_id
                )
            ) or Decimal("0")
            if other + due > payment.fattura.totale:
                raise ValueError("Installments exceed invoice total")
            payment.importo = due
            session.flush()
        if importo_pagato is not None:
            desired = Decimal(str(importo_pagato))
            if (
                not desired.is_finite()
                or desired < 0
                or desired > payment.importo
                or desired != desired.quantize(Decimal(".01"))
            ):
                raise ValueError("Invalid paid amount")
            difference = desired - payment.importo_pagato
            if difference > 0:
                receipt = ledger.record(
                    session,
                    request_id=key + ":receipt",
                    amount=str(difference),
                    effective_date=date.fromisoformat(data_pagamento) if data_pagamento else None,
                )
                ledger.allocate(
                    session,
                    request_id=key + ":entry",
                    receipt_id=receipt.id,
                    invoice_id=payment.fattura_id,
                    payment_id=payment_id,
                    amount=str(difference),
                )
            elif difference < 0:
                remaining = -difference
                entries = session.scalars(
                    select(CollectionEntry)
                    .join(CollectionReceipt)
                    .where(
                        CollectionEntry.payment_id == payment_id,
                        CollectionEntry.amount > 0,
                        CollectionReceipt.origin.in_(["manual", "opening"]),
                    )
                    .order_by(CollectionEntry.id.desc())
                ).all()
                for entry in entries:
                    already = session.scalar(
                        select(func.coalesce(func.sum(CollectionEntry.amount), 0)).where(
                            CollectionEntry.reverses_id == entry.id
                        )
                    ) or Decimal("0")
                    amount = min(remaining, entry.amount + already)
                    if amount > 0:
                        ledger.reverse(
                            session,
                            request_id=key + f":reverse:{entry.id}",
                            entry_id=entry.id,
                            amount=str(amount),
                            reason="Manual cumulative correction",
                        )
                        remaining -= amount
                    if remaining == 0:
                        break
                if remaining:
                    raise ValueError(
                        "Cannot change bank allocations through a manual cumulative update"
                    )
        if data_scadenza is not None:
            payment.data_scadenza = date.fromisoformat(data_scadenza) if data_scadenza else None
        if data_pagamento is not None:
            payment.data_pagamento = date.fromisoformat(data_pagamento) if data_pagamento else None
        if modalita is not None:
            payment.modalita = modalita
        set_payment_status(payment)
        return {
            "payment_id": payment.id,
            "fattura_id": payment.fattura_id,
            "importo": float(payment.importo),
            "importo_pagato": float(payment.importo_pagato),
            "saldo_residuo": float(payment.saldo_residuo),
            "stato": payment.stato.value,
            "message": "Payment updated with ledger evidence",
        }

    return run_operation("update-payment", key, locals_without_action(locals()), action)


def delete_payment(payment_id: int) -> dict[str, Any]:
    with db_session() as session:
        try:
            payment = session.get(Pagamento, payment_id)
            if payment is None:
                raise ValueError("Payment not found")
            if payment.importo_pagato or session.scalar(
                select(CollectionEntry.id).where(CollectionEntry.payment_id == payment_id).limit(1)
            ):
                raise ValueError("Cannot delete a payment with collection history")
            from openfatture.payment.domain.models import BankTransaction

            if session.scalar(
                select(BankTransaction.id)
                .where(BankTransaction.matched_payment_id == payment_id)
                .limit(1)
            ):
                raise ValueError("Cannot delete a payment linked to bank movements")
            session.delete(payment)
            session.commit()
            return {"success": True, "payment_id": payment_id}
        except Exception as exc:
            session.rollback()
            return {"error": describe_error(exc)}


def record_bank_collection(transaction_id: str, request_id: str) -> dict[str, Any]:
    def action(session: Session) -> dict[str, Any]:
        from openfatture.payment.application.bank_collections import bank_receipt
        from openfatture.payment.domain.models import BankTransaction

        transaction = session.get(BankTransaction, UUID(transaction_id))
        if transaction is None:
            raise ValueError("Bank transaction not found")
        receipt = bank_receipt(session, transaction)
        return {
            "receipt_id": receipt.id,
            "amount": str(receipt.amount),
            "available": str(receipt.amount - receipt.allocated),
        }

    return run_operation("bank-receipt", request_id, {"transaction_id": transaction_id}, action)


def allocate_collection_batch(
    receipt_id: int, allocations_json: str, request_id: str
) -> dict[str, Any]:
    def action(session: Session) -> dict[str, Any]:
        allocations = json.loads(allocations_json)
        if not isinstance(allocations, list) or not allocations:
            raise ValueError("Require a nonempty array of allocations")
        entries = []
        for index, item in enumerate(sorted(allocations, key=lambda item: int(item["invoice_id"]))):
            entry = ledger.allocate(
                session,
                request_id=request_id + f":entry:{index}",
                receipt_id=receipt_id,
                invoice_id=int(item["invoice_id"]),
                payment_id=item.get("payment_id"),
                amount=str(item["amount"]),
            )
            entries.append(entry.id)
        return {"entry_ids": entries}

    return run_operation(
        "allocate-batch",
        request_id,
        {"receipt_id": receipt_id, "allocations": allocations_json},
        action,
    )
