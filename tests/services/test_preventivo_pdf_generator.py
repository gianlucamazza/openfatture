"""Tests for PreventivoPDFGenerator."""

import tempfile
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from openfatture.services.pdf.generator import PDFGeneratorConfig
from openfatture.services.pdf.preventivo_generator import (
    PreventivoPDFGenerator,
    create_preventivo_pdf_generator,
)
from openfatture.storage.database.base import Base
from openfatture.storage.database.models import Cliente, Preventivo, RigaPreventivo, StatoPreventivo


@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()


@pytest.fixture
def test_cliente(db_session: Session) -> Cliente:
    """Create test client."""
    cliente = Cliente(
        denominazione="Test Client SRL",
        partita_iva="12345678901",
        codice_fiscale="12345678901",
        indirizzo="Via Roma 1",
        numero_civico="10",
        cap="00100",
        comune="Roma",
        provincia="RM",
        nazione="IT",
        email="test@example.com",
        telefono="+39 06 12345678",
    )
    db_session.add(cliente)
    db_session.commit()
    db_session.refresh(cliente)
    return cliente


@pytest.fixture
def test_preventivo(db_session: Session, test_cliente: Cliente) -> Preventivo:
    """Create test preventivo."""
    preventivo = Preventivo(
        numero="1",
        anno=2025,
        data_emissione=date.today(),
        data_scadenza=date.today() + timedelta(days=30),
        cliente_id=test_cliente.id,
        validita_giorni=30,
        stato=StatoPreventivo.BOZZA,
        note="Test note for preventivo",
        condizioni="Payment terms: 50% advance, 50% on delivery",
        imponibile=Decimal("1000.00"),
        iva=Decimal("220.00"),
        totale=Decimal("1220.00"),
    )
    db_session.add(preventivo)
    db_session.flush()

    # Add righe
    righe_data = [
        {
            "numero_riga": 1,
            "descrizione": "Consulenza IT",
            "quantita": Decimal("10.00"),
            "prezzo_unitario": Decimal("100.00"),
            "unita_misura": "ore",
            "aliquota_iva": Decimal("22.00"),
        },
    ]

    for riga_data in righe_data:
        imponibile = riga_data["quantita"] * riga_data["prezzo_unitario"]
        iva = imponibile * riga_data["aliquota_iva"] / Decimal("100")
        totale = imponibile + iva

        riga = RigaPreventivo(
            preventivo_id=preventivo.id,
            **riga_data,
            imponibile=imponibile,
            iva=iva,
            totale=totale,
        )
        db_session.add(riga)

    db_session.commit()
    db_session.refresh(preventivo)
    return preventivo


class TestPreventivoPDFGeneratorBasic:
    """Basic tests for PreventivoPDFGenerator."""

    def test_create_pdf_generator(self):
        """Test PreventivoPDFGenerator instantiation."""
        generator = PreventivoPDFGenerator()

        assert generator is not None
        assert generator.config is not None

    def test_create_pdf_generator_with_config(self):
        """Test PreventivoPDFGenerator with custom config."""
        config = PDFGeneratorConfig(
            company_name="Test Company",
            company_vat="12345678901",
            watermark_text="BOZZA",
        )

        generator = PreventivoPDFGenerator(config)

        assert generator.config.company_name == "Test Company"
        assert generator.config.watermark_text == "BOZZA"

    def test_create_preventivo_pdf_generator_factory(self):
        """Test factory function."""
        generator = create_preventivo_pdf_generator(
            company_name="Factory Test",
            watermark_text="TEST",
        )

        assert isinstance(generator, PreventivoPDFGenerator)
        assert generator.config.company_name == "Factory Test"


