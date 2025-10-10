"""Tests for PDF generation service."""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest

from openfatture.services.pdf import (
    BrandedTemplate,
    MinimalistTemplate,
    PDFGenerator,
    PDFGeneratorConfig,
    ProfessionalTemplate,
)
from openfatture.services.pdf.components.qrcode import (
    generate_pagopa_qr_data,
    generate_sepa_qr_data,
)


@pytest.fixture
def mock_fattura():
    """Create mock invoice for testing."""
    # Mock cliente
    cliente = Mock()
    cliente.denominazione = "ACME S.r.l."
    cliente.partita_iva = "12345678901"
    cliente.codice_fiscale = "RSSMRA80A01H501U"
    cliente.indirizzo = "Via Roma"
    cliente.numero_civico = "123"
    cliente.cap = "00100"
    cliente.comune = "Roma"
    cliente.provincia = "RM"

    # Mock righe (invoice lines)
    riga1 = Mock()
    riga1.descrizione = "Consulenza Python - Sviluppo API REST"
    riga1.quantita = Decimal("10")
    riga1.prezzo_unitario = Decimal("100.00")
    riga1.unita_misura = "ore"
    riga1.aliquota_iva = Decimal("22")
    riga1.imponibile = Decimal("1000.00")
    riga1.iva = Decimal("220.00")
    riga1.totale = Decimal("1220.00")

    riga2 = Mock()
    riga2.descrizione = "Code review e testing"
    riga2.quantita = Decimal("5")
    riga2.prezzo_unitario = Decimal("80.00")
    riga2.unita_misura = "ore"
    riga2.aliquota_iva = Decimal("22")
    riga2.imponibile = Decimal("400.00")
    riga2.iva = Decimal("88.00")
    riga2.totale = Decimal("488.00")

    # Mock pagamento
    pagamento = Mock()
    pagamento.modalita = "Bonifico"
    pagamento.data_scadenza = date(2025, 11, 30)
    pagamento.iban = "IT60X0542811101000000123456"
    pagamento.bic_swift = "BPPIITRRXXX"
    pagamento.importo = Decimal("1708.00")

    # Mock fattura
    fattura = Mock()
    fattura.id = 123
    fattura.numero = "001"
    fattura.anno = 2025
    fattura.data_emissione = date(2025, 10, 10)
    fattura.tipo_documento = Mock(value="TD01")
    fattura.cliente = cliente
    fattura.righe = [riga1, riga2]
    fattura.pagamenti = [pagamento]
    fattura.imponibile = Decimal("1400.00")
    fattura.iva = Decimal("308.00")
    fattura.totale = Decimal("1708.00")
    fattura.ritenuta_acconto = Decimal("0")
    fattura.aliquota_ritenuta = Decimal("0")
    fattura.importo_bollo = Decimal("0")
    fattura.stato = Mock(value="bozza")
    fattura.note = "Pagamento entro 30 giorni dalla data fattura"

    return fattura


class TestPDFGeneratorConfig:
    """Test PDF generator configuration."""

    def test_default_config(self):
        """Test default configuration."""
        config = PDFGeneratorConfig()

        assert config.template == "minimalist"
        assert config.enable_pdfa is True
        assert config.enable_qr_code is False
        assert config.primary_color == "#2C3E50"

    def test_custom_config(self):
        """Test custom configuration."""
        config = PDFGeneratorConfig(
            template="professional",
            company_name="ACME S.r.l.",
            company_vat="12345678901",
            enable_qr_code=True,
            primary_color="#E74C3C",
        )

        assert config.template == "professional"
        assert config.company_name == "ACME S.r.l."
        assert config.enable_qr_code is True
        assert config.primary_color == "#E74C3C"


