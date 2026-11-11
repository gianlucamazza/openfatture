"""What the assistant's query tools return for the model to act on."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from openfatture.billing.application import client_queries, invoice_queries, report_queries
from openfatture.storage.database.models import (
    Cliente,
    Fattura,
    RigaFattura,
    StatoFattura,
    TipoDocumento,
)


def test_search_treats_like_wildcards_literally(
    runtime_session: Session, seed_fattura: Fattura, seed_cliente: Cliente
) -> None:
    seed_fattura.note = "rif_2026%"
    runtime_session.commit()
    assert invoice_queries.search_invoices(query="rif_2026%")["count"] == 1
    # "_" and "%" are not wildcards: "rifx2026" does not match "rif_2026".
    assert invoice_queries.search_invoices(query="rifx")["count"] == 0
    seed_cliente.denominazione = "Acme_Corp"
    runtime_session.commit()
    assert client_queries.search_clients(query="acme_")["count"] == 1
    assert client_queries.search_clients(query="acme%corp")["count"] == 0


def test_invoice_details_identify_each_line(seed_fattura: Fattura) -> None:
    righe = invoice_queries.get_invoice_details(seed_fattura.id)["righe"]
    riga = seed_fattura.righe[0]
    assert righe[0]["id"] == riga.id
    assert righe[0]["numero_riga"] == 1
    assert "natura" in righe[0]


def test_credit_notes_reduce_vat_and_client_reports(
    runtime_session: Session, seed_fattura: Fattura, seed_cliente: Cliente
) -> None:
    seed_fattura.stato = StatoFattura.INVIATA
    credit = Fattura(
        numero="2",
        anno=2025,
        data_emissione=date(2025, 2, 1),
        cliente_id=seed_cliente.id,
        tipo_documento=TipoDocumento.TD04,
        stato=StatoFattura.INVIATA,
        imponibile=Decimal("100.00"),
        iva=Decimal("22.00"),
        totale=Decimal("122.00"),
    )
    runtime_session.add(credit)
    runtime_session.flush()
    runtime_session.add(
        RigaFattura(
            fattura_id=credit.id,
            numero_riga=1,
            descrizione="Storno parziale",
            quantita=Decimal("1"),
            prezzo_unitario=Decimal("100.00"),
            aliquota_iva=Decimal("22.00"),
            imponibile=Decimal("100.00"),
            iva=Decimal("22.00"),
            totale=Decimal("122.00"),
        )
    )
    runtime_session.commit()

    vat = report_queries.generate_vat_report(anno=2025)
    assert vat["total_imponibile"] == 900.0
    assert vat["total_iva"] == 198.0
    assert vat["by_vat_rate"] == [{"vat_rate": 22.0, "imponibile": 900.0, "iva": 198.0}]
    clients = report_queries.generate_client_report(anno=2025)
    assert clients["clients"][0]["total_revenue"] == 1098.0
