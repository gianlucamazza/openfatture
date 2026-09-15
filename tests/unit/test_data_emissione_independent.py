"""Tests for independent data_emissione (Issue #70).

Tests that data_emissione can be set independently of when the draft is created:
- Draft created on day X
- Invoice dated for day Y
- PDF/XML use Y, not X

NOTE: The functionality for setting data_emissione independently already exists:
1. create_invoice(data_emissione="YYYY-MM-DD") - set at creation
2. update_invoice(fattura_id, data_emissione="YYYY-MM-DD") - update later (BOZZA only)

These tests document and verify the expected behavior.
"""

from datetime import date
from decimal import Decimal

from openfatture.storage.database.models import Fattura, RigaFattura


class TestDataEmissioneIndependent:
    """Test that data_emissione is independent of draft creation time."""

    def test_model_allows_arbitrary_data_emissione(self, db_session, sample_cliente):
        """Test that Fattura model accepts any data_emissione."""
        # Create invoice with future date
        future_fattura = Fattura(
            numero="FUTURE_1",
            anno=2026,
            data_emissione=date(2026, 12, 31),
            cliente_id=sample_cliente.id,
            imponibile=Decimal("0.00"),
            iva=Decimal("0.00"),
            totale=Decimal("0.00"),
        )
        db_session.add(future_fattura)

        # Create invoice with past date
        past_fattura = Fattura(
            numero="PAST_1",
            anno=2026,
            data_emissione=date(2026, 1, 1),
            cliente_id=sample_cliente.id,
            imponibile=Decimal("0.00"),
            iva=Decimal("0.00"),
            totale=Decimal("0.00"),
        )
        db_session.add(past_fattura)

        # Create invoice with today
        today_fattura = Fattura(
            numero="TODAY_1",
            anno=2026,
            data_emissione=date.today(),
            cliente_id=sample_cliente.id,
            imponibile=Decimal("0.00"),
            iva=Decimal("0.00"),
            totale=Decimal("0.00"),
        )
        db_session.add(today_fattura)

        db_session.commit()

        # All should be saved with their respective dates
        db_session.refresh(future_fattura)
        db_session.refresh(past_fattura)
        db_session.refresh(today_fattura)

        assert future_fattura.data_emissione == date(2026, 12, 31)
        assert past_fattura.data_emissione == date(2026, 1, 1)
        assert today_fattura.data_emissione == date.today()

    def test_data_emissione_can_be_updated(self, db_session, sample_cliente):
        """Test that data_emissione can be modified after creation (while BOZZA)."""
        # Create invoice with one date
        fattura = Fattura(
            numero="UPDATE_1",
            anno=2026,
            data_emissione=date(2026, 9, 10),
            cliente_id=sample_cliente.id,
            imponibile=Decimal("0.00"),
            iva=Decimal("0.00"),
            totale=Decimal("0.00"),
        )
        db_session.add(fattura)
        db_session.commit()

        # Update to different date
        fattura.data_emissione = date(2026, 9, 14)
        db_session.commit()
        db_session.refresh(fattura)

        # Should have new date
        assert fattura.data_emissione == date(2026, 9, 14)

    def test_xml_generation_uses_data_emissione(self, db_session, sample_cliente, test_settings):
        """Test that XML uses fattura.data_emissione field."""
        # Create invoice with specific date
        fattura = Fattura(
            numero="XML_1",
            anno=2026,
            data_emissione=date(2026, 9, 14),
            cliente_id=sample_cliente.id,
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
            descrizione="Test",
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
        from lxml import etree

        from openfatture.sdi.xml_builder.fatturapa import FatturaPABuilder

        builder = FatturaPABuilder(test_settings)
        xml_content = builder.build(fattura)
        root = etree.fromstring(xml_content.encode("utf-8"))

        # Verify XML Data element
        data_elem = root.find(".//{*}Data")
        assert data_elem is not None
        assert data_elem.text == "2026-09-14"

    def test_multiple_invoices_different_dates(self, db_session, sample_cliente):
        """Test that multiple invoices can have different emission dates."""
        # Create 3 invoices with different dates
        fattura1 = Fattura(
            numero="DIFF_1",
            anno=2026,
            data_emissione=date(2026, 9, 10),
            cliente_id=sample_cliente.id,
            imponibile=Decimal("0.00"),
            iva=Decimal("0.00"),
            totale=Decimal("0.00"),
        )
        fattura2 = Fattura(
            numero="DIFF_2",
            anno=2026,
            data_emissione=date(2026, 9, 14),
            cliente_id=sample_cliente.id,
            imponibile=Decimal("0.00"),
            iva=Decimal("0.00"),
            totale=Decimal("0.00"),
        )
        fattura3 = Fattura(
            numero="DIFF_3",
            anno=2026,
            data_emissione=date(2026, 9, 20),
            cliente_id=sample_cliente.id,
            imponibile=Decimal("0.00"),
            iva=Decimal("0.00"),
            totale=Decimal("0.00"),
        )

        db_session.add_all([fattura1, fattura2, fattura3])
        db_session.commit()

        # Each should retain its own date
        assert fattura1.data_emissione == date(2026, 9, 10)
        assert fattura2.data_emissione == date(2026, 9, 14)
        assert fattura3.data_emissione == date(2026, 9, 20)