class TestTemplates:
    """Test PDF templates."""

    def test_minimalist_template(self):
        """Test minimalist template."""
        template = MinimalistTemplate()

        assert template.get_primary_color() == "#000000"
        assert template.get_secondary_color() == "#666666"

    def test_professional_template(self):
        """Test professional template."""
        template = ProfessionalTemplate(logo_path="./logo.png")

        assert template.get_primary_color() == "#1E3A5F"
        assert template.get_secondary_color() == "#4A90E2"
        assert template.logo_path == "./logo.png"

    def test_branded_template(self):
        """Test branded template."""
        template = BrandedTemplate(
            primary_color="#E74C3C",
            secondary_color="#95A5A6",
            watermark_text="BOZZA",
        )

        assert template.get_primary_color() == "#E74C3C"
        assert template.get_secondary_color() == "#95A5A6"
        assert template.watermark_text == "BOZZA"


class TestPDFGenerator:
    """Test PDF generator."""

    def test_create_minimalist_template(self):
        """Test creating minimalist template."""
        config = PDFGeneratorConfig(template="minimalist")
        generator = PDFGenerator(config)

        assert isinstance(generator.template, MinimalistTemplate)

    def test_create_professional_template(self):
        """Test creating professional template."""
        config = PDFGeneratorConfig(template="professional", logo_path="./logo.png")
        generator = PDFGenerator(config)

        assert isinstance(generator.template, ProfessionalTemplate)

    def test_create_branded_template(self):
        """Test creating branded template."""
        config = PDFGeneratorConfig(
            template="branded",
            primary_color="#E74C3C",
            watermark_text="COPIA",
        )
        generator = PDFGenerator(config)

        assert isinstance(generator.template, BrandedTemplate)

    def test_invalid_template(self):
        """Test invalid template name."""
        config = PDFGeneratorConfig(template="invalid")

        with pytest.raises(ValueError, match="Invalid template"):
            PDFGenerator(config)

    def test_generate_pdf(self, mock_fattura, tmp_path):
        """Test PDF generation."""
        config = PDFGeneratorConfig(
            template="minimalist",
            company_name="Test Company",
            enable_qr_code=False,
        )
        generator = PDFGenerator(config)

        output_file = tmp_path / "test_invoice.pdf"
        pdf_path = generator.generate(mock_fattura, output_path=str(output_file))

        assert pdf_path.exists()
        assert pdf_path.suffix == ".pdf"
        assert pdf_path.stat().st_size > 0

    def test_generate_pdf_with_qr_code(self, mock_fattura, tmp_path):
        """Test PDF generation with QR code."""
        config = PDFGeneratorConfig(
            template="professional",
            company_name="Test Company",
            enable_qr_code=True,
            qr_code_type="sepa",
        )
        generator = PDFGenerator(config)

        output_file = tmp_path / "test_invoice_qr.pdf"
        pdf_path = generator.generate(mock_fattura, output_path=str(output_file))

        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0

    def test_fattura_to_dict(self, mock_fattura):
        """Test invoice to dictionary conversion."""
        config = PDFGeneratorConfig()
        generator = PDFGenerator(config)

        data = generator._fattura_to_dict(mock_fattura)

        assert data["numero"] == "001"
        assert data["anno"] == 2025
        assert data["cliente"]["denominazione"] == "ACME S.r.l."
        assert len(data["righe"]) == 2
        assert data["pagamento"]["iban"] == "IT60X0542811101000000123456"
        assert data["totale"] == Decimal("1708.00")

    def test_auto_generated_filename(self, mock_fattura, tmp_path):
        """Test auto-generated filename."""
        import os

        os.chdir(tmp_path)  # Change to temp dir

        config = PDFGeneratorConfig()
        generator = PDFGenerator(config)

        pdf_path = generator.generate(mock_fattura)

        assert pdf_path.name == "fattura_001_2025.pdf"
        assert pdf_path.exists()


