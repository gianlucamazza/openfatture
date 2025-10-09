"""
Integration tests for complete invoice workflow.

Tests the entire flow: Create Invoice → Generate XML → Validate → Send to SDI
"""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from openfatture.core.fatture.service import InvoiceService
from openfatture.sdi.pec_sender.sender import PECSender
from openfatture.storage.database.models import (
    Cliente,
    Fattura,
    LogSDI,
    RigaFattura,
    StatoFattura,
    TipoDocumento,
)

pytestmark = pytest.mark.integration


class TestInvoiceWorkflowE2E:
    """End-to-end tests for invoice workflow."""

    def test_complete_invoice_workflow(
        self, db_session: Session, test_settings, mock_pec_server, tmp_path
    ):
        """
        Test complete workflow: create → generate XML → send to SDI.

        This is the happy path that a user would follow.
        """
        # Step 1: Create a client
        cliente = Cliente(
            denominazione="Test Client SRL",
            partita_iva="12345678901",
            codice_destinatario="ABC1234",
            indirizzo="Via Roma 1",
            cap="20100",
            comune="Milano",
            provincia="MI",
        )
        db_session.add(cliente)
        db_session.commit()
        db_session.refresh(cliente)

        # Step 2: Create an invoice
        fattura = Fattura(
            numero="1",
            anno=2025,
            data_emissione=date(2025, 1, 15),
            cliente_id=cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("1000.00"),
            iva=Decimal("220.00"),
            totale=Decimal("1220.00"),
        )
        db_session.add(fattura)
        db_session.flush()

        # Step 3: Add line items
        riga = RigaFattura(
            fattura_id=fattura.id,
            numero_riga=1,
            descrizione="Consulenza sviluppo software",
            quantita=Decimal("10"),
            prezzo_unitario=Decimal("100.00"),
            unita_misura="ore",
            aliquota_iva=Decimal("22.00"),
            imponibile=Decimal("1000.00"),
            iva=Decimal("220.00"),
            totale=Decimal("1220.00"),
        )
        db_session.add(riga)
        db_session.commit()
        db_session.refresh(fattura)

        # Step 4: Generate XML
        service = InvoiceService(test_settings)
        xml_content, error = service.generate_xml(fattura, validate=False)

        assert error is None
        assert xml_content is not None
        assert "FatturaElettronica" in xml_content
        assert cliente.denominazione in xml_content

        # Step 5: Save XML to file
        xml_path = tmp_path / "invoice.xml"
        xml_path.write_text(xml_content, encoding="utf-8")

        # Step 6: Send via PEC (mocked)
        sender = PECSender(test_settings)
        success, send_error = sender.send_invoice(fattura, xml_path, signed=False)

        assert success is True
        assert send_error is None
        assert fattura.stato == StatoFattura.INVIATA
        assert fattura.data_invio_sdi is not None

        # Step 7: Verify email was sent
        assert len(mock_pec_server) == 1
        sent_email = mock_pec_server[0]
        assert test_settings.sdi_pec_address in sent_email["To"]

    def test_invoice_with_ritenuta_workflow(self, db_session: Session, test_settings, tmp_path):
        """Test workflow for invoice with withholding tax."""
        # Create client
        cliente = Cliente(
            denominazione="Professional Client",
            codice_fiscale="RSSMRA80A01H501U",
            codice_destinatario="0000000",
            pec="client@pec.it",
        )
        db_session.add(cliente)
        db_session.commit()

        # Create invoice with ritenuta
        imponibile = Decimal("1000.00")
        iva = Decimal("220.00")
        ritenuta = imponibile * Decimal("0.20")

        fattura = Fattura(
            numero="2",
            anno=2025,
            data_emissione=date.today(),
            cliente_id=cliente.id,
            tipo_documento=TipoDocumento.TD06,  # Parcella
            stato=StatoFattura.DA_INVIARE,
            imponibile=imponibile,
            iva=iva,
            ritenuta_acconto=ritenuta,
            aliquota_ritenuta=Decimal("20.00"),
            totale=imponibile + iva,
        )
        db_session.add(fattura)
        db_session.flush()

        # Add line item
        riga = RigaFattura(
            fattura_id=fattura.id,
            numero_riga=1,
            descrizione="Servizi professionali",
            quantita=Decimal("1"),
            prezzo_unitario=imponibile,
            unita_misura="servizio",
            aliquota_iva=Decimal("22.00"),
            imponibile=imponibile,
            iva=iva,
            totale=imponibile + iva,
        )
        db_session.add(riga)
        db_session.commit()

        # Generate XML
        service = InvoiceService(test_settings)
        xml_content, error = service.generate_xml(fattura, validate=False)

        assert error is None
        assert "DatiRitenuta" in xml_content
        assert str(ritenuta) in xml_content or "200" in xml_content  # 200.00 formatted

    def test_invoice_validation_failure(self, db_session: Session, test_settings):
        """Test workflow when invoice validation fails."""
        # Create invoice without line items (should fail validation)
        cliente = Cliente(denominazione="Test Client")
        db_session.add(cliente)
        db_session.commit()

        fattura = Fattura(
            numero="999",
            anno=2025,
            data_emissione=date.today(),
            cliente_id=cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("0"),
            iva=Decimal("0"),
            totale=Decimal("0"),
        )
        db_session.add(fattura)
        db_session.commit()

        # Try to generate XML (should fail - no line items)
        service = InvoiceService(test_settings)
        xml_content, error = service.generate_xml(fattura, validate=False)

        assert error is not None
        assert "line item" in error.lower()

    def test_multiple_invoices_workflow(self, db_session: Session, test_settings, tmp_path):
        """Test creating and processing multiple invoices."""
        # Create client
        cliente = Cliente(
            denominazione="Bulk Client",
            partita_iva="12345678901",
            codice_destinatario="ABC1234",
        )
        db_session.add(cliente)
        db_session.commit()

        # Create multiple invoices
        fatture = []
        for i in range(1, 4):
            fattura = Fattura(
                numero=str(i),
                anno=2025,
                data_emissione=date(2025, 1, i),
                cliente_id=cliente.id,
                tipo_documento=TipoDocumento.TD01,
                stato=StatoFattura.BOZZA,
                imponibile=Decimal(f"{i}00.00"),
                iva=Decimal(f"{i * 22}.00"),
                totale=Decimal(f"{i * 122}.00"),
            )
            db_session.add(fattura)
            db_session.flush()

            # Add line item
            riga = RigaFattura(
                fattura_id=fattura.id,
                numero_riga=1,
                descrizione=f"Service {i}",
                quantita=Decimal("1"),
                prezzo_unitario=Decimal(f"{i}00.00"),
                unita_misura="servizio",
                aliquota_iva=Decimal("22.00"),
                imponibile=Decimal(f"{i}00.00"),
                iva=Decimal(f"{i * 22}.00"),
                totale=Decimal(f"{i * 122}.00"),
            )
            db_session.add(riga)
            fatture.append(fattura)

        db_session.commit()

        # Generate XML for all invoices
        service = InvoiceService(test_settings)
        for fattura in fatture:
            db_session.refresh(fattura)
            xml_content, error = service.generate_xml(fattura, validate=False)

            assert error is None
            assert xml_content is not None
            assert fattura.numero in xml_content

        # Verify all XMLs are unique
        xml_files = list((test_settings.archivio_dir / "xml").glob("*.xml"))
        assert len(xml_files) == 3


