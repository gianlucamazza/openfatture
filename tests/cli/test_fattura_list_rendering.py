"""Narrow and wide renderings of ``fattura list``."""

from typing import Any

import pytest
from rich.console import Console
from typer.testing import CliRunner

from openfatture.cli.commands import fattura
from openfatture.i18n import _

runner = CliRunner()


@pytest.fixture(autouse=True)
def _isolated_database(runtime_db):
    """The command group opens the configured database before listing."""


def _invoice(**overrides: Any) -> dict[str, Any]:
    invoice: dict[str, Any] = {
        "id": 1,
        "numero": "1",
        "anno": 2026,
        "data": "2026-01-15",
        "cliente": "ACME [srl]",
        "importo": 1220.0,
        "amount_paid": 0.0,
        "outstanding": 1220.0,
        "payment_status": "unpaid",
        "stato": "inviata",
        "issued_elsewhere": False,
    }
    invoice.update(overrides)
    return invoice


INVOICES = [
    _invoice(
        id=7,
        numero="7",
        payment_status="no_payment_record",
        issued_elsewhere=True,
        status_origin="sdi_receipt",
        stato="consegnata",
        submission_state="pending",
        collection_statement={"value": "settled", "source": "owner"},
    ),
    _invoice(id=8, numero="8", amount_paid=200.0, outstanding=1020.0),
    _invoice(id=9, numero="9", issued_elsewhere=True, submission_state="uncertain"),
]


def _run(monkeypatch: pytest.MonkeyPatch, width: int, result: dict[str, Any]) -> str:
    monkeypatch.setattr(fattura, "console", Console(width=width))
    monkeypatch.setattr(fattura, "search_invoices", lambda **kwargs: result)
    monkeypatch.setattr(fattura, "remember_result", lambda result: None)
    outcome = runner.invoke(fattura.app, ["list"])
    assert outcome.exit_code == 0, outcome.output
    return outcome.output


def test_error_exits_with_code_one(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(fattura, "search_invoices", lambda **kwargs: {"error": "db down"})
    monkeypatch.setattr(fattura, "remember_result", lambda result: None)
    outcome = runner.invoke(fattura.app, ["list"])
    assert outcome.exit_code == 1
    assert "db down" in outcome.output


def test_narrow_listing(monkeypatch: pytest.MonkeyPatch):
    output = _run(monkeypatch, 119, {"count": 3, "fatture": INVOICES, "has_more": True})
    lines = output.splitlines()
    assert "7/2026 · ACME [srl]" in lines
    assert f"  {_('cli-invoice-collected')}: —" in lines
    assert f"  {_('cli-invoice-collected')}: 200,00\xa0€" in lines
    historical = _("cli-invoice-historical")
    pec = _("cli-fattura-pec-to-verify")
    no_record = _("cli-invoice-no-payment-record")
    assert f"  2026-01-15 · {historical} · {pec} · SDI: consegnata · {no_record}" in lines
    assert f"  2026-01-15 · inviata · {_('cli-invoice-unpaid')}" in lines
    assert f"  2026-01-15 · {historical} · {pec} · {_('cli-invoice-unpaid')}" in lines
    assert "  " + _("cli-fattura-statement", value="settled", source="owner") in lines
    assert lines[-1] == "… --limit"


def test_wide_listing(monkeypatch: pytest.MonkeyPatch):
    output = _run(monkeypatch, 200, {"count": 3, "fatture": INVOICES, "has_more": True})
    rows = {line.split("│")[1].strip(): line for line in output.splitlines() if "│" in line}
    historical = _("cli-invoice-historical")
    assert f"{historical} · SDI: consegnata" in rows["7"]
    assert "—" in rows["7"]
    assert "inviata" in rows["8"] and "200" in rows["8"]
    assert historical in rows["9"] and "SDI" not in rows["9"]
    statement = _("cli-fattura-statement", value="settled", source="owner")
    assert f"7/2026 · {statement}" in output.splitlines()
    assert "Usa --limit" in output


def test_wide_listing_without_more(monkeypatch: pytest.MonkeyPatch):
    output = _run(monkeypatch, 200, {"count": 1, "fatture": INVOICES[1:2]})
    assert "Usa --limit" not in output
    assert "Dichiarazione" not in output


def test_narrow_listing_without_more(monkeypatch: pytest.MonkeyPatch):
    output = _run(monkeypatch, 80, {"count": 1, "fatture": INVOICES[1:2]})
    assert "--limit" not in output
