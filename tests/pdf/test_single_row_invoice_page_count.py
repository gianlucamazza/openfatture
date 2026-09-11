"""Regression test for single-row invoice with payment staying on one page.

Bug: PDFGenerator._draw_invoice was too conservative with page breaks,
causing a simple 1-row invoice with IBAN payment info to span 2 pages
when it should fit comfortably on a single A4 page.
"""

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock

import pytest

from openfatture.pdf import PDFGenerator, PDFGeneratorConfig


def count_pdf_pages(pdf_path: Path) -> int:
    """Count the number of pages in a PDF file.

    Uses pypdf which is a standard library for PDF manipulation.
    """
    try:
        from pypdf import PdfReader

        with open(pdf_path, "rb") as f:
            pdf = PdfReader(f)
            return len(pdf.pages)
    except ImportError:
        # Fallback: count showPage calls in PDF source
        # This is a simple heuristic but works for basic PDFs
        with open(pdf_path, "rb") as f:
            content = f.read()
            # Count number of page objects in PDF
            return content.count(b"/Type /Page")


@pytest.fixture
def mock_single_row_invoice_with_payment():
    """Create a minimal mock invoice: 1 row + payment info (IBAN, BIC, scadenza).

    Uses realistic long company/client names that previously triggered the bug
    where available_for_table dropped below the 5cm threshold.
    """
    # Mock cliente with realistic long name and address
    cliente = Mock()
    cliente.denominazione = "ACME Consulenza e Sviluppo Software S.r.l."
    cliente.partita_iva = "12345678901"
    cliente.codice_fiscale = "RSSMRA80A01H501U"
    cliente.indirizzo = "Via Giuseppe Mazzini"
    cliente.numero_civico = "123/A"
    cliente.cap = "00100"
    cliente.comune = "Roma"
    cliente.provincia = "RM"

    # Single invoice line
    riga = Mock()
    riga.descrizione = "Consulenza specialistica sviluppo software e testing"
    riga.quantita = Decimal("10")
    riga.prezzo_unitario = Decimal("100.00")
    riga.unita_misura = "ore"
    riga.aliquota_iva = Decimal("22")
    riga.imponibile = Decimal("1000.00")
    riga.iva = Decimal("220.00")
    riga.totale = Decimal("1220.00")

    # Payment with IBAN, BIC, and due date
    pagamento = Mock()
    pagamento.modalita = "MP05"  # Bonifico
    pagamento.data_scadenza = date.today() + timedelta(days=30)
    pagamento.iban = "IT60X0542811101000000123456"
    pagamento.bic_swift = "BPPIITRRXXX"
    pagamento.importo = Decimal("1220.00")

    # Mock fattura
    fattura = Mock()
    fattura.id = 123
    fattura.numero = "001"
    fattura.anno = 2026
    fattura.data_emissione = date.today()
    fattura.tipo_documento = Mock(value="TD01")
    fattura.cliente = cliente
    fattura.righe = [riga]
    fattura.pagamenti = [pagamento]
    fattura.imponibile = Decimal("1000.00")
    fattura.iva = Decimal("220.00")
    fattura.totale = Decimal("1220.00")
    fattura.ritenuta_acconto = Decimal("0")
    fattura.aliquota_ritenuta = Decimal("0")
    fattura.importo_bollo = Decimal("0")
    fattura.stato = Mock(value="bozza")
    fattura.note = None  # No notes to keep it simple

    return fattura


def test_single_row_invoice_with_payment_fits_on_one_page(
    mock_single_row_invoice_with_payment, tmp_path
):
    """Test that a 1-row invoice with IBAN payment block stays on 1 page.

    Regression test for premature page break bug where the PDF generator
    was too conservative about reserved space, causing simple invoices
    to unnecessarily span 2 pages.

    A typical freelance invoice (1 line item + totals + IBAN/BIC/due date)
    MUST fit on a single A4 page, even with long company names and addresses.
    """
    # Use long company name and address that previously triggered the bug
    config = PDFGeneratorConfig(
        template="professional",
        company_name="Consulenza Freelance Avanzata e Innovazione Bancaria S.r.l.",
        company_vat="IT12345678901",
        company_address="Via della Innovazione 42/B",
        company_city="Milano, 20100 (MI)",
    )
    generator = PDFGenerator(config)

    output_file = tmp_path / "single_row_invoice_with_payment.pdf"
    pdf_path = generator.generate(
        mock_single_row_invoice_with_payment, output_path=str(output_file)
    )

    assert pdf_path.exists()

    # The critical assertion: must be exactly 1 page
    page_count = count_pdf_pages(pdf_path)
    assert page_count == 1, (
        f"Single-row invoice with payment info should fit on 1 page, "
        f"but spans {page_count} pages. This indicates the page break "
        f"logic is too conservative."
    )


def test_single_row_invoice_with_short_notes_fits_on_one_page(
    mock_single_row_invoice_with_payment, tmp_path
):
    """Test that a 1-row invoice with payment + short notes stays on 1 page."""
    # Add a short note (typical case)
    mock_single_row_invoice_with_payment.note = "Pagamento entro 30 giorni dalla data fattura."

    config = PDFGeneratorConfig(
        template="professional",
        company_name="Test Freelancer SRL",
        company_vat="IT12345678901",
    )
    generator = PDFGenerator(config)

    output_file = tmp_path / "single_row_with_notes.pdf"
    pdf_path = generator.generate(
        mock_single_row_invoice_with_payment, output_path=str(output_file)
    )

    assert pdf_path.exists()

    page_count = count_pdf_pages(pdf_path)
    assert page_count == 1, (
        f"Single-row invoice with payment and short notes should fit on 1 page, "
        f"but spans {page_count} pages."
    )
