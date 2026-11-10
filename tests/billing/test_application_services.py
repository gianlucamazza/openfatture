"""Behaviour of the billing application services on a real database."""

import re
from decimal import Decimal

from openfatture.billing.application import (
    client_commands,
    invoice_commands,
    nota_credito_ops,
    preventivo_ops,
    prodotto_ops,
)
from openfatture.platform.config import get_settings
from openfatture.sdi.xml_builder.fatturapa import FatturaPABuilder
from openfatture.storage.database.models import Fattura, Preventivo


def _invoice_with_lines(cliente_id: int, lines: list[tuple[str, float, float]]) -> int:
    invoice_id = invoice_commands.create_invoice(cliente_id=cliente_id, anno=2026)["invoice_id"]
    for descrizione, quantita, prezzo in lines:
        result = invoice_commands.create_riga(
            fattura_id=invoice_id,
            descrizione=descrizione,
            quantita=quantita,
            prezzo_unitario=prezzo,
            aliquota_iva=22,
        )
        assert result.get("success"), result
    return invoice_id


def _consistent(document) -> None:
    assert document.totale == document.imponibile + document.iva
    for amount in (document.imponibile, document.iva, document.totale):
        assert amount == amount.quantize(Decimal("0.01"))


# --- Totals ---------------------------------------------------------------


def test_invoice_totals_stay_consistent_through_edits(runtime_session, seed_cliente):
    invoice_id = _invoice_with_lines(
        seed_cliente.id, [("A", 3, 33.33), ("B", 1, 0.25), ("C", 7, 1.15), ("D", 1, 10.05)]
    )
    righe = sorted(runtime_session.get(Fattura, invoice_id).righe, key=lambda r: r.numero_riga)
    invoice_commands.update_riga(riga_id=righe[2].id, quantita=9)
    invoice_commands.delete_riga(riga_id=righe[3].id)

    runtime_session.expire_all()
    fattura = runtime_session.get(Fattura, invoice_id)
    _consistent(fattura)
    assert (fattura.imponibile, fattura.iva, fattura.totale) == (
        Decimal("110.59"),
        Decimal("24.33"),
        Decimal("134.92"),
    )

    xml = FatturaPABuilder(get_settings()).build(fattura)
    assert re.findall(r"<Imposta>([^<]+)</Imposta>", xml) == ["24.33"]
    assert re.findall(r"<ImportoPagamento>([^<]+)</ImportoPagamento>", xml) == ["134.92"]


def test_vat_is_rounded_half_up(runtime_session, seed_cliente):
    # 0.25 at 22% is 0.055: commercial rounding gives 0.06, banker's rounding 0.06/0.05.
    invoice_id = _invoice_with_lines(seed_cliente.id, [("A", 1, 0.25)])
    runtime_session.expire_all()
    assert runtime_session.get(Fattura, invoice_id).iva == Decimal("0.06")


def test_explicit_duplicate_invoice_number_is_rejected(runtime_db, seed_cliente):
    assert invoice_commands.create_invoice(cliente_id=seed_cliente.id, anno=2026, numero="7")[
        "success"
    ]
    result = invoice_commands.create_invoice(cliente_id=seed_cliente.id, anno=2026, numero="7")
    assert result["error"].startswith("Invoice number 7/2026 is already used")
    assert "SQL" not in result["error"]


def test_credit_note_matches_source_totals(runtime_session, seed_cliente):
    invoice_id = _invoice_with_lines(seed_cliente.id, [("A", 3, 33.33), ("B", 1, 0.25)])

    result = nota_credito_ops.create_nota_credito_from_fattura(fattura_id=invoice_id)

    assert result.get("success"), result
    runtime_session.expire_all()
    source = runtime_session.get(Fattura, invoice_id)
    credit = runtime_session.get(Fattura, result["nota_credito_id"])
    _consistent(credit)
    assert (credit.imponibile, credit.iva, credit.totale) == (
        source.imponibile,
        source.iva,
        source.totale,
    )
    assert credit.fattura_collegata_id == source.id


# --- Quotes ---------------------------------------------------------------


def test_quote_lifecycle_and_conversion(runtime_session, seed_cliente):
    created = preventivo_ops.create_preventivo(
        cliente_id=seed_cliente.id,
        righe=[
            {"descrizione": "Analisi", "quantita": 3, "prezzo_unitario": 33.33, "aliquota_iva": 22},
            {"descrizione": "Setup", "quantita": 1, "prezzo_unitario": 0.25, "aliquota_iva": 22},
        ],
    )
    assert created.get("success"), created
    quote_id = created["preventivo_id"]

    runtime_session.expire_all()
    quote = runtime_session.get(Preventivo, quote_id)
    _consistent(quote)

    assert preventivo_ops.update_preventivo_status(quote_id, "accettato").get("success")
    converted = preventivo_ops.convert_preventivo_to_invoice(quote_id)
    assert converted.get("success"), converted

    runtime_session.expire_all()
    invoice = runtime_session.get(Fattura, converted["fattura_id"])
    _consistent(invoice)
    assert invoice.totale == runtime_session.get(Preventivo, quote_id).totale
    assert "error" in preventivo_ops.delete_preventivo(quote_id)


# --- Products and clients -------------------------------------------------


def test_product_crud_and_guarded_delete(runtime_db):
    created = prodotto_ops.create_prodotto(
        codice="CONS", descrizione="Consulenza", prezzo_unitario=90
    )
    assert created.get("success"), created
    assert "error" in prodotto_ops.create_prodotto(
        codice="CONS", descrizione="Altro", prezzo_unitario=1
    )

    product_id = created["prodotto_id"]
    updated = prodotto_ops.update_prodotto(product_id, prezzo_unitario=95.5)
    assert updated.get("success"), updated
    assert prodotto_ops.get_prodotto_details(product_id)["prezzo_unitario"] == 95.5
    assert prodotto_ops.search_prodotti(codice_contains="CON")["count"] == 1

    assert prodotto_ops.delete_prodotto(product_id).get("success")
    assert "error" in prodotto_ops.get_prodotto_details(product_id)


def test_client_update_and_delete_guard(runtime_session, seed_cliente):
    updated = client_commands.update_client(seed_cliente.id, email="nuova@example.com")
    assert updated.get("success"), updated

    _invoice_with_lines(seed_cliente.id, [("A", 1, 10)])
    refused = client_commands.delete_client(seed_cliente.id)
    assert "error" in refused

    other = client_commands.create_client(denominazione="Beta", partita_iva="01234567890")
    assert other.get("success"), other
    assert client_commands.delete_client(other["client_id"]).get("success")
