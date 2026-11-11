"""The yearly invoice situation computed from the database, not by the model."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from openfatture.billing.application.invoice_queries import get_invoice_stats
from openfatture.billing.application.report_queries import invoice_situation
from openfatture.storage.database.models import (
    Fattura,
    Pagamento,
    StatoFattura,
    TipoDocumento,
)

YEAR = 2026


def _invoice(session, cliente, numero: str, totale: str, **fields) -> Fattura:
    fattura = Fattura(
        numero=numero,
        anno=YEAR,
        data_emissione=date(YEAR, 1, int(numero) % 28 + 1),
        cliente_id=cliente.id,
        tipo_documento=fields.pop("tipo_documento", TipoDocumento.TD01),
        stato=fields.pop("stato", StatoFattura.INVIATA),
        imponibile=Decimal(totale),
        iva=Decimal("0.00"),
        totale=Decimal(totale),
        **fields,
    )
    session.add(fattura)
    session.flush()
    return fattura


def _payment(session, fattura, importo: str, pagato: str, scadenza: date | None) -> None:
    session.add(
        Pagamento(
            fattura_id=fattura.id,
            modalita="MP05",
            importo=Decimal(importo),
            importo_pagato=Decimal(pagato),
            data_scadenza=scadenza,
        )
    )


def test_situation_totals_per_document_and_clients(runtime_session, seed_cliente) -> None:
    past = date.today() - timedelta(days=30)
    paid = _invoice(runtime_session, seed_cliente, "1", "1000.00")
    _payment(runtime_session, paid, "1000.00", "1000.00", past)
    partial = _invoice(runtime_session, seed_cliente, "2", "500.00", issued_elsewhere=True)
    _payment(runtime_session, partial, "500.00", "200.00", past)
    _invoice(runtime_session, seed_cliente, "3", "300.00")
    _invoice(runtime_session, seed_cliente, "4", "999.00", stato=StatoFattura.BOZZA)
    _invoice(runtime_session, seed_cliente, "5", "100.00", tipo_documento=TipoDocumento.TD04)
    runtime_session.commit()

    result = invoice_situation(YEAR)

    assert result["documents_count"] == 4
    assert result["excluded_drafts"] == 1
    assert result["historical_count"] == 1
    assert result["totals"] == {
        "invoiced": 1800.0,
        "credit_notes": 100.0,
        "net_invoiced": 1700.0,
        "collected": 1200.0,
        "outstanding": 600.0,
        "overdue": 300.0,
        "unscheduled": 300.0,
    }
    rows = {row["numero"]: row for row in result["documents"]}
    assert rows["1/2026"]["payment_status"] == "fully_paid"
    assert rows["2/2026"]["payment_status"] == "partially_paid"
    assert rows["2/2026"]["overdue"] == 300.0
    assert rows["3/2026"]["payment_status"] == "no_payment_record"
    assert rows["5/2026"]["nota_credito"] is True
    assert "4/2026" not in rows
    assert result["clients"] == [{"cliente": "Acme Corporation", "totale": 1800.0, "quota": 100.0}]


def test_situation_agrees_with_invoice_stats(runtime_session, seed_cliente) -> None:
    first = _invoice(runtime_session, seed_cliente, "1", "1220.00")
    _payment(runtime_session, first, "1220.00", "220.00", None)
    _invoice(runtime_session, seed_cliente, "2", "80.00")
    runtime_session.commit()

    totals = invoice_situation(YEAR)["totals"]
    stats = get_invoice_stats(YEAR)

    assert totals["collected"] == stats["incassato_totale"]
    assert totals["outstanding"] == stats["residuo_totale"]


def test_situation_is_not_capped_like_search(runtime_session, seed_cliente) -> None:
    for numero in range(1, 121):
        _invoice(runtime_session, seed_cliente, str(numero), "10.00")
    runtime_session.commit()

    result = invoice_situation(YEAR)

    assert result["documents_count"] == 120
    assert result["totals"]["invoiced"] == 1200.0
    assert result["documents"][0]["numero"] == "1/2026"
    assert result["documents"][-1]["numero"] == "120/2026"


def test_empty_year(runtime_db) -> None:
    result = invoice_situation(YEAR)
    assert result["documents_count"] == 0
    assert result["documents"] == []
    assert result["totals"]["invoiced"] == 0.0