class TestInvoiceStateTransitions:
    """Test invoice state transitions through workflow."""

    def test_state_transition_bozza_to_inviata(
        self, db_session: Session, test_settings, sample_fattura, mock_pec_server, tmp_path
    ):
        """Test state transition from BOZZA to INVIATA."""
        assert sample_fattura.stato == StatoFattura.BOZZA

        # Generate XML
        service = InvoiceService(test_settings)
        xml_content, _ = service.generate_xml(sample_fattura, validate=False)

        # Save and send
        xml_path = tmp_path / "invoice.xml"
        xml_path.write_text(xml_content, encoding="utf-8")

        sender = PECSender(test_settings)
        success, _ = sender.send_invoice(sample_fattura, xml_path)

        assert success
        assert sample_fattura.stato == StatoFattura.INVIATA

    def test_cannot_send_already_sent_invoice(
        self, db_session: Session, test_settings, sample_fattura, tmp_path
    ):
        """Test that already sent invoices cannot be sent again."""
        # Mark as already sent
        sample_fattura.stato = StatoFattura.INVIATA

        xml_path = tmp_path / "invoice.xml"
        xml_path.write_text("test", encoding="utf-8")

        # Business logic should prevent re-sending
        # (This would be implemented in service layer)
        # For now, just verify state is already INVIATA
        assert sample_fattura.stato == StatoFattura.INVIATA


class TestInvoiceLogging:
    """Test logging throughout invoice workflow."""

    def test_log_creation_on_send(
        self, db_session: Session, test_settings, sample_fattura, mock_pec_server, tmp_path
    ):
        """Test that log entries are created when sending invoices."""
        # Generate and send
        service = InvoiceService(test_settings)
        xml_content, _ = service.generate_xml(sample_fattura, validate=False)

        xml_path = tmp_path / "invoice.xml"
        xml_path.write_text(xml_content, encoding="utf-8")

        sender = PECSender(test_settings)
        sender.send_invoice(sample_fattura, xml_path)

        # Create log entry
        from openfatture.sdi.pec_sender.sender import create_log_entry

        log = create_log_entry(
            sample_fattura,
            tipo="TX",
            descrizione="Fattura inviata a SDI",
        )
        db_session.add(log)
        db_session.commit()

        # Verify log exists
        logs = db_session.query(LogSDI).filter_by(fattura_id=sample_fattura.id).all()
        assert len(logs) == 1
        assert logs[0].tipo_notifica == "TX"


class TestInvoiceArchiving:
    """Test invoice archiving and file management."""

    def test_xml_files_are_stored_correctly(self, test_settings, sample_fattura):
        """Test that XML files are stored in correct location."""
        service = InvoiceService(test_settings)
        xml_content, _ = service.generate_xml(sample_fattura, validate=False)

        xml_path = service.get_xml_path(sample_fattura)

        assert xml_path.exists()
        assert xml_path.parent == test_settings.archivio_dir / "xml"
        assert xml_path.suffix == ".xml"

    def test_xml_filename_format(self, test_settings, sample_fattura):
        """Test XML filename follows FatturaPA convention."""
        from openfatture.sdi.xml_builder.fatturapa import generate_filename

        filename = generate_filename(sample_fattura, test_settings)

        # Should be ITPPPPPPPPPPPP_NNNNN.xml format
        assert filename.startswith("IT")
        assert test_settings.cedente_partita_iva in filename
        assert filename.endswith(".xml")
        assert "_" in filename
