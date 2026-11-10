"""Stored totals, XML and PDF describe the same document.

Covers the forfettario case: 0% lines with natura N2.2, INPS contribution
(TC22 4%), automatic stamp duty and its N1 re-charge line. The test cedente is
in the forfettario regime (RF19).
"""

import re
from decimal import Decimal

import pytest

from openfatture.billing.application import (
    cassa_ops,
    invoice_commands,
    nota_credito_ops,
    preventivo_ops,
)
from openfatture.billing.application.totals import (
    amount_due,
    bollo_due,
    check_vat,
    resolve_vat,
)
from openfatture.pdf.generator import PDFGenerator, PDFGeneratorConfig
from openfatture.pdf.templates.base import summary_rows
from openfatture.platform.config import get_settings
from openfatture.sdi.validator.xsd_validator import FatturaPAValidator
from openfatture.sdi.xml_builder.fatturapa import FatturaPABuilder
from openfatture.storage.database.models import Fattura, RigaFattura

D = Decimal


def _riepilogo(xml: str) -> list[tuple[str | None, str, str]]:
    rows = []
    for block in re.findall(r"<DatiRiepilogo>.*?</DatiRiepilogo>", xml, re.S):
        natura = _tag(block, "Natura")
        rows.append(
            (
                natura[0] if natura else None,
                _tag(block, "ImponibileImporto")[0],
                _tag(block, "Imposta")[0],
            )
        )
    return rows


def _tag(xml: str, name: str) -> list[str]:
    return re.findall(rf"<{name}>(.*?)</{name}>", xml)


@pytest.fixture
def forfettario_invoice(runtime_session, seed_cliente) -> int:
    """2000 compensi + INPS 4% + stamp duty charged with an N1 line = 2082."""
    invoice_id = invoice_commands.create_invoice(cliente_id=seed_cliente.id, anno=2026)[
        "invoice_id"
    ]
    assert invoice_commands.create_riga(
        fattura_id=invoice_id, descrizione="Consulenza", quantita=1, prezzo_unitario=2000
    ).get("success")
    assert cassa_ops.set_cassa_previdenziale(invoice_id, "TC22", 4).get("success")
    assert invoice_commands.create_riga(
        fattura_id=invoice_id,
        descrizione="Rivalsa imposta di bollo",
        quantita=1,
        prezzo_unitario=2,
        unita_misura="",
        natura="N1",
    ).get("success")
    return int(invoice_id)


def test_forfettario_invoice_totals(runtime_session, forfettario_invoice):
    fattura = runtime_session.get(Fattura, forfettario_invoice)
    righe = sorted(fattura.righe, key=lambda r: r.numero_riga)
    assert [(r.aliquota_iva, r.natura) for r in righe] == [(D("0.00"), "N2.2"), (D("0.00"), "N1")]
    cassa = fattura.cassa_previdenziale[0]
    # The N1 line is not subject to the contribution.
    assert (cassa.imponibile_cassa, cassa.importo_contributo_cassa) == (D("2000.00"), D("80.00"))
    assert (cassa.aliquota_iva, cassa.natura) == (D("0.00"), "N2.2")
    assert (fattura.imponibile, fattura.iva, fattura.totale) == (D("2082.00"), 0, D("2082.00"))
    assert fattura.importo_bollo == D("2.00")


def test_xml_matches_stored_totals(runtime_session, forfettario_invoice):
    fattura = runtime_session.get(Fattura, forfettario_invoice)
    xml = FatturaPABuilder(get_settings()).build(fattura)

    assert FatturaPAValidator().validate(xml) == (True, None)
    assert _riepilogo(xml) == [("N1", "2.00", "0.00"), ("N2.2", "2080.00", "0.00")]
    assert _tag(xml, "ImportoContributoCassa") == ["80.00"]
    assert _tag(xml, "ImportoBollo") == ["2.00"]
    assert _tag(xml, "ImportoTotaleDocumento") == ["2082.00"]
    assert _tag(xml, "ImportoPagamento") == ["2082.00"]
    # Every 0% line carries its natura; the empty unit of measure is omitted.
    assert _tag(xml, "Natura").count("N2.2") == 3  # line, cassa, riepilogo
    assert "<UnitaMisura></UnitaMisura>" not in xml and "<UnitaMisura/>" not in xml
    assert "EsigibilitaIVA" not in xml


def test_pdf_shows_the_xml_amounts(runtime_session, forfettario_invoice):
    fattura = runtime_session.get(Fattura, forfettario_invoice)
    data = PDFGenerator(PDFGeneratorConfig())._fattura_to_dict(fattura)

    assert [(r["natura"], r["imponibile"], r["imposta"]) for r in data["riepilogo"]] == [
        ("N1", D("2.00"), D("0.00")),
        ("N2.2", D("2080.00"), D("0.00")),
    ]
    # The stamp duty is in the N1 line: no extra row, the total is what is paid.
    assert summary_rows(data) == [
        ("Imponibile", D("2082.00")),
        ("IVA", D("0.00")),
        ("Totale documento", D("2082.00")),
    ]
    assert data["importo_da_pagare"] == D("2082.00")


