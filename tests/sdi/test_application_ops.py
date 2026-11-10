"""SDI application operations used by the deterministic CLI."""

from openfatture.sdi.application.invoice_sdi_ops import generate_invoice_xml
from openfatture.sdi.application.journal_ops import (
    associate_receipt,
    list_sdi_journal,
    resolve_submission_attempt,
)
from openfatture.storage.database.models import Fattura


def test_journal_is_empty_on_new_database(runtime_db):
    assert list_sdi_journal() == {"submissions": [], "receipts": []}


def test_journal_operations_report_errors(runtime_db):
    assert "error" in associate_receipt(999, 1, evidence="pec receipt")
    assert "error" in resolve_submission_attempt(999, sent=True, evidence="   ")


def test_generate_xml_dry_run_leaves_invoice_unchanged(runtime_session, seed_fattura):
    result = generate_invoice_xml(seed_fattura.id, dry_run=True)

    assert result.get("success"), result
    assert "FatturaElettronica" in result["xml_content"]
    runtime_session.expire_all()
    assert runtime_session.get(Fattura, seed_fattura.id).xml_path is None


def test_generate_xml_writes_requested_file(runtime_session, seed_fattura, tmp_path):
    target = tmp_path / "out" / "fattura.xml"

    result = generate_invoice_xml(seed_fattura.id, output_path=str(target))

    assert result.get("success"), result
    assert target.read_text(encoding="utf-8").startswith("<?xml")


def test_generate_xml_unknown_invoice(runtime_db):
    assert "error" in generate_invoice_xml(999_999)
