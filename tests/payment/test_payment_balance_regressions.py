"""Regression coverage for invoice balances and manual payment validation."""

from contextlib import nullcontext
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from openfatture.payment.application import payment_commands, payment_queries
from openfatture.storage.database.models import StatoPagamento


def test_paid_installment_does_not_settle_invoice(monkeypatch):
    invoice = SimpleNamespace(numero="1", anno=2026, totale=Decimal("2082.00"))
    payment = SimpleNamespace(
        id=1,
        importo=Decimal("500"),
        importo_pagato=Decimal("500"),
        saldo_residuo=Decimal("0"),
        stato=StatoPagamento.PAGATO,
        data_scadenza=date(2026, 8, 7),
        data_pagamento=None,
        modalita="Bonifico",
    )
    session = MagicMock()
    session.query.return_value.filter.return_value.first.return_value = invoice
    session.query.return_value.filter.return_value.all.return_value = [payment]
    monkeypatch.setattr(payment_queries, "db_session", lambda: nullcontext(session))
    result = payment_queries.get_payment_status(1)
    assert result["payment_status"] == "partially_paid"
    assert result["outstanding"] == 1582
    assert result["unscheduled_amount"] == 1582


@pytest.mark.parametrize(
    "due,paid", [(-1, 0), (100, -1), (100, 101), (1.001, 0), (float("inf"), 0), (100, float("nan"))]
)
@pytest.mark.parametrize("operation", ["create", "update"])
def test_reject_invalid_amounts_without_commit(monkeypatch, due, paid, operation):
    session = MagicMock()
    session.query.return_value.filter.return_value.first.return_value = SimpleNamespace(
        importo=Decimal("100"), importo_pagato=Decimal("0")
    )
    monkeypatch.setattr(payment_commands, "db_session", lambda: nullcontext(session))
    if operation == "create":
        result = payment_commands.create_manual_payment(1, due, "2026-08-07", paid)
    else:
        result = payment_commands.update_payment(1, importo=due, importo_pagato=paid)
    assert "error" in result
    session.commit.assert_not_called()