def test_editing_a_line_keeps_the_contribution(runtime_session, forfettario_invoice):
    fattura = runtime_session.get(Fattura, forfettario_invoice)
    first = min(fattura.righe, key=lambda r: r.numero_riga)
    assert invoice_commands.update_riga(riga_id=first.id, prezzo_unitario=300).get("success")

    runtime_session.expire_all()
    fattura = runtime_session.get(Fattura, forfettario_invoice)
    assert fattura.cassa_previdenziale[0].importo_contributo_cassa == D("12.00")
    assert fattura.totale == D("314.00")

    assert cassa_ops.set_cassa_previdenziale(forfettario_invoice, None).get("success")
    runtime_session.expire_all()
    assert runtime_session.get(Fattura, forfettario_invoice).totale == D("302.00")


def test_credit_note_copies_the_contribution(runtime_session, forfettario_invoice):
    result = nota_credito_ops.create_nota_credito_from_fattura(fattura_id=forfettario_invoice)
    assert result.get("success"), result

    runtime_session.expire_all()
    credit = runtime_session.get(Fattura, result["nota_credito_id"])
    assert credit.cassa_previdenziale[0].importo_contributo_cassa == D("80.00")
    assert (credit.totale, credit.importo_bollo) == (D("2082.00"), D("2.00"))
    assert FatturaPAValidator().validate(FatturaPABuilder(get_settings()).build(credit))[0]


def test_stamp_duty_threshold(runtime_session, seed_cliente):
    invoice_id = invoice_commands.create_invoice(cliente_id=seed_cliente.id, anno=2026)[
        "invoice_id"
    ]
    invoice_commands.create_riga(
        fattura_id=invoice_id, descrizione="A", quantita=1, prezzo_unitario=77.47
    )
    assert runtime_session.get(Fattura, invoice_id).importo_bollo == 0

    invoice_commands.create_riga(
        fattura_id=invoice_id, descrizione="B", quantita=1, prezzo_unitario=0.01
    )
    runtime_session.expire_all()
    assert runtime_session.get(Fattura, invoice_id).importo_bollo == D("2.00")

    # Taxable lines never make the stamp duty due.
    taxed = [RigaFattura(aliquota_iva=D("22"), natura=None, imponibile=D("1000"))]
    assert bollo_due(taxed) == 0


def test_vat_and_natura_rules(runtime_session, seed_cliente):
    assert resolve_vat(None, None, "RF19") == (D("0"), "N2.2")
    assert resolve_vat(None, None, "RF01") == (D("22"), None)
    assert check_vat(D("0"), None) is not None
    assert check_vat(D("22"), "N2.2") is not None
    assert check_vat(D("0"), "N9") is not None
    assert amount_due(D("1220.00"), D("200.00")) == D("1020.00")

    invoice_id = invoice_commands.create_invoice(cliente_id=seed_cliente.id, anno=2026)[
        "invoice_id"
    ]
    refused = invoice_commands.create_riga(
        fattura_id=invoice_id,
        descrizione="A",
        quantita=1,
        prezzo_unitario=10,
        natura="N2.2",
        aliquota_iva=22,
    )
    assert "only allowed with a 0% VAT rate" in refused["error"]

    created = invoice_commands.create_riga(
        fattura_id=invoice_id, descrizione="A", quantita=1, prezzo_unitario=10, aliquota_iva=22
    )
    # Switching to 0% picks the forfettario natura; back to 22% clears it.
    assert invoice_commands.update_riga(riga_id=created["riga_id"], aliquota_iva=0).get("success")
    runtime_session.expire_all()
    assert runtime_session.get(RigaFattura, created["riga_id"]).natura == "N2.2"
    assert invoice_commands.update_riga(riga_id=created["riga_id"], aliquota_iva=22).get("success")
    runtime_session.expire_all()
    assert runtime_session.get(RigaFattura, created["riga_id"]).natura is None


def test_quote_conversion_keeps_natura(runtime_session, seed_cliente):
    quote = preventivo_ops.create_preventivo(
        cliente_id=seed_cliente.id,
        righe=[{"descrizione": "Corso", "quantita": 1, "prezzo_unitario": 960}],
    )
    assert quote.get("success"), quote
    assert (
        preventivo_ops.get_preventivo_details(quote["preventivo_id"])["righe"][0]["natura"]
        == "N2.2"
    )
    assert preventivo_ops.update_preventivo_status(quote["preventivo_id"], "accettato").get(
        "success"
    )
    converted = preventivo_ops.convert_preventivo_to_invoice(quote["preventivo_id"])
    assert converted.get("success"), converted

    runtime_session.expire_all()
    fattura = runtime_session.get(Fattura, converted["fattura_id"])
    assert fattura.righe[0].natura == "N2.2"
    assert fattura.importo_bollo == D("2.00")
    assert FatturaPAValidator().validate(FatturaPABuilder(get_settings()).build(fattura))[0]
