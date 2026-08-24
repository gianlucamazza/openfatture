"""Tests for payment due summary utilities."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from openfatture.payment.application.services.payment_overview import (
    PaymentDueEntry,
    PaymentDueSummary,
    _client_name,
    _compute_residual,
    collect_payment_due_summary,
)


class DummyPayment:
    """Simple stand-in object for residual calculations."""

    def __init__(
        self,
        *,
        saldo_residuo=None,
        importo=Decimal("0.00"),
        importo_pagato=Decimal("0.00"),
    ):
        self.saldo_residuo = saldo_residuo
        self.importo = importo
        self.importo_pagato = importo_pagato
        self.importo_da_pagare = importo


@pytest.mark.parametrize(
    "payment, expected",
    [
        (DummyPayment(saldo_residuo=Decimal("150.50")), Decimal("150.50")),
        (DummyPayment(saldo_residuo="-10.00"), Decimal("0.00")),
        (
            DummyPayment(
                saldo_residuo="invalid", importo=Decimal("200.00"), importo_pagato=Decimal("50.00")
            ),
            Decimal("150.00"),
        ),
        (
            DummyPayment(importo=Decimal("75.00"), importo_pagato=Decimal("80.00")),
            Decimal("0.00"),
        ),
    ],
)
def test_compute_residual_handles_various_inputs(payment, expected):
    """_compute_residual should normalise saldo / importo combinations."""
    assert _compute_residual(payment) == expected


@pytest.mark.parametrize(
    "fattura_fields, expected",
    [
        ({"denominazione": "ACME Spa"}, "ACME Spa"),
        ({"denominazione": None, "nome": "Mario", "cognome": "Rossi"}, "Mario Rossi"),
        ({}, "N/D"),
        (None, "N/D"),
    ],
)
def test_client_name_variants(fattura_fields, expected, mocker):
    """_client_name should derive sensible labels from fattura/cliente data."""
    if fattura_fields is None:
        assert _client_name(None) == expected
        return

    fattura = mocker.Mock()
    cliente = mocker.Mock(**fattura_fields)
    fattura.cliente = cliente if fattura_fields else None
    assert _client_name(fattura) == expected


def test_collect_payment_due_summary_groups_entries(db_session, sample_cliente):
    """collect_payment_due_summary should bucket payments by urgency and aggregate totals."""
    from openfatture.storage.database.models import (
        Fattura,
        Pagamento,
        StatoFattura,
        StatoPagamento,
    )

    today = date.today()

    fattura = Fattura(
        numero="42",
        anno=today.year,
        data_emissione=today,
        cliente_id=sample_cliente.id,
        stato=StatoFattura.DA_INVIARE,
        imponibile=Decimal("1000.00"),
        iva=Decimal("220.00"),
        totale=Decimal("1220.00"),
    )
    db_session.add(fattura)
    db_session.flush()

    payments = [
        Pagamento(
            fattura_id=fattura.id,
            importo=Decimal("500.00"),
            importo_pagato=Decimal("0.00"),
            data_scadenza=today - timedelta(days=3),
            stato=StatoPagamento.DA_PAGARE,
        ),
        Pagamento(
            fattura_id=fattura.id,
            importo=Decimal("300.00"),
            importo_pagato=Decimal("50.00"),
            data_scadenza=today + timedelta(days=5),
            stato=StatoPagamento.DA_PAGARE,
        ),
        Pagamento(
            fattura_id=fattura.id,
            importo=Decimal("200.00"),
            importo_pagato=Decimal("0.00"),
            data_scadenza=today + timedelta(days=30),
            stato=StatoPagamento.DA_PAGARE,
        ),
        Pagamento(
            fattura_id=fattura.id,
            importo=Decimal("180.00"),
            importo_pagato=Decimal("0.00"),
            data_scadenza=today + timedelta(days=31),
            stato=StatoPagamento.DA_PAGARE,
        ),
        Pagamento(
            fattura_id=fattura.id,
            importo=Decimal("120.00"),
            importo_pagato=Decimal("120.00"),
            data_scadenza=today,
            stato=StatoPagamento.DA_PAGARE,
        ),
    ]

    db_session.add_all(payments)
    db_session.commit()

    summary = collect_payment_due_summary(db_session, window_days=7, max_upcoming=1)

    assert isinstance(summary, PaymentDueSummary)
    assert len(summary.overdue) == 1
    assert len(summary.due_soon) == 1
    assert len(summary.upcoming) == 1  # second upcoming should be hidden
    assert summary.hidden_upcoming == 1

    overdue_entry = summary.overdue[0]
    assert isinstance(overdue_entry, PaymentDueEntry)
    assert overdue_entry.residual == Decimal("500.00")
    assert overdue_entry.client_name == sample_cliente.denominazione

    due_soon_entry = summary.due_soon[0]
    assert due_soon_entry.residual == Decimal("250.00")
    assert due_soon_entry.days_delta == 5

    assert summary.total_outstanding == Decimal("1130.00")
