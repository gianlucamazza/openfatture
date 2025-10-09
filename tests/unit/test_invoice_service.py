"""
Unit tests for InvoiceService.

Tests the business logic layer for invoice operations.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from openfatture.core.fatture.service import InvoiceService

pytestmark = pytest.mark.unit


class TestInvoiceService:
    """Test InvoiceService business logic."""

    def test_init(self, test_settings):
        """Test service initialization."""
        service = InvoiceService(test_settings)

        assert service.settings == test_settings
        assert service.xml_builder is not None
        assert service.validator is not None

    def test_generate_xml_success(self, test_settings, sample_fattura, tmp_path):
        """Test successful XML generation."""
        service = InvoiceService(test_settings)

        # Generate XML without validation (to avoid XSD download)
        xml_content, error = service.generate_xml(sample_fattura, validate=False)

        assert error is None
        assert xml_content is not None
        assert "FatturaElettronica" in xml_content
        assert sample_fattura.xml_path is not None

    def test_generate_xml_with_validation_success(self, test_settings, sample_fattura):
        """Test XML generation with successful validation."""
        service = InvoiceService(test_settings)

        # Mock validator to return success
        with patch.object(service.validator, "validate", return_value=(True, None)):
            xml_content, error = service.generate_xml(sample_fattura, validate=True)

            assert error is None
            assert xml_content is not None
            assert "FatturaElettronica" in xml_content

    def test_generate_xml_with_validation_failure(self, test_settings, sample_fattura):
        """Test XML generation with validation failure."""
        service = InvoiceService(test_settings)

        # Mock validator to return failure
        validation_error = "Invalid XML schema"
        with patch.object(service.validator, "validate", return_value=(False, validation_error)):
            xml_content, error = service.generate_xml(sample_fattura, validate=True)

            assert error is not None
            assert "Validation failed" in error
            assert validation_error in error
            assert xml_content is not None  # XML is still returned even if validation fails

    def test_generate_xml_exception_handling(self, test_settings, sample_fattura):
        """Test XML generation handles exceptions properly."""
        service = InvoiceService(test_settings)

        # Mock xml_builder to raise exception
        with patch.object(service.xml_builder, "build", side_effect=Exception("XML error")):
            xml_content, error = service.generate_xml(sample_fattura, validate=False)

            assert error is not None
            assert "Error generating XML" in error
            assert "XML error" in error
            assert xml_content == ""

    def test_generate_xml_updates_fattura_path(self, test_settings, sample_fattura):
        """Test that XML generation updates fattura.xml_path."""
        service = InvoiceService(test_settings)

        # Initial state
        assert sample_fattura.xml_path is None

        # Generate XML
        xml_content, error = service.generate_xml(sample_fattura, validate=False)

        # Verify path was updated
        assert error is None
        assert sample_fattura.xml_path is not None
        assert "IT12345678903_00001.xml" in sample_fattura.xml_path

    def test_get_xml_path(self, test_settings, sample_fattura):
        """Test getting XML path for invoice."""
        service = InvoiceService(test_settings)

        xml_path = service.get_xml_path(sample_fattura)

        assert isinstance(xml_path, Path)
        assert xml_path.name == "IT12345678903_00001.xml"
        assert "archivio" in str(xml_path)
        assert "xml" in str(xml_path)

    def test_generate_xml_with_ritenuta(self, test_settings, sample_fattura_with_ritenuta):
        """Test XML generation for invoice with withholding tax."""
        service = InvoiceService(test_settings)

        xml_content, error = service.generate_xml(sample_fattura_with_ritenuta, validate=False)

        assert error is None
        assert xml_content is not None
        assert "Ritenuta" in xml_content or "DatiRitenuta" in xml_content

    def test_generate_xml_with_bollo(self, test_settings, sample_fattura_with_bollo):
        """Test XML generation for invoice with stamp duty."""
        service = InvoiceService(test_settings)

        xml_content, error = service.generate_xml(sample_fattura_with_bollo, validate=False)

        assert error is None
        assert xml_content is not None
        assert "DatiBollo" in xml_content or "ImportoBollo" in xml_content


class TestInvoiceServiceIntegration:
    """Integration tests for InvoiceService with real XML builder."""

    def test_full_xml_generation_workflow(self, test_settings, sample_fattura):
        """Test complete XML generation workflow."""
        service = InvoiceService(test_settings)

        # Generate XML
        xml_content, error = service.generate_xml(sample_fattura, validate=False)

        # Verify success
        assert error is None
        assert xml_content is not None

        # Verify XML structure (accepts both single and double quotes)
        assert "encoding" in xml_content and "UTF-8" in xml_content
        assert "FatturaElettronica" in xml_content
        assert "FatturaElettronicaHeader" in xml_content
        assert "FatturaElettronicaBody" in xml_content

        # Verify cedente data
        assert "12345678903" in xml_content  # Partita IVA
        assert "Test Company SRL" in xml_content

        # Verify cessionario data
        assert sample_fattura.cliente.denominazione in xml_content
        assert sample_fattura.cliente.partita_iva in xml_content

        # Verify invoice details
        assert sample_fattura.numero in xml_content
        # Imponibile - accept various decimal formats (1000, 1000.0, 1000.00)
        assert "1000" in xml_content

    def test_xml_path_creation(self, test_settings, sample_fattura):
        """Test that XML path is created correctly."""
        service = InvoiceService(test_settings)

        expected_filename = "IT12345678903_00001.xml"
        expected_path = test_settings.archivio_dir / "xml" / expected_filename

        # Get path
        xml_path = service.get_xml_path(sample_fattura)

        assert xml_path == expected_path
        assert xml_path.name == expected_filename
