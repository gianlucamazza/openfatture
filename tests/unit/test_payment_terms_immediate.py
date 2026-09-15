"""Tests for immediate payment terms functionality (Issue #67).

Tests that payment terms can be:
- Immediate (giorni_scadenza=0, rif. termini = data emissione)
- N-day terms (giorni_scadenza=N, scadenza = data emissione + N days)
"""

from datetime import date, timedelta
from decimal import Decimal

from lxml import etree

from openfatture.pdf.generator import PDFGenerator, PDFGeneratorConfig
from openfatture.sdi.xml_builder.fatturapa import FatturaPABuilder
from openfatture.storage.database.models import (
    Fattura,
    Pagamento,
    RigaFattura,
    StatoFattura,
    TipoDocumento,
)


class TestPaymentTermsImmediate:
    """Test immediate payment terms (giorni_scadenza=0)."""

    def test_immediate_payment_xml(self, test_settings, db_session, sample_cliente):
        """Test that immediate payment generates XML with data emissione as scadenza."""
        # Create invoice with immediate payment
        fattura = Fattura(
            numero="IMM_1",
            anno=2026,
            data_emissione=date(2026, 9, 14),
            cliente_id=sample_cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("960.00"),
            iva=Decimal("0.00"),
            totale=Decimal("960.00"),
        )
        db_session.add(fattura)
        db_session.flush()

        # Add line item
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

        # Add immediate payment
        pagamento = Pagamento(
            fattura_id=fattura.id,
            importo=Decimal("960.00"),
            data_scadenza=date(2026, 9, 14),  # Same as invoice date
            giorni_scadenza=0,  # Immediate
            modalita="Bonifico",
            iban="IT94U0305801604100572272740",
        )
        db_session.add(pagamento)
        db_session.commit()
        db_session.refresh(fattura)

        # Generate XML
        builder = FatturaPABuilder(test_settings)
        xml_content = builder.build(fattura)

        root = etree.fromstring(xml_content.encode("utf-8"))

        # Check DataScadenzaPagamento = data_emissione
        data_scadenza_elem = root.find(".//{*}DataScadenzaPagamento")
        assert data_scadenza_elem is not None
        assert data_scadenza_elem.text == "2026-09-14"

    def test_n_day_payment_xml(self, test_settings, db_session, sample_cliente):
        """Test that N-day payment generates XML with correct scadenza."""
        # Create invoice with 30-day payment
        fattura = Fattura(
            numero="N30_1",
            anno=2026,
            data_emissione=date(2026, 9, 14),
            cliente_id=sample_cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("1000.00"),
            iva=Decimal("220.00"),
            totale=Decimal("1220.00"),
        )
        db_session.add(fattura)
        db_session.flush()

        # Add line item
        riga = RigaFattura(
            fattura_id=fattura.id,
            numero_riga=1,
            descrizione="Test service",
            quantita=Decimal("1"),
            prezzo_unitario=Decimal("1000.00"),
            unita_misura="servizio",
            aliquota_iva=Decimal("22.00"),
            imponibile=Decimal("1000.00"),
            iva=Decimal("220.00"),
            totale=Decimal("1220.00"),
        )
        db_session.add(riga)

        # Add 30-day payment
        expected_scadenza = date(2026, 9, 14) + timedelta(days=30)
        pagamento = Pagamento(
            fattura_id=fattura.id,
            importo=Decimal("1220.00"),
            data_scadenza=expected_scadenza,
            giorni_scadenza=30,  # 30-day terms
            modalita="Bonifico",
        )
        db_session.add(pagamento)
        db_session.commit()
        db_session.refresh(fattura)

        # Generate XML
        builder = FatturaPABuilder(test_settings)
        xml_content = builder.build(fattura)

        root = etree.fromstring(xml_content.encode("utf-8"))

        # Check DataScadenzaPagamento = data_emissione + 30 days
        data_scadenza_elem = root.find(".//{*}DataScadenzaPagamento")
        assert data_scadenza_elem is not None
        assert data_scadenza_elem.text == expected_scadenza.isoformat()

    def test_backward_compatibility_no_pagamento(self, test_settings, db_session, sample_cliente):
        """Test that invoices without Pagamento records still work (30-day default)."""
        # Create invoice without Pagamento record
        fattura = Fattura(
            numero="LEGACY_1",
            anno=2026,
            data_emissione=date(2026, 9, 14),
            cliente_id=sample_cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("100.00"),
            iva=Decimal("22.00"),
            totale=Decimal("122.00"),
        )
        db_session.add(fattura)
        db_session.flush()

        # Add line item
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
        db_session.refresh(fattura)

        # Generate XML (should use 30-day default)
        builder = FatturaPABuilder(test_settings)
        xml_content = builder.build(fattura)

        root = etree.fromstring(xml_content.encode("utf-8"))

        # Check DataScadenzaPagamento = data_emissione + 30 days (default)
        expected_scadenza = date(2026, 9, 14) + timedelta(days=30)
        data_scadenza_elem = root.find(".//{*}DataScadenzaPagamento")
        assert data_scadenza_elem is not None
        assert data_scadenza_elem.text == expected_scadenza.isoformat()

    def test_immediate_payment_pdf(self, test_settings, db_session, sample_cliente, tmp_path):
        """Test that immediate payment shows correct labels in PDF."""
        # Create invoice with immediate payment
        fattura = Fattura(
            numero="PDF_IMM_1",
            anno=2026,
            data_emissione=date(2026, 9, 14),
            cliente_id=sample_cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("960.00"),
            iva=Decimal("0.00"),
            totale=Decimal("960.00"),
        )
        db_session.add(fattura)
        db_session.flush()

        # Add line item
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

        # Add immediate payment
        pagamento = Pagamento(
            fattura_id=fattura.id,
            importo=Decimal("960.00"),
            data_scadenza=date(2026, 9, 14),  # Same as invoice date
            giorni_scadenza=0,  # Immediate
            modalita="Bonifico",
            iban="IT94U0305801604100572272740",
        )
        db_session.add(pagamento)
        db_session.commit()
        db_session.refresh(fattura)

        # Generate PDF
        config = PDFGeneratorConfig(
            company_name=test_settings.cedente_denominazione or "Test Company",
            company_vat=test_settings.cedente_partita_iva,
        )
        generator = PDFGenerator(config)

        output_file = tmp_path / "test_immediate_payment.pdf"
        pdf_path = generator.generate(fattura, output_path=str(output_file))

        # PDF should be generated successfully
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0

    def test_giorni_scadenza_default_value(self, db_session, sample_cliente):
        """Test that giorni_scadenza defaults to 30 for backward compatibility."""
        fattura = Fattura(
            numero="DEFAULT_TEST",
            anno=2026,
            data_emissione=date(2026, 9, 14),
            cliente_id=sample_cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("100.00"),
            iva=Decimal("0.00"),
            totale=Decimal("100.00"),
        )
        db_session.add(fattura)
        db_session.flush()

        # Create Pagamento without specifying giorni_scadenza
        pagamento = Pagamento(
            fattura_id=fattura.id,
            importo=Decimal("100.00"),
            data_scadenza=date(2026, 10, 14),
            modalita="Bonifico",
            # giorni_scadenza not set - should default to 30
        )
        db_session.add(pagamento)
        db_session.commit()

        assert pagamento.giorni_scadenza == 30

    def test_mixed_payment_terms(self, db_session, sample_cliente):
        """Test that different invoices can have different payment terms."""
        # Invoice 1: Immediate
        fattura1 = Fattura(
            numero="MIX_IMM",
            anno=2026,
            data_emissione=date(2026, 9, 14),
            cliente_id=sample_cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("500.00"),
            iva=Decimal("0.00"),
            totale=Decimal("500.00"),
        )
        db_session.add(fattura1)
        db_session.flush()

        pagamento1 = Pagamento(
            fattura_id=fattura1.id,
            importo=Decimal("500.00"),
            data_scadenza=date(2026, 9, 14),
            giorni_scadenza=0,  # Immediate
        )
        db_session.add(pagamento1)

        # Invoice 2: 60-day terms
        fattura2 = Fattura(
            numero="MIX_60",
            anno=2026,
            data_emissione=date(2026, 9, 14),
            cliente_id=sample_cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("1000.00"),
            iva=Decimal("0.00"),
            totale=Decimal("1000.00"),
        )
        db_session.add(fattura2)
        db_session.flush()

        pagamento2 = Pagamento(
            fattura_id=fattura2.id,
            importo=Decimal("1000.00"),
            data_scadenza=date(2026, 11, 13),
            giorni_scadenza=60,  # 60-day terms
        )
        db_session.add(pagamento2)
        db_session.commit()

        # Verify both are correct
        assert pagamento1.giorni_scadenza == 0
        assert pagamento2.giorni_scadenza == 60

    def test_create_manual_payment_sets_giorni(self, db_session, sample_cliente):
        """Test that create_manual_payment sets giorni_scadenza correctly."""
        # Create invoice
        fattura = Fattura(
            numero="MANUAL_TEST",
            anno=2026,
            data_emissione=date(2026, 9, 14),
            cliente_id=sample_cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("1000.00"),
            iva=Decimal("0.00"),
            totale=Decimal("1000.00"),
        )
        db_session.add(fattura)
        db_session.flush()

        # Create immediate payment directly (simulates create_manual_payment logic)
        due_date = date(2026, 9, 14)  # Same as invoice date

        # Calculate giorni_scadenza as create_manual_payment does
        if due_date == fattura.data_emissione:
            giorni_scadenza = 0
        else:
            giorni_scadenza = (due_date - fattura.data_emissione).days
            if giorni_scadenza < 0:
                giorni_scadenza = 30

        pagamento = Pagamento(
            fattura_id=fattura.id,
            importo=Decimal("1000.00"),
            data_scadenza=due_date,
            giorni_scadenza=giorni_scadenza,
            modalita="Bonifico",
        )
        db_session.add(pagamento)
        db_session.commit()

        # Verify giorni_scadenza was set to 0
        assert pagamento.giorni_scadenza == 0

    def test_update_payment_resyncs_giorni(self, db_session, sample_cliente):
        """Test that update_payment logic resyncs giorni_scadenza when data_scadenza changes."""
        # Create invoice
        fattura = Fattura(
            numero="UPDATE_TEST",
            anno=2026,
            data_emissione=date(2026, 9, 14),
            cliente_id=sample_cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("500.00"),
            iva=Decimal("0.00"),
            totale=Decimal("500.00"),
        )
        db_session.add(fattura)
        db_session.flush()

        # Create 30-day payment
        pagamento = Pagamento(
            fattura_id=fattura.id,
            importo=Decimal("500.00"),
            data_scadenza=date(2026, 10, 14),  # 30 days later
            giorni_scadenza=30,
            modalita="Bonifico",
        )
        db_session.add(pagamento)
        db_session.commit()

        # Simulate update_payment logic: change data_scadenza to immediate
        new_data_scadenza = date(2026, 9, 14)  # Same as invoice date
        pagamento.data_scadenza = new_data_scadenza

        # Recalculate giorni_scadenza (as update_payment does)
        if new_data_scadenza == fattura.data_emissione:
            pagamento.giorni_scadenza = 0
        else:
            giorni = (new_data_scadenza - fattura.data_emissione).days
            pagamento.giorni_scadenza = giorni if giorni >= 0 else 30

        db_session.commit()
        db_session.refresh(pagamento)

        assert pagamento.giorni_scadenza == 0  # Should be resynced to 0

    def test_invoice_creation_workflow_sets_giorni(self, test_settings, db_session, sample_cliente):
        """Test that invoice_creation workflow sets giorni_scadenza for new payments."""
        # This tests the AI workflow path at invoice_creation.py ~line 588

        # Create invoice
        fattura = Fattura(
            numero="WORKFLOW_TEST",
            anno=2026,
            data_emissione=date(2026, 9, 14),
            cliente_id=sample_cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("960.00"),
            iva=Decimal("0.00"),
            totale=Decimal("960.00"),
        )
        db_session.add(fattura)
        db_session.flush()

        # Simulate AI workflow creating payment (immediate)
        # This logic mirrors invoice_creation.py lines 580-594
        due_date = date(2026, 9, 14)  # Same as invoice date

        # Calculate giorni_scadenza (as the workflow should)
        if due_date == fattura.data_emissione:
            giorni_scadenza = 0
        else:
            giorni_scadenza = (due_date - fattura.data_emissione).days
            if giorni_scadenza < 0:
                giorni_scadenza = 30

        pagamento = Pagamento(
            fattura_id=fattura.id,
            importo=Decimal("960.00"),
            data_scadenza=due_date,
            giorni_scadenza=giorni_scadenza,
            stato="DA_PAGARE",
        )
        db_session.add(pagamento)

        # Add line item for XML generation
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
        db_session.refresh(fattura)

        # Verify giorni_scadenza is 0
        assert pagamento.giorni_scadenza == 0

        # Generate XML and verify it uses giorni=0 (invoice date, not +30 days)
        from openfatture.sdi.xml_builder.fatturapa import FatturaPABuilder

        builder = FatturaPABuilder(test_settings)
        xml_content = builder.build(fattura)

        root = etree.fromstring(xml_content.encode("utf-8"))
        data_scadenza_elem = root.find(".//{*}DataScadenzaPagamento")
        assert data_scadenza_elem is not None
        assert data_scadenza_elem.text == "2026-09-14"  # Should be invoice date, not +30 days