class TestPreventivoPDFGeneration:
    """Tests for PDF generation."""

    def test_generate_pdf_basic(self, test_preventivo: Preventivo):
        """Test basic PDF generation."""
        generator = PreventivoPDFGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_preventivo.pdf"

            pdf_path = generator.generate(test_preventivo, str(output_path))

            assert pdf_path.exists()
            assert pdf_path.stat().st_size > 0  # File has content
            assert pdf_path.suffix == ".pdf"

    def test_generate_pdf_with_watermark(self, test_preventivo: Preventivo):
        """Test PDF generation with watermark."""
        config = PDFGeneratorConfig(watermark_text="BOZZA")
        generator = PreventivoPDFGenerator(config)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "preventivo_watermark.pdf"

            pdf_path = generator.generate(test_preventivo, str(output_path))

            assert pdf_path.exists()
            assert pdf_path.stat().st_size > 0

    def test_generate_pdf_auto_filename(self, test_preventivo: Preventivo):
        """Test PDF generation with automatic filename."""
        generator = PreventivoPDFGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp directory for auto-generated file
            import os

            original_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                pdf_path = generator.generate(test_preventivo)

                assert pdf_path.exists()
                assert (
                    pdf_path.name
                    == f"preventivo_{test_preventivo.numero}_{test_preventivo.anno}.pdf"
                )
            finally:
                os.chdir(original_cwd)

    def test_generate_pdf_multiple_righe(self, db_session: Session, test_cliente: Cliente):
        """Test PDF generation with multiple line items."""
        preventivo = Preventivo(
            numero="2",
            anno=2025,
            data_emissione=date.today(),
            data_scadenza=date.today() + timedelta(days=30),
            cliente_id=test_cliente.id,
            validita_giorni=30,
            stato=StatoPreventivo.BOZZA,
            imponibile=Decimal("5000.00"),
            iva=Decimal("1100.00"),
            totale=Decimal("6100.00"),
        )
        db_session.add(preventivo)
        db_session.flush()

        # Add 10 righe
        for i in range(1, 11):
            riga = RigaPreventivo(
                preventivo_id=preventivo.id,
                numero_riga=i,
                descrizione=f"Line item {i}",
                quantita=Decimal("5.00"),
                prezzo_unitario=Decimal("100.00"),
                unita_misura="ore",
                aliquota_iva=Decimal("22.00"),
                imponibile=Decimal("500.00"),
                iva=Decimal("110.00"),
                totale=Decimal("610.00"),
            )
            db_session.add(riga)

        db_session.commit()
        db_session.refresh(preventivo)

        generator = PreventivoPDFGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "preventivo_many_righe.pdf"

            pdf_path = generator.generate(preventivo, str(output_path))

            assert pdf_path.exists()
            # PDF with more lines should be larger
            assert pdf_path.stat().st_size > 1000


class TestPreventivoPDFDataConversion:
    """Tests for data conversion."""

    def test_preventivo_to_dict(self, test_preventivo: Preventivo):
        """Test _preventivo_to_dict method."""
        generator = PreventivoPDFGenerator()

        preventivo_data = generator._preventivo_to_dict(test_preventivo)

        # Verify basic fields
        assert preventivo_data["id"] == test_preventivo.id
        assert preventivo_data["numero"] == test_preventivo.numero
        assert preventivo_data["anno"] == test_preventivo.anno
        assert preventivo_data["data_emissione"] == test_preventivo.data_emissione
        assert preventivo_data["data_scadenza"] == test_preventivo.data_scadenza
        assert preventivo_data["validita_giorni"] == test_preventivo.validita_giorni

        # Verify amounts
        assert preventivo_data["imponibile"] == test_preventivo.imponibile
        assert preventivo_data["iva"] == test_preventivo.iva
        assert preventivo_data["totale"] == test_preventivo.totale

        # Verify stato
        assert preventivo_data["stato"] == test_preventivo.stato.value

        # Verify cliente data
        assert preventivo_data["cliente"]["denominazione"] == test_preventivo.cliente.denominazione
        assert preventivo_data["cliente"]["partita_iva"] == test_preventivo.cliente.partita_iva

        # Verify righe
        assert len(preventivo_data["righe"]) == len(test_preventivo.righe)

    def test_preventivo_to_dict_with_partial_cliente_data(
        self, db_session: Session, test_preventivo: Preventivo
    ):
        """Test _preventivo_to_dict with partial cliente data."""
        # Remove some optional cliente fields
        test_preventivo.cliente.numero_civico = None
        test_preventivo.cliente.telefono = None
        db_session.commit()

        generator = PreventivoPDFGenerator()

        preventivo_data = generator._preventivo_to_dict(test_preventivo)

        assert preventivo_data["cliente"]["numero_civico"] is None
        assert preventivo_data["cliente"]["denominazione"] is not None


