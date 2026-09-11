"""Integration tests for FatturaPA XML XSD validation."""

from decimal import Decimal
from pathlib import Path

import pytest

from openfatture.sdi.validator.xsd_validator import FatturaPAValidator
from openfatture.sdi.xml_builder.fatturapa import FatturaPABuilder

pytestmark = pytest.mark.unit


class TestXSDValidation:
    """Tests for XSD validation of generated XML."""

    @pytest.fixture(autouse=True)
    def setup_xsd_path(self, test_settings):
        """Ensure XSD schema is available."""
        xsd_path = test_settings.data_dir / "schemas" / "FatturaPA_v1.2.2.xsd"
        if not xsd_path.exists():
            pytest.skip("XSD schema not available - download it with `uv run python -c 'from openfatture.sdi.validator.xsd_validator import download_xsd_schema; download_xsd_schema(auto_download=True)'`")

    def test_basic_invoice_validates(self, test_settings, sample_fattura):
        """Test basic invoice XML validates against XSD."""
        builder = FatturaPABuilder(test_settings)
        xml_content = builder.build(sample_fattura)

        validator = FatturaPAValidator()
        is_valid, error = validator.validate(xml_content)

        assert is_valid, f"Validation failed: {error}"

    def test_invoice_with_ritenuta_validates(self, test_settings, sample_fattura_with_ritenuta):
        """Test invoice with withholding tax validates against XSD."""
        builder = FatturaPABuilder(test_settings)
        xml_content = builder.build(sample_fattura_with_ritenuta)

        validator = FatturaPAValidator()
        is_valid, error = validator.validate(xml_content)

        assert is_valid, f"Validation failed: {error}"

    def test_invoice_with_bollo_validates(self, test_settings, sample_fattura_with_bollo):
        """Test invoice with stamp duty validates against XSD."""
        builder = FatturaPABuilder(test_settings)
        xml_content = builder.build(sample_fattura_with_bollo)

        validator = FatturaPAValidator()
        is_valid, error = validator.validate(xml_content)

        assert is_valid, f"Validation failed: {error}"

    def test_invoice_with_natura_validates(self, test_settings, sample_fattura_with_natura):
        """Test invoice with natura code validates against XSD."""
        builder = FatturaPABuilder(test_settings)
        xml_content = builder.build(sample_fattura_with_natura)

        validator = FatturaPAValidator()
        is_valid, error = validator.validate(xml_content)

        assert is_valid, f"Validation failed: {error}"

    def test_invoice_with_cassa_validates(self, test_settings, sample_fattura_with_cassa):
        """Test invoice with social security contribution validates against XSD."""
        builder = FatturaPABuilder(test_settings)
        xml_content = builder.build(sample_fattura_with_cassa)

        validator = FatturaPAValidator()
        is_valid, error = validator.validate(xml_content)

        assert is_valid, f"Validation failed: {error}"

    def test_natura_codes_validate(self, test_settings, sample_fattura):
        """Test various natura codes validate correctly."""
        builder = FatturaPABuilder(test_settings)

        # Test different natura codes
        natura_codes = ["N1", "N2.1", "N2.2", "N3.1", "N3.2", "N4", "N5", "N6.1", "N6.2", "N7"]

        for natura in natura_codes:
            # Set natura on the line item
            sample_fattura.righe[0].natura = natura
            sample_fattura.righe[0].aliquota_iva = Decimal("0.00")

            xml_content = builder.build(sample_fattura)

            validator = FatturaPAValidator()
            is_valid, error = validator.validate(xml_content)

            assert is_valid, f"Validation failed for natura {natura}: {error}"

    def test_mixed_vat_rates_with_natura_validates(self, test_settings, db_session, sample_fattura):
        """Test invoice with mixed VAT rates and natura codes validates."""
        from openfatture.storage.database.models import RigaFattura

        # Add another line with different VAT rate and natura
        riga2 = RigaFattura(
            fattura_id=sample_fattura.id,
            numero_riga=2,
            descrizione="Export service (non-taxable)",
            quantita=Decimal("5"),
            prezzo_unitario=Decimal("100.00"),
            unita_misura="ore",
            aliquota_iva=Decimal("0.00"),
            natura="N3.1",  # Non imponibile - esportazioni
            imponibile=Decimal("500.00"),
            iva=Decimal("0.00"),
            totale=Decimal("500.00"),
        )
        db_session.add(riga2)
        db_session.commit()
        db_session.refresh(sample_fattura)

        builder = FatturaPABuilder(test_settings)
        xml_content = builder.build(sample_fattura)

        validator = FatturaPAValidator()
        is_valid, error = validator.validate(xml_content)

        assert is_valid, f"Validation failed: {error}"
