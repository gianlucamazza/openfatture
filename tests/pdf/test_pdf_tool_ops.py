"""Application-level PDF generation: location, courtesy-copy contract, defaults."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from openfatture.pdf.components import COURTESY_COPY_NOTE
from openfatture.pdf.generator import DEFAULT_TEMPLATE
from openfatture.pdf.tool_ops import generate_invoice_pdf
from openfatture.platform.config import get_settings


def test_default_output_goes_to_exports_not_cwd(seed_fattura, tmp_path, monkeypatch) -> None:
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    monkeypatch.chdir(cwd)

    result = generate_invoice_pdf(fattura_id=seed_fattura.id)

    assert result["success"] is True, result
    pdf_path = Path(result["pdf_path"])
    assert pdf_path == get_settings().exports_dir / "fatture" / "fattura_1_2025.pdf"
    assert pdf_path.is_file()
    assert list(cwd.iterdir()) == []
    assert result["courtesy_copy"] is True
    assert result["template"] == DEFAULT_TEMPLATE


def test_pdf_states_it_is_a_courtesy_copy(seed_fattura) -> None:
    result = generate_invoice_pdf(fattura_id=seed_fattura.id)

    text = " ".join(page.extract_text() for page in PdfReader(result["pdf_path"]).pages)
    assert "Copia di cortesia" in text
    assert "DM 17/06/2014" not in text
    assert COURTESY_COPY_NOTE.startswith("Copia di cortesia")


def test_issued_elsewhere_invoice_can_be_rendered(seed_fattura, runtime_session) -> None:
    seed_fattura.issued_elsewhere = True
    runtime_session.commit()

    result = generate_invoice_pdf(fattura_id=seed_fattura.id)

    assert result["success"] is True, result
    assert result["issued_elsewhere"] is True


def test_unknown_template_is_refused(seed_fattura) -> None:
    result = generate_invoice_pdf(fattura_id=seed_fattura.id, template="fancy")
    assert result["success"] is False
    assert "minimalist" in result["error"]
