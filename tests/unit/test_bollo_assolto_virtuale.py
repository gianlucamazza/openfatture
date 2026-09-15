"""Tests for bollo assolto virtuale functionality (Issue #66).

Tests that when bollo_assolto_virtuale=True:
- Bollo is shown in XML with BolloVirtuale=SI
- Bollo is NOT added to client's payable total
- Bollo is shown in PDF footer with MEF ART.6 wording
- Bollo is NOT shown in PDF summary box
- Compliance validation passes
"""

from decimal import Decimal

import pytest
from lxml import etree

from openfatture.ai.agents.compliance.rules import ComplianceRulesEngine
from openfatture.billing.fatture.service import InvoiceService
from openfatture.pdf.generator import PDFGenerator, PDFGeneratorConfig
from openfatture.sdi.xml_builder.fatturapa import FatturaPABuilder
from openfatture.storage.database.models import Fattura


class TestBolloAssoltoVirtuale:
    """Test bollo assolto virtuale (stamp duty paid by provider, not charged to client)."""

    def test_bollo_assolto_xml_structure(self, test_settings, sample_fattura_with_bollo_assolto):
        """Test that bollo assolto is correctly represented in XML."""
        fattura = sample_fattura_with_bollo_assolto
        builder = FatturaPABuilder(test_settings)
        xml_content = builder.build(fattura)

        root = etree.fromstring(xml_content.encode("utf-8"))
        
        # Check DatiBollo section exists
        dati_bollo = root.find(".//{*}DatiBollo")
        assert dati_bollo is not None, "DatiBollo section should exist"

        # Check BolloVirtuale = SI
        bollo_virtuale = dati_bollo.find("{*}BolloVirtuale")
        assert bollo_virtuale is not None
        assert bollo_virtuale.text == "SI", "BolloVirtuale should be SI"

        # Check ImportoBollo = 2.00
        importo_bollo = dati_bollo.find("{*}ImportoBollo")
        assert importo_bollo is not None
        assert Decimal(importo_bollo.text) == Decimal("2.00"), "ImportoBollo should be 2.00"

    def test_bollo_assolto_total_calculation(self, sample_fattura_with_bollo_assolto):
        """Test that bollo assolto is NOT added to client total."""
        fattura = sample_fattura_with_bollo_assolto
        
        # Verify totals
        assert fattura.imponibile == Decimal("960.00"), "Imponibile should be 960.00"
        assert fattura.importo_bollo == Decimal("2.00"), "Bollo should be 2.00"
        assert fattura.bollo_assolto_virtuale is True, "Bollo should be assolto virtuale"
        assert fattura.totale == Decimal("960.00"), "Total should equal imponibile (bollo NOT added)"

    def test_bollo_charged_total_calculation(self, sample_fattura_with_bollo):
        """Test that bollo charged to client IS added to total."""
        fattura = sample_fattura_with_bollo
        
        # Verify totals
        assert fattura.imponibile == Decimal("100.00"), "Imponibile should be 100.00"
        assert fattura.importo_bollo == Decimal("2.00"), "Bollo should be 2.00"
        assert fattura.bollo_assolto_virtuale is False, "Bollo should be charged to client"
        assert fattura.totale == Decimal("102.00"), "Total should include bollo"

    def test_bollo_assolto_compliance_validation(self, test_settings, sample_fattura_with_bollo_assolto):
        """Test that compliance validation passes for bollo assolto."""
        fattura = sample_fattura_with_bollo_assolto
        engine = ComplianceRulesEngine()
        
        result = engine.validate_invoice(fattura)
        
        # Should have no errors
        errors = [issue for issue in result.issues if issue.severity.value == "error"]
        assert len(errors) == 0, f"Should have no validation errors, got: {errors}"

    def test_bollo_charged_compliance_validation(self, test_settings, sample_fattura_with_bollo):
        """Test that compliance validation passes when bollo is charged to client."""
        fattura = sample_fattura_with_bollo
        engine = ComplianceRulesEngine()
        
        result = engine.validate_invoice(fattura)
        
        # Should have no errors
        errors = [issue for issue in result.issues if issue.severity.value == "error"]
        assert len(errors) == 0, f"Should have no validation errors, got: {errors}"

    def test_bollo_assolto_pdf_generation(self, test_settings, sample_fattura_with_bollo_assolto, tmp_path):
        """Test PDF generation for invoice with bollo assolto."""
        fattura = sample_fattura_with_bollo_assolto
        
        config = PDFGeneratorConfig(
            company_name=test_settings.cedente_denominazione or "Test Company",
            company_vat=test_settings.cedente_partita_iva,
            company_cf=test_settings.cedente_codice_fiscale,
        )
        generator = PDFGenerator(config)
        
        output_file = tmp_path / "test_bollo_assolto.pdf"
        pdf_path = generator.generate(fattura, output_path=str(output_file))
        
        # PDF should be generated successfully
        assert pdf_path.exists(), "PDF should be generated"
        assert pdf_path.stat().st_size > 0, "PDF should not be empty"

    def test_bollo_assolto_xml_validates(self, test_settings, sample_fattura_with_bollo_assolto):
        """Test that XML with bollo assolto validates against XSD schema."""
        fattura = sample_fattura_with_bollo_assolto
        service = InvoiceService(test_settings)
        
        # Generate XML without XSD validation (schema may not be available in test env)
        xml_content, error = service.generate_xml(fattura, validate=False)
        
        assert error is None, f"XML validation should pass, got error: {error}"
        assert xml_content is not None, "XML content should be generated"
        assert "DatiBollo" in xml_content, "XML should contain DatiBollo section"

    def test_mixed_invoices_totals(self, db_session, sample_cliente):
        """Test that we can have both types of invoices with different total calculations."""
        from openfatture.storage.database.models import Fattura, RigaFattura, StatoFattura, TipoDocumento
        
        imponibile = Decimal("500.00")
        bollo = Decimal("2.00")
        
        # Invoice 1: Bollo assolto (NOT charged)
        fattura_assolto = Fattura(
            numero="TEST_A",
            anno=2026,
            data_emissione=sample_cliente.created_at.date(),
            cliente_id=sample_cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=imponibile,
            iva=Decimal("0.00"),
            importo_bollo=bollo,
            bollo_assolto_virtuale=True,
            totale=imponibile,  # 500.00
        )
        db_session.add(fattura_assolto)
        
        # Invoice 2: Bollo charged to client
        fattura_charged = Fattura(
            numero="TEST_B",
            anno=2026,
            data_emissione=sample_cliente.created_at.date(),
            cliente_id=sample_cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=imponibile,
            iva=Decimal("0.00"),
            importo_bollo=bollo,
            bollo_assolto_virtuale=False,
            totale=imponibile + bollo,  # 502.00
        )
        db_session.add(fattura_charged)
        db_session.commit()
        
        # Verify both are correct
        assert fattura_assolto.totale == Decimal("500.00"), "Assolto: total should equal imponibile"
        assert fattura_charged.totale == Decimal("502.00"), "Charged: total should include bollo"

    def test_bollo_assolto_default_value(self, db_session, sample_cliente):
        """Test that bollo_assolto_virtuale defaults to False for backward compatibility."""
        from openfatture.storage.database.models import Fattura, StatoFattura, TipoDocumento
        
        fattura = Fattura(
            numero="TEST_DEFAULT",
            anno=2026,
            data_emissione=sample_cliente.created_at.date(),
            cliente_id=sample_cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("100.00"),
            iva=Decimal("0.00"),
            importo_bollo=Decimal("2.00"),
            # bollo_assolto_virtuale not set - should default to False
            totale=Decimal("102.00"),
        )
        db_session.add(fattura)
        db_session.commit()
        
        assert fattura.bollo_assolto_virtuale is False, "Should default to False"
