"""SDI application operations: FatturaPA XML and the SDI journal."""

from pathlib import Path

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


def test_generate_xml_writes_the_valid_file_in_the_archive(runtime_session, seed_fattura):
    result = generate_invoice_xml(seed_fattura.id)

    assert result.get("valid"), result
    path = Path(result["xml_path"])
    assert path.parent.name == "xml"
    assert path.read_text(encoding="utf-8").startswith("<?xml")
    runtime_session.expire_all()
    assert runtime_session.get(Fattura, seed_fattura.id).xml_path == str(path)


def test_invalid_xml_is_never_written(runtime_session, seed_fattura, monkeypatch):
    from openfatture.sdi.validator.xsd_validator import FatturaPAValidator

    monkeypatch.setattr(FatturaPAValidator, "validate", lambda self, xml: (False, "bad"))

    result = generate_invoice_xml(seed_fattura.id)

    assert result["valid"] is False
    assert "bad" in result["error"]
    runtime_session.expire_all()
    assert runtime_session.get(Fattura, seed_fattura.id).xml_path is None
    from openfatture.platform.config import get_settings

    assert not list((get_settings().archivio_dir / "xml").glob("*.xml"))


def test_generate_xml_unknown_invoice(runtime_db):
    assert "error" in generate_invoice_xml(999_999)