class TestPreventivoPDFRendering:
    """Tests for PDF rendering components."""

    def test_generate_pdf_with_notes(self, test_preventivo: Preventivo):
        """Test PDF generation with notes."""
        test_preventivo.note = "Important notes about this preventivo"

        generator = PreventivoPDFGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "preventivo_notes.pdf"

            pdf_path = generator.generate(test_preventivo, str(output_path))

            assert pdf_path.exists()

    def test_generate_pdf_with_conditions(self, test_preventivo: Preventivo):
        """Test PDF generation with conditions."""
        test_preventivo.condizioni = "Terms and conditions: payment within 30 days"

        generator = PreventivoPDFGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "preventivo_conditions.pdf"

            pdf_path = generator.generate(test_preventivo, str(output_path))

            assert pdf_path.exists()

    def test_generate_pdf_with_long_notes(self, test_preventivo: Preventivo):
        """Test PDF generation with very long notes (text wrapping)."""
        test_preventivo.note = "This is a very long note. " * 100  # Very long text

        generator = PreventivoPDFGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "preventivo_long_notes.pdf"

            pdf_path = generator.generate(test_preventivo, str(output_path))

            assert pdf_path.exists()
            # Should handle long text without errors

    def test_generate_pdf_with_long_conditions(self, test_preventivo: Preventivo):
        """Test PDF generation with very long conditions."""
        test_preventivo.condizioni = "Condition clause. " * 150

        generator = PreventivoPDFGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "preventivo_long_conditions.pdf"

            pdf_path = generator.generate(test_preventivo, str(output_path))

            assert pdf_path.exists()


class TestPreventivoPDFProperties:
    """Tests for PDF file properties."""

    def test_pdf_file_size_reasonable(self, test_preventivo: Preventivo):
        """Test PDF file size is reasonable."""
        generator = PreventivoPDFGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_size.pdf"

            pdf_path = generator.generate(test_preventivo, str(output_path))

            file_size = pdf_path.stat().st_size

            # PDF should be between 1KB and 10MB
            assert 1000 < file_size < 10_000_000

    def test_generate_pdf_for_different_stati(self, db_session: Session, test_cliente: Cliente):
        """Test PDF generation for preventivi with different stati."""
        stati = [
            StatoPreventivo.BOZZA,
            StatoPreventivo.INVIATO,
            StatoPreventivo.ACCETTATO,
            StatoPreventivo.RIFIUTATO,
            StatoPreventivo.SCADUTO,
        ]

        generator = PreventivoPDFGenerator()

        for stato in stati:
            preventivo = Preventivo(
                numero=f"{stati.index(stato) + 10}",
                anno=2025,
                data_emissione=date.today(),
                data_scadenza=date.today() + timedelta(days=30),
                cliente_id=test_cliente.id,
                validita_giorni=30,
                stato=stato,
                imponibile=Decimal("1000.00"),
                iva=Decimal("220.00"),
                totale=Decimal("1220.00"),
            )
            db_session.add(preventivo)
            db_session.flush()

            # Add at least one riga
            riga = RigaPreventivo(
                preventivo_id=preventivo.id,
                numero_riga=1,
                descrizione="Test",
                quantita=Decimal("1.00"),
                prezzo_unitario=Decimal("1000.00"),
                unita_misura="ore",
                aliquota_iva=Decimal("22.00"),
                imponibile=Decimal("1000.00"),
                iva=Decimal("220.00"),
                totale=Decimal("1220.00"),
            )
            db_session.add(riga)
            db_session.commit()
            db_session.refresh(preventivo)

            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / f"preventivo_{stato.value}.pdf"

                pdf_path = generator.generate(preventivo, str(output_path))

                assert pdf_path.exists()
                assert pdf_path.stat().st_size > 0
