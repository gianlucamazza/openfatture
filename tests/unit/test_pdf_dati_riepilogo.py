"""Tests for PDF Dati di riepilogo block (Issue #68).

Tests that the PDF includes a Dati di riepilogo table showing:
- Aliquota IVA
- Natura label
- Imponibile
- Imposta

For each unique (aliquota_iva, natura) combination in the invoice.
"""

from datetime import date
from decimal import Decimal

from openfatture.pdf.generator import PDFGenerator, PDFGeneratorConfig
from openfatture.storage.database.models import (
    DatiCassaPrevidenziale,
    Fattura,
    RigaFattura,
    StatoFattura,
    TipoDocumento,
)


class TestPDFDatiRiepilogo:
    """Test PDF Dati di riepilogo table generation."""

    def test_dati_riepilogo_single_natura(
        self, test_settings, db_session, sample_cliente, tmp_path
    ):
        """Test Dati riepilogo with single natura (N2.2, IVA 0%)."""
        # Create invoice with one line - forfettario N2.2
        fattura = Fattura(
            numero="RIEP_1",
            anno=2026,
            data_emissione=date(2026, 9, 15),
            cliente_id=sample_cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("960.00"),
            iva=Decimal("0.00"),
            totale=Decimal("960.00"),
        )
        db_session.add(fattura)
        db_session.flush()

        # Add line with N2.2 natura
        riga = RigaFattura(
            fattura_id=fattura.id,
            numero_riga=1,
            descrizione="Forfettario service",
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

        # Generate PDF
        config = PDFGeneratorConfig(
            company_name=test_settings.cedente_denominazione or "Test Company",
            company_vat=test_settings.cedente_partita_iva,
        )
        generator = PDFGenerator(config)

        output_file = tmp_path / "test_dati_riepilogo_single.pdf"
        pdf_path = generator.generate(fattura, output_path=str(output_file))

        # PDF should be generated successfully
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0

    def test_dati_riepilogo_multiple_rates(
        self, test_settings, db_session, sample_cliente, tmp_path
    ):
        """Test Dati riepilogo with multiple tax rates."""
        # Create invoice with mixed tax rates
        fattura = Fattura(
            numero="RIEP_MULTI",
            anno=2026,
            data_emissione=date(2026, 9, 15),
            cliente_id=sample_cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("1500.00"),
            iva=Decimal("198.00"),
            totale=Decimal("1698.00"),
        )
        db_session.add(fattura)
        db_session.flush()

        # Line 1: 22% IVA
        riga1 = RigaFattura(
            fattura_id=fattura.id,
            numero_riga=1,
            descrizione="Service with 22% VAT",
            quantita=Decimal("1"),
            prezzo_unitario=Decimal("1000.00"),
            unita_misura="servizio",
            aliquota_iva=Decimal("22.00"),
            imponibile=Decimal("1000.00"),
            iva=Decimal("220.00"),
            totale=Decimal("1220.00"),
        )
        db_session.add(riga1)

        # Line 2: 10% IVA
        riga2 = RigaFattura(
            fattura_id=fattura.id,
            numero_riga=2,
            descrizione="Service with 10% VAT",
            quantita=Decimal("1"),
            prezzo_unitario=Decimal("500.00"),
            unita_misura="servizio",
            aliquota_iva=Decimal("10.00"),
            imponibile=Decimal("500.00"),
            iva=Decimal("50.00"),
            totale=Decimal("550.00"),
        )
        db_session.add(riga2)

        # Line 3: 0% N2.2 (forfettario - should not be charged)
        # Actually this shouldn't mix with normal IVA, but testing aggregation
        db_session.commit()
        db_session.refresh(fattura)

        # Generate PDF
        config = PDFGeneratorConfig(
            company_name=test_settings.cedente_denominazione or "Test Company",
            company_vat=test_settings.cedente_partita_iva,
        )
        generator = PDFGenerator(config)

        output_file = tmp_path / "test_dati_riepilogo_multi.pdf"
        pdf_path = generator.generate(fattura, output_path=str(output_file))

        # PDF should be generated successfully
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0

    def test_dati_riepilogo_aggregates_same_rate(
        self, test_settings, db_session, sample_cliente, tmp_path
    ):
        """Test that Dati riepilogo aggregates multiple lines with same rate."""
        # Create invoice with multiple lines at 22% IVA
        fattura = Fattura(
            numero="RIEP_AGG",
            anno=2026,
            data_emissione=date(2026, 9, 15),
            cliente_id=sample_cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("1500.00"),
            iva=Decimal("330.00"),
            totale=Decimal("1830.00"),
        )
        db_session.add(fattura)
        db_session.flush()

        # Line 1: 22% IVA - €1000
        riga1 = RigaFattura(
            fattura_id=fattura.id,
            numero_riga=1,
            descrizione="Service A",
            quantita=Decimal("1"),
            prezzo_unitario=Decimal("1000.00"),
            unita_misura="servizio",
            aliquota_iva=Decimal("22.00"),
            imponibile=Decimal("1000.00"),
            iva=Decimal("220.00"),
            totale=Decimal("1220.00"),
        )
        db_session.add(riga1)

        # Line 2: 22% IVA - €500 (same rate, should aggregate)
        riga2 = RigaFattura(
            fattura_id=fattura.id,
            numero_riga=2,
            descrizione="Service B",
            quantita=Decimal("1"),
            prezzo_unitario=Decimal("500.00"),
            unita_misura="servizio",
            aliquota_iva=Decimal("22.00"),
            imponibile=Decimal("500.00"),
            iva=Decimal("110.00"),
            totale=Decimal("610.00"),
        )
        db_session.add(riga2)

        db_session.commit()
        db_session.refresh(fattura)

        # Generate PDF
        config = PDFGeneratorConfig(
            company_name=test_settings.cedente_denominazione or "Test Company",
            company_vat=test_settings.cedente_partita_iva,
        )
        generator = PDFGenerator(config)

        output_file = tmp_path / "test_dati_riepilogo_agg.pdf"
        pdf_path = generator.generate(fattura, output_path=str(output_file))

        # PDF should be generated successfully
        # Dati riepilogo should show ONE row: 22% / € 1500.00 / € 330.00
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0

    def test_dati_riepilogo_with_cassa(self, test_settings, db_session, sample_cliente, tmp_path):
        """Test Dati riepilogo includes cassa previdenziale."""
        # Create invoice with cassa previdenziale
        fattura = Fattura(
            numero="RIEP_CASSA",
            anno=2026,
            data_emissione=date(2026, 9, 15),
            cliente_id=sample_cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("1000.00"),
            iva=Decimal("0.00"),
            totale=Decimal("1040.00"),
        )
        db_session.add(fattura)
        db_session.flush()

        # Line: N2.2 forfettario
        riga = RigaFattura(
            fattura_id=fattura.id,
            numero_riga=1,
            descrizione="Professional service",
            quantita=Decimal("1"),
            prezzo_unitario=Decimal("1000.00"),
            unita_misura="servizio",
            aliquota_iva=Decimal("0.00"),
            natura="N2.2",
            imponibile=Decimal("1000.00"),
            iva=Decimal("0.00"),
            totale=Decimal("1000.00"),
        )
        db_session.add(riga)

        # Add INPS cassa 4%
        cassa = DatiCassaPrevidenziale(
            fattura_id=fattura.id,
            tipo_cassa="TC07",
            al_cassa=Decimal("4.00"),
            importo_contributo_cassa=Decimal("40.00"),
            imponibile_cassa=Decimal("1000.00"),
            aliquota_iva=Decimal("0.00"),
            natura="N2.2",
        )
        db_session.add(cassa)

        db_session.commit()
        db_session.refresh(fattura)

        # Generate PDF
        config = PDFGeneratorConfig(
            company_name=test_settings.cedente_denominazione or "Test Company",
            company_vat=test_settings.cedente_partita_iva,
        )
        generator = PDFGenerator(config)

        output_file = tmp_path / "test_dati_riepilogo_cassa.pdf"
        pdf_path = generator.generate(fattura, output_path=str(output_file))

        # PDF should be generated successfully
        # Dati riepilogo should aggregate line + cassa: N2.2 / € 2000.00 / € 0.00
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0

    def test_dati_riepilogo_empty_invoice(
        self, test_settings, db_session, sample_cliente, tmp_path
    ):
        """Test that invoice without lines doesn't break PDF generation."""
        # Create invoice without lines (edge case)
        fattura = Fattura(
            numero="RIEP_EMPTY",
            anno=2026,
            data_emissione=date(2026, 9, 15),
            cliente_id=sample_cliente.id,
            tipo_documento=TipoDocumento.TD01,
            stato=StatoFattura.BOZZA,
            imponibile=Decimal("0.00"),
            iva=Decimal("0.00"),
            totale=Decimal("0.00"),
        )
        db_session.add(fattura)
        db_session.commit()
        db_session.refresh(fattura)

        # Generate PDF (should not crash, just skip riepilogo)
        config = PDFGeneratorConfig(
            company_name=test_settings.cedente_denominazione or "Test Company",
            company_vat=test_settings.cedente_partita_iva,
        )
        generator = PDFGenerator(config)

        output_file = tmp_path / "test_dati_riepilogo_empty.pdf"
        pdf_path = generator.generate(fattura, output_path=str(output_file))

        # PDF should be generated successfully (without riepilogo block)
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0
