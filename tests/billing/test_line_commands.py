"""Branch coverage for invoice line updates on a real database."""

from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from openfatture.billing.application import line_commands
from openfatture.storage.database.models import Fattura, RigaFattura, StatoFattura


def _riga_id(fattura: Fattura) -> int:
    return fattura.righe[0].id


def _reload(session: Session, riga_id: int) -> RigaFattura:
    session.expire_all()
    riga = session.get(RigaFattura, riga_id)
    assert riga is not None
    return riga


def test_missing_line_is_reported(runtime_db):
    assert line_commands.update_riga(9999) == {"error": "Line item 9999 not found"}


def test_orphan_line_is_reported(runtime_session: Session, seed_fattura: Fattura):
    riga_id = _riga_id(seed_fattura)
    runtime_session.execute(text("PRAGMA foreign_keys=OFF"))
    runtime_session.execute(
        text("UPDATE righe_fattura SET fattura_id = 9999 WHERE id = :id"), {"id": riga_id}
    )
    runtime_session.commit()
    result = line_commands.update_riga(riga_id, descrizione="x")
    assert result == {"error": f"Invoice for line item {riga_id} not found"}


def test_sent_invoice_is_not_editable(runtime_session: Session, seed_fattura: Fattura):
    seed_fattura.stato = StatoFattura.INVIATA
    runtime_session.commit()
    result = line_commands.update_riga(_riga_id(seed_fattura), descrizione="x")
    assert "Cannot modify line item" in result["error"]


def test_identical_values_make_no_changes(seed_fattura: Fattura):
    riga = seed_fattura.righe[0]
    result = line_commands.update_riga(
        riga.id,
        descrizione=riga.descrizione,
        quantita=float(riga.quantita),
        prezzo_unitario=float(riga.prezzo_unitario),
        unita_misura=riga.unita_misura,
    )
    assert result["success"] is True
    assert "changes" not in result


def test_text_only_changes_keep_totals(runtime_session: Session, seed_fattura: Fattura):
    riga_id = _riga_id(seed_fattura)
    result = line_commands.update_riga(riga_id, descrizione="Nuova", unita_misura="giorni")
    assert result["changes"] == ["descrizione", "unita_misura"]
    riga = _reload(runtime_session, riga_id)
    assert (riga.descrizione, riga.unita_misura) == ("Nuova", "giorni")
    assert riga.imponibile == Decimal("1000.00")


def test_rate_change_keeps_natura(runtime_session: Session, seed_fattura: Fattura):
    riga_id = _riga_id(seed_fattura)
    result = line_commands.update_riga(riga_id, aliquota_iva=10)
    assert result["changes"] == ["aliquota_iva"]
    assert result["iva"] == 100.0


def test_natura_change_keeps_rate(runtime_session: Session, seed_fattura: Fattura):
    riga_id = _riga_id(seed_fattura)
    first = line_commands.update_riga(riga_id, aliquota_iva=0)
    assert first["changes"] == ["aliquota_iva", "natura"]
    assert _reload(runtime_session, riga_id).natura == "N2.2"
    second = line_commands.update_riga(riga_id, natura="N2.1")
    assert second["changes"] == ["natura"]
    kept = line_commands.update_riga(riga_id, aliquota_iva=0)
    assert "changes" not in kept
    assert _reload(runtime_session, riga_id).natura == "N2.1"


def test_invalid_vat_combination_is_rejected(seed_fattura: Fattura):
    result = line_commands.update_riga(_riga_id(seed_fattura), aliquota_iva=22, natura="N2.2")
    assert set(result) == {"error"}


def test_unexpected_failure_rolls_back(
    monkeypatch: pytest.MonkeyPatch, runtime_session: Session, seed_fattura: Fattura
):
    riga_id = _riga_id(seed_fattura)

    def boom(fattura: Fattura) -> None:
        raise RuntimeError("recompute failed")

    monkeypatch.setattr(line_commands, "recompute_invoice", boom)
    assert line_commands.update_riga(riga_id, quantita=3) == {"error": "recompute failed"}
    assert _reload(runtime_session, riga_id).quantita == Decimal("10")
