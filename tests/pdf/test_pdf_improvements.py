"""Tests for PDF improvements (professional template, cedente header, IBAN block)."""

from pathlib import Path

from openfatture.pdf.generator import PDFGenerator, PDFGeneratorConfig


def test_professional_template_is_default():
    """Test that professional template is now the default."""
    config = PDFGeneratorConfig()
    assert config.template == "professional"


def test_pdf_with_logo_path_not_required(sample_fattura_with_righe):
    """Test that logo path can be specified without requiring the file to exist."""
    config = PDFGeneratorConfig(
        template="professional",
        company_name="Test Company",
        logo_path="/nonexistent/logo.png",  # File doesn't exist but shouldn't fail
    )
    generator = PDFGenerator(config)

    # Should not raise an error
    pdf_path = generator.generate(sample_fattura_with_righe, output_path="/tmp/test_logo.pdf")
    assert Path(pdf_path).exists()


def test_pdf_with_payment_iban_block(sample_fattura_with_payment):
    """Test PDF generation with IBAN/payment block."""
    config = PDFGeneratorConfig(
        template="professional",
        company_name="Test Company SRL",
        company_vat="12345678901",
    )
    generator = PDFGenerator(config)

    pdf_path = generator.generate(sample_fattura_with_payment, output_path="/tmp/test_payment.pdf")
    assert Path(pdf_path).exists()

    # Check file size is reasonable (payment block adds content)
    assert Path(pdf_path).stat().st_size > 5000


def test_professional_template_cedente_header(sample_fattura_with_righe):
    """Test professional template with cedente (issuer) header block."""
    config = PDFGeneratorConfig(
        template="professional",
        company_name="ACME Consulting SRL",
        company_vat="IT12345678901",
        company_address="Via Roma 123",
        company_city="Milano 20100",
    )
    generator = PDFGenerator(config)

    pdf_path = generator.generate(sample_fattura_with_righe, output_path="/tmp/test_cedente.pdf")
    assert Path(pdf_path).exists()


def test_pdf_long_description_with_payment(sample_fattura_with_long_descriptions):
    """Test PDF with long descriptions AND payment block (regression test)."""
    # Add payment data
    from openfatture.storage.database.models import Pagamento

    pagamento = Pagamento(
        fattura_id=sample_fattura_with_long_descriptions.id,
        modalita="MP05",
        importo=sample_fattura_with_long_descriptions.totale,
        iban="IT60X0542811101000000123456",
        bic_swift="BPMOITMMXXX",
    )
    sample_fattura_with_long_descriptions.pagamenti = [pagamento]

    config = PDFGeneratorConfig(
        template="professional",
        company_name="Test Company",
        company_vat="12345678901",
    )
    generator = PDFGenerator(config)

    pdf_path = generator.generate(
        sample_fattura_with_long_descriptions, output_path="/tmp/test_long_payment.pdf"
    )
    assert Path(pdf_path).exists()


def test_minimalist_template_still_available(sample_fattura_with_righe):
    """Test that minimalist template is still available."""
    config = PDFGeneratorConfig(
        template="minimalist",
        company_name="Test Company",
    )
    generator = PDFGenerator(config)

    pdf_path = generator.generate(sample_fattura_with_righe, output_path="/tmp/test_minimalist.pdf")
    assert Path(pdf_path).exists()


def test_pdf_factory_function_default():
    """Test factory function uses professional as default."""
    from openfatture.pdf.generator import create_pdf_generator

    generator = create_pdf_generator(company_name="Test")
    assert generator.config.template == "professional"