class TestQRCodeGeneration:
    """Test QR code generation."""

    def test_generate_sepa_qr(self):
        """Test SEPA QR code generation."""
        qr_data = generate_sepa_qr_data(
            beneficiary_name="ACME S.r.l.",
            iban="IT60X0542811101000000123456",
            amount=1708.00,
            reference="Fattura 001/2025",
            bic="BPPIITRRXXX",
        )

        assert "BCD" in qr_data  # Service tag
        assert "SCT" in qr_data  # SEPA Credit Transfer
        assert "ACME S.r.l." in qr_data
        assert "IT60X0542811101000000123456" in qr_data
        assert "EUR1708.00" in qr_data
        assert "Fattura 001/2025" in qr_data

    def test_generate_pagopa_qr(self):
        """Test pagoPa QR code generation."""
        qr_data = generate_pagopa_qr_data(
            creditor_fiscal_code="12345678901",
            notice_number="123456789012345678",
            amount=1708.00,
        )

        assert qr_data.startswith("PAGOPA|")
        assert "002" in qr_data  # Version
        assert "123456789012345678" in qr_data  # Notice number
        assert "12345678901" in qr_data  # Fiscal code
        assert "170800" in qr_data  # Amount in cents

    def test_sepa_qr_without_bic(self):
        """Test SEPA QR without BIC (optional)."""
        qr_data = generate_sepa_qr_data(
            beneficiary_name="ACME S.r.l.",
            iban="IT60X0542811101000000123456",
            amount=1000.00,
            reference="Test payment",
        )

        assert "BCD" in qr_data
        assert "IT60X0542811101000000123456" in qr_data
        # BIC line should be empty
        lines = qr_data.split("\n")
        assert lines[4] == ""  # BIC line (index 4) should be empty


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_invoice_with_ritenuta(self, mock_fattura, tmp_path):
        """Test invoice with ritenuta d'acconto."""
        mock_fattura.ritenuta_acconto = Decimal("280.00")  # 20% of 1400
        mock_fattura.aliquota_ritenuta = Decimal("20")

        config = PDFGeneratorConfig()
        generator = PDFGenerator(config)

        output_file = tmp_path / "test_ritenuta.pdf"
        pdf_path = generator.generate(mock_fattura, output_path=str(output_file))

        assert pdf_path.exists()

    def test_invoice_with_bollo(self, mock_fattura, tmp_path):
        """Test invoice with bollo (stamp duty)."""
        mock_fattura.importo_bollo = Decimal("2.00")

        config = PDFGeneratorConfig()
        generator = PDFGenerator(config)

        output_file = tmp_path / "test_bollo.pdf"
        pdf_path = generator.generate(mock_fattura, output_path=str(output_file))

        assert pdf_path.exists()

    def test_invoice_without_payment(self, mock_fattura, tmp_path):
        """Test invoice without payment info."""
        mock_fattura.pagamenti = []

        config = PDFGeneratorConfig(enable_qr_code=True)
        generator = PDFGenerator(config)

        output_file = tmp_path / "test_no_payment.pdf"
        pdf_path = generator.generate(mock_fattura, output_path=str(output_file))

        # Should generate without QR code
        assert pdf_path.exists()

    def test_invoice_with_long_description(self, mock_fattura, tmp_path):
        """Test invoice with very long line description."""
        mock_fattura.righe[0].descrizione = "A" * 200  # Very long description

        config = PDFGeneratorConfig()
        generator = PDFGenerator(config)

        output_file = tmp_path / "test_long_desc.pdf"
        pdf_path = generator.generate(mock_fattura, output_path=str(output_file))

        # Should truncate and still generate
        assert pdf_path.exists()

    def test_watermark_on_branded_template(self, mock_fattura, tmp_path):
        """Test watermark on branded template."""
        config = PDFGeneratorConfig(
            template="branded",
            watermark_text="BOZZA",
        )
        generator = PDFGenerator(config)

        output_file = tmp_path / "test_watermark.pdf"
        pdf_path = generator.generate(mock_fattura, output_path=str(output_file))

        assert pdf_path.exists()
        # Watermark is visual, can't easily test in PDF, but should not crash


@pytest.mark.parametrize("template_name", ["minimalist", "professional", "branded"])
def test_all_templates(template_name, mock_fattura, tmp_path):
    """Test all templates generate valid PDFs."""
    config = PDFGeneratorConfig(
        template=template_name,
        company_name="Test Company",
    )
    generator = PDFGenerator(config)

    output_file = tmp_path / f"test_{template_name}.pdf"
    pdf_path = generator.generate(mock_fattura, output_path=str(output_file))

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 1000  # At least 1KB
