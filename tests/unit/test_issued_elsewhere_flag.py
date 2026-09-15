"""Tests for issued_elsewhere flag functionality (Issue #71).

Tests that when issued_elsewhere=True:
- XML generation is blocked
- SDI sending is blocked
- Appropriate error messages are returned
- Flag is visible and can be queried
"""

from decimal import Decimal

import pytest

from openfatture.billing.fatture.service import InvoiceService
from openfatture.sdi.application.invoice_sdi_ops import send_invoice_to_sdi, validate_invoice_xml
from openfatture.storage.database.models import Fattura, RigaFattura, StatoFattura, TipoDocumento


class TestIssuedElsewhereFlag:
    """Test issued_elsewhere flag (STORICO/calibration invoices)."""

    def test_issued_elsewhere_default_value(self, db_session, sample_cliente):
        """Test that issued_elsewhere defaults to False for backward compatibility."""
        fattura = Fattura(
            numero="TEST_DEFAULT",
            anno=2026,
            data_emissione=sample_cliente.created_at.date(),
            cliente_id=sample_cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("100.00"),
            iva=Decimal("0.00"),
            totale=Decimal("100.00"),
        )
        db_session.add(fattura)
        db_session.commit()
        
        assert fattura.issued_elsewhere is False, "Should default to False"

    def test_issued_elsewhere_flag_can_be_set(self, db_session, sample_cliente):
        """Test that issued_elsewhere flag can be set to True."""
        fattura = Fattura(
            numero="STORICO_1",
            anno=2026,
            data_emissione=sample_cliente.created_at.date(),
            cliente_id=sample_cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("960.00"),
            iva=Decimal("0.00"),
            totale=Decimal("960.00"),
            issued_elsewhere=True,  # Mark as issued elsewhere
        )
        db_session.add(fattura)
        db_session.commit()
        
        assert fattura.issued_elsewhere is True
        
        # Verify it can be queried
        fetched = db_session.query(Fattura).filter_by(issued_elsewhere=True).first()
        assert fetched is not None
        assert fetched.numero == "STORICO_1"

    def test_xml_generation_blocked_when_issued_elsewhere(self, test_settings, db_session, sample_cliente):
        """Test that XML generation is blocked for invoices issued elsewhere."""
        # Create invoice marked as issued elsewhere
        fattura = Fattura(
            numero="CFAIB_2_2026",
            anno=2026,
            data_emissione=sample_cliente.created_at.date(),
            cliente_id=sample_cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("960.00"),
            iva=Decimal("0.00"),
            totale=Decimal("960.00"),
            issued_elsewhere=True,
        )
        db_session.add(fattura)
        db_session.flush()
        
        # Add a line item
        riga = RigaFattura(
            fattura_id=fattura.id,
            numero_riga=1,
            descrizione="Test service",
            quantita=Decimal("1"),
            prezzo_unitario=Decimal("960.00"),
            unita_misura="servizio",
            aliquota_iva=Decimal("0.00"),
            natura="N2.2",
            imponibile=Decimal("960.00"),
            iva=Decimal("0.00"),
            totale=Decimal("960.00"),
        )
        db_session.add(riga)
        db_session.commit()
        
        # Try to generate XML
        service = InvoiceService(test_settings)
        xml_content, error = service.generate_xml(fattura, validate=False)
        
        # Should return empty content and error message
        assert xml_content == "", "XML content should be empty"
        assert error is not None, "Should return an error"
        assert "issued elsewhere" in error.lower(), f"Error should mention 'issued elsewhere': {error}"
        assert "CFAIB_2_2026" in error, f"Error should mention invoice number: {error}"

    def test_xml_generation_works_when_not_issued_elsewhere(self, test_settings, db_session, sample_cliente):
        """Test that XML generation works normally when issued_elsewhere=False."""
        # Create normal invoice
        fattura = Fattura(
            numero="NORMAL_1",
            anno=2026,
            data_emissione=sample_cliente.created_at.date(),
            cliente_id=sample_cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("100.00"),
            iva=Decimal("22.00"),
            totale=Decimal("122.00"),
            issued_elsewhere=False,
        )
        db_session.add(fattura)
        db_session.flush()
        
        # Add a line item
        riga = RigaFattura(
            fattura_id=fattura.id,
            numero_riga=1,
            descrizione="Test service",
            quantita=Decimal("1"),
            prezzo_unitario=Decimal("100.00"),
            unita_misura="servizio",
            aliquota_iva=Decimal("22.00"),
            imponibile=Decimal("100.00"),
            iva=Decimal("22.00"),
            totale=Decimal("122.00"),
        )
        db_session.add(riga)
        db_session.commit()
        
        # Generate XML
        service = InvoiceService(test_settings)
        xml_content, error = service.generate_xml(fattura, validate=False)
        
        # Should succeed
        assert error is None, f"Should not return error: {error}"
        assert xml_content != "", "XML content should not be empty"
        assert "<FatturaElettronica" in xml_content, "Should contain XML"

    def test_validate_xml_tool_blocked_when_issued_elsewhere(self, runtime_db, sample_cliente):
        """Test that validate_invoice_xml tool blocks invoices issued elsewhere."""
        # Create session from runtime_db
        session = runtime_db()
        
        # Create invoice marked as issued elsewhere
        fattura = Fattura(
            numero="STORICO_CALIB",
            anno=2026,
            data_emissione=sample_cliente.created_at.date(),
            cliente_id=sample_cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("960.00"),
            iva=Decimal("0.00"),
            totale=Decimal("960.00"),
            issued_elsewhere=True,
        )
        session.add(fattura)
        session.flush()
        
        # Add a line item
        riga = RigaFattura(
            fattura_id=fattura.id,
            numero_riga=1,
            descrizione="Historical calibration invoice",
            quantita=Decimal("1"),
            prezzo_unitario=Decimal("960.00"),
            unita_misura="servizio",
            aliquota_iva=Decimal("0.00"),
            natura="N2.2",
            imponibile=Decimal("960.00"),
            iva=Decimal("0.00"),
            totale=Decimal("960.00"),
        )
        session.add(riga)
        session.commit()
        
        # Save ID before closing session
        fattura_id = fattura.id
        session.close()
        
        # Try to validate via tool
        result = validate_invoice_xml(fattura_id)
        
        # Should block with error
        assert "error" in result, f"Should return error: {result}"
        assert "issued elsewhere" in result["error"].lower(), f"Error should mention 'issued elsewhere': {result}"

    def test_send_to_sdi_blocked_when_issued_elsewhere(self, runtime_db, sample_cliente):
        """Test that send_invoice_to_sdi blocks invoices issued elsewhere."""
        # Create session from runtime_db
        session = runtime_db()
        
        # Create invoice marked as issued elsewhere
        fattura = Fattura(
            numero="MUM_ISSUED",
            anno=2026,
            data_emissione=sample_cliente.created_at.date(),
            cliente_id=sample_cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("960.00"),
            iva=Decimal("0.00"),
            totale=Decimal("960.00"),
            issued_elsewhere=True,
        )
        session.add(fattura)
        session.flush()
        
        # Add a line item
        riga = RigaFattura(
            fattura_id=fattura.id,
            numero_riga=1,
            descrizione="Issued by mum",
            quantita=Decimal("1"),
            prezzo_unitario=Decimal("960.00"),
            unita_misura="servizio",
            aliquota_iva=Decimal("0.00"),
            natura="N2.2",
            imponibile=Decimal("960.00"),
            iva=Decimal("0.00"),
            totale=Decimal("960.00"),
        )
        session.add(riga)
        session.commit()
        
        # Save ID before closing session
        fattura_id = fattura.id
        session.close()
        
        # Try to send to SDI
        result = send_invoice_to_sdi(fattura_id)
        
        # Should block with error
        assert "error" in result, f"Should return error: {result}"
        assert "issued elsewhere" in result["error"].lower(), f"Error should mention 'issued elsewhere': {result}"
        assert "duplicate" in result["error"].lower(), f"Error should mention 'duplicate': {result}"

    def test_query_issued_elsewhere_invoices(self, db_session, sample_cliente):
        """Test querying for issued_elsewhere invoices."""
        # Create mix of invoices
        for i in range(5):
            fattura = Fattura(
                numero=f"INV_{i}",
                anno=2026,
                data_emissione=sample_cliente.created_at.date(),
                cliente_id=sample_cliente.id,
                tipo_documento=TipoDocumento.TD01,
                stato=StatoFattura.BOZZA,
                imponibile=Decimal("100.00"),
                iva=Decimal("0.00"),
                totale=Decimal("100.00"),
                issued_elsewhere=(i % 2 == 0),  # Even numbers issued elsewhere
            )
            db_session.add(fattura)
        
        db_session.commit()
        
        # Query issued elsewhere
        issued_elsewhere = db_session.query(Fattura).filter_by(issued_elsewhere=True).all()
        assert len(issued_elsewhere) == 3, "Should have 3 invoices issued elsewhere"
        
        # Query normal invoices
        normal = db_session.query(Fattura).filter_by(issued_elsewhere=False).all()
        assert len(normal) == 2, "Should have 2 normal invoices"
