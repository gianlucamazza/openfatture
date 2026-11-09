from decimal import Decimal

import pytest

from openfatture.payment.application.collection_ledger import (
    allocate,
    money,
    record,
    reverse,
    total_paid,
)


def test_partial_receipt_reversal_and_replay(db_session, sample_fattura):
    receipt = record(db_session, request_id="receipt-1", amount="2000.00")
    entry = allocate(
        db_session,
        request_id="allocation-1",
        receipt_id=receipt.id,
        invoice_id=sample_fattura.id,
        amount="700.00",
    )
    assert (
        allocate(
            db_session,
            request_id="allocation-1",
            receipt_id=receipt.id,
            invoice_id=sample_fattura.id,
            amount="700.00",
        ).id
        == entry.id
    )
    assert total_paid(db_session, sample_fattura.id) == Decimal("700")
    reversal = reverse(
        db_session, request_id="reversal-1", entry_id=entry.id, amount="200", reason="Correction"
    )
    assert (
        reverse(
            db_session,
            request_id="reversal-1",
            entry_id=entry.id,
            amount="200",
            reason="Correction",
        ).id
        == reversal.id
    )
    assert total_paid(db_session, sample_fattura.id) == Decimal("500")
    assert receipt.allocated == Decimal("500")
    assert receipt.effective_date is None


@pytest.mark.parametrize("value", ["-1", "0", "NaN", "Infinity", "0.001"])
def test_reject_invalid_money(value):
    with pytest.raises(ValueError):
        money(value)


def test_allocation_cannot_exceed_invoice(db_session, sample_fattura):
    receipt = record(db_session, request_id="receipt", amount="2000")
    db_session.commit()
    with pytest.raises(ValueError, match="invoice balance"):
        allocate(
            db_session,
            request_id="allocation",
            receipt_id=receipt.id,
            invoice_id=sample_fattura.id,
            amount="1500",
        )
    db_session.rollback()
    assert total_paid(db_session, sample_fattura.id) == 0
