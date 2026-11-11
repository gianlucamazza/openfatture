"""Branch coverage for the legacy cumulative-balance migration."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session, sessionmaker

from openfatture.payment.application.collection_migration import migrate_balances
from openfatture.payment.domain.models import BankAccount, BankTransaction
from openfatture.payment.domain.payment_allocation import PaymentAllocation
from openfatture.storage.database.models import (
    CollectionEntry,
    CollectionReceipt,
    Fattura,
    Pagamento,
)

SessionFactory = sessionmaker[Session]


def _payment(session: Session, invoice: Fattura, *, importo: str, pagato: str) -> Pagamento:
    payment = Pagamento(
        fattura_id=invoice.id,
        importo=Decimal(importo),
        importo_pagato=Decimal(pagato),
        data_scadenza=date(2026, 11, 1),
    )
    session.add(payment)
    session.flush()
    return payment


def _transaction(session: Session, *, amount: str, currency: str = "EUR") -> BankTransaction:
    account = BankAccount(name=f"Conto {currency}", currency=currency)
    session.add(account)
    session.flush()
    transaction = BankTransaction(
        id=uuid4(),
        account_id=account.id,
        date=date(2026, 1, 10),
        amount=Decimal(amount),
        description="Bonifico storico",
    )
    session.add(transaction)
    session.flush()
    return transaction


def _allocate(
    session: Session, payment: Pagamento, transaction: BankTransaction, amount: str
) -> None:
    session.add(
        PaymentAllocation(
            payment_id=payment.id, transaction_id=transaction.id, amount=Decimal(amount)
        )
    )
    session.flush()


def _ledger_entry(session: Session, payment: Pagamento, amount: str) -> None:
    receipt = CollectionReceipt(
        request_id=f"seed-{payment.id}",
        amount=Decimal(amount),
        allocated=Decimal(amount),
        origin="manual",
    )
    session.add(receipt)
    session.flush()
    session.add(
        CollectionEntry(
            request_id=f"seed-entry-{payment.id}",
            receipt_id=receipt.id,
            invoice_id=payment.fattura_id,
            payment_id=payment.id,
            amount=Decimal(amount),
        )
    )
    session.flush()


def _expect(session: Session, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        migrate_balances(session)


@pytest.mark.parametrize("pagato", ["-1", "1500"])
def test_rejects_out_of_range_balance(runtime_db: SessionFactory, seed_fattura: Fattura, pagato):
    with runtime_db() as session:
        _payment(session, seed_fattura, importo="1220", pagato=pagato)
        _expect(session, "Invalid historical payment balance")


def test_rejects_ledger_above_cached_balance(runtime_db: SessionFactory, seed_fattura: Fattura):
    with runtime_db() as session:
        payment = _payment(session, seed_fattura, importo="1220", pagato="100")
        _ledger_entry(session, payment, "200")
        _expect(session, "Ledger/cache mismatch for payment")


def test_rejects_partially_explained_balance(runtime_db: SessionFactory, seed_fattura: Fattura):
    with runtime_db() as session:
        payment = _payment(session, seed_fattura, importo="1220", pagato="300")
        _ledger_entry(session, payment, "100")
        _expect(session, "Unexplained payment change")


def test_rejects_non_positive_allocation(runtime_db: SessionFactory, seed_fattura: Fattura):
    with runtime_db() as session:
        payment = _payment(session, seed_fattura, importo="1220", pagato="100")
        _allocate(session, payment, _transaction(session, amount="100"), "0")
        _expect(session, "Invalid historical bank allocation")


def test_rejects_non_eur_allocation(runtime_db: SessionFactory, seed_fattura: Fattura):
    with runtime_db() as session:
        payment = _payment(session, seed_fattura, importo="1220", pagato="100")
        _allocate(session, payment, _transaction(session, amount="100", currency="USD"), "100")
        _expect(session, "non-EUR")


def test_reuses_bank_receipt_across_payments(runtime_db: SessionFactory, seed_fattura: Fattura):
    with runtime_db() as session:
        transaction = _transaction(session, amount="300")
        first = _payment(session, seed_fattura, importo="600", pagato="100")
        second = _payment(session, seed_fattura, importo="600", pagato="250")
        _allocate(session, first, transaction, "100")
        _allocate(session, second, transaction, "200")
        migrate_balances(session)
        receipts = session.query(CollectionReceipt).order_by(CollectionReceipt.id).all()
        assert [(r.origin, r.amount, r.allocated) for r in receipts] == [
            ("bank", Decimal("300"), Decimal("300")),
            ("opening", Decimal("50"), Decimal("50")),
        ]
        assert sum(e.amount for e in session.query(CollectionEntry).all()) == Decimal("350")


def test_rejects_allocations_above_transaction(runtime_db: SessionFactory, seed_fattura: Fattura):
    with runtime_db() as session:
        transaction = _transaction(session, amount="100")
        first = _payment(session, seed_fattura, importo="600", pagato="80")
        second = _payment(session, seed_fattura, importo="600", pagato="80")
        _allocate(session, first, transaction, "80")
        _allocate(session, second, transaction, "80")
        _expect(session, "exceeds transaction")


def test_rejects_allocations_above_balance(runtime_db: SessionFactory, seed_fattura: Fattura):
    with runtime_db() as session:
        payment = _payment(session, seed_fattura, importo="1220", pagato="50")
        _allocate(session, payment, _transaction(session, amount="100"), "80")
        _expect(session, "exceed cumulative balance")


def test_rejects_collections_above_invoice_total(runtime_db: SessionFactory, seed_fattura: Fattura):
    with runtime_db() as session:
        _payment(session, seed_fattura, importo="2000", pagato="1500")
        _expect(session, "inconsistent collections")


def test_skips_payments_without_balance(runtime_db: SessionFactory, seed_fattura: Fattura):
    with runtime_db() as session:
        _payment(session, seed_fattura, importo="1220", pagato="0")
        migrate_balances(session)
        assert session.query(CollectionReceipt).count() == 0
