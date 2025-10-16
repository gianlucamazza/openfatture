"""Integration tests for preventivo → fattura conversion."""

from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from openfatture.core.preventivi.service import PreventivoService
from openfatture.storage.database.base import Base
from openfatture.storage.database.models import (
    Cliente,
    Preventivo,
    StatoFattura,
    StatoPreventivo,
    TipoDocumento,
)
from openfatture.utils.config import Settings


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
        cap="00100",
        comune="Roma",
        provincia="RM",
        nazione="IT",
    )
    db_session.add(cliente)
    db_session.commit()
    db_session.refresh(cliente)
    return cliente


@pytest.fixture
def preventivo_service() -> PreventivoService:
    """Create PreventivoService instance."""
    settings = Settings(
        cedente_partita_iva="11111111111",
        cedente_codice_fiscale="11111111111",
        cedente_denominazione="Test Company",
        cedente_regime_fiscale="RF01",
        cedente_indirizzo="Via Test",
        cedente_cap="00100",
        cedente_comune="Roma",
        cedente_provincia="RM",
        cedente_nazione="IT",
    )
    return PreventivoService(settings)


@pytest.fixture
def test_preventivo(
    db_session: Session, test_cliente: Cliente, preventivo_service: PreventivoService
) -> Preventivo:
    """Create test preventivo."""
    righe = [
        {
            "descrizione": "Consulenza IT",
            "quantita": 10,
            "prezzo_unitario": 100.00,
            "aliquota_iva": 22.00,
            "unita_misura": "ore",
        },
        {
            "descrizione": "Sviluppo software",
            "quantita": 20,
            "prezzo_unitario": 150.00,
            "aliquota_iva": 22.00,
            "unita_misura": "ore",
        },
    ]

    preventivo, _ = preventivo_service.create_preventivo(
        db=db_session,
        cliente_id=test_cliente.id,
        righe=righe,
        validita_giorni=30,
        note="Test preventivo",
    )

    return preventivo


class TestPreventivoConversion:
    """Tests for preventivo to fattura conversion."""

    def test_converti_a_fattura_success(
        self,
        db_session: Session,
        test_preventivo: Preventivo,
        preventivo_service: PreventivoService,
    ):
        """Test successful conversion from preventivo to fattura."""
        fattura, error = preventivo_service.converti_a_fattura(
            db_session, test_preventivo.id, TipoDocumento.TD01
        )

        assert error is None
        assert fattura is not None

        # Verify fattura data
        assert fattura.numero == "1"
        assert fattura.anno == date.today().year
        assert fattura.cliente_id == test_preventivo.cliente_id
        assert fattura.preventivo_id == test_preventivo.id
        assert fattura.stato == StatoFattura.BOZZA
        assert fattura.tipo_documento == TipoDocumento.TD01

        # Verify amounts match
        assert fattura.imponibile == test_preventivo.imponibile
        assert fattura.iva == test_preventivo.iva
        assert fattura.totale == test_preventivo.totale

        # Verify righe copied correctly
        assert len(fattura.righe) == len(test_preventivo.righe)

        for riga_fatt, riga_prev in zip(fattura.righe, test_preventivo.righe, strict=False):
            assert riga_fatt.descrizione == riga_prev.descrizione
            assert riga_fatt.quantita == riga_prev.quantita
            assert riga_fatt.prezzo_unitario == riga_prev.prezzo_unitario
            assert riga_fatt.aliquota_iva == riga_prev.aliquota_iva
            assert riga_fatt.imponibile == riga_prev.imponibile
            assert riga_fatt.iva == riga_prev.iva
            assert riga_fatt.totale == riga_prev.totale

        # Verify preventivo status updated
        db_session.refresh(test_preventivo)
        assert test_preventivo.stato == StatoPreventivo.CONVERTITO

    def test_converti_a_fattura_already_converted(
        self,
        db_session: Session,
        test_preventivo: Preventivo,
        preventivo_service: PreventivoService,
    ):
        """Test conversion fails if preventivo already converted."""
        # Convert once
        preventivo_service.converti_a_fattura(db_session, test_preventivo.id, TipoDocumento.TD01)

        # Try to convert again
        fattura, error = preventivo_service.converti_a_fattura(
            db_session, test_preventivo.id, TipoDocumento.TD01
        )

        assert fattura is None
        assert "already converted" in error.lower()

    def test_converti_a_fattura_expired(
        self,
        db_session: Session,
        test_preventivo: Preventivo,
        preventivo_service: PreventivoService,
    ):
        """Test conversion fails if preventivo expired."""
        # Set expiration date to past
        test_preventivo.data_scadenza = date.today() - timedelta(days=1)
        db_session.commit()

        # Try to convert
        fattura, error = preventivo_service.converti_a_fattura(
            db_session, test_preventivo.id, TipoDocumento.TD01
        )

        assert fattura is None
        assert "expired" in error.lower()

    def test_converti_a_fattura_scaduto_status(
        self,
        db_session: Session,
        test_preventivo: Preventivo,
        preventivo_service: PreventivoService,
    ):
        """Test conversion fails if preventivo has SCADUTO status."""
        # Mark as expired
        test_preventivo.stato = StatoPreventivo.SCADUTO
        db_session.commit()

        # Try to convert
        fattura, error = preventivo_service.converti_a_fattura(
            db_session, test_preventivo.id, TipoDocumento.TD01
        )

        assert fattura is None
        assert "cannot convert expired" in error.lower()

    def test_converti_a_fattura_preserves_notes(
        self,
        db_session: Session,
        test_preventivo: Preventivo,
        preventivo_service: PreventivoService,
    ):
        """Test conversion preserves notes from preventivo."""
        test_note = "Important notes about this project"
        test_preventivo.note = test_note
        db_session.commit()

        fattura, error = preventivo_service.converti_a_fattura(
            db_session, test_preventivo.id, TipoDocumento.TD01
        )

        assert error is None
        assert fattura.note == test_note

    def test_converti_a_fattura_different_document_types(
        self,
        db_session: Session,
        test_cliente: Cliente,
        preventivo_service: PreventivoService,
    ):
        """Test conversion with different document types."""
        righe = [
            {
                "descrizione": "Test",
                "quantita": 1,
                "prezzo_unitario": 100.00,
                "aliquota_iva": 22.00,
            }
        ]

        # TD01 - Fattura ordinaria
        prev1, _ = preventivo_service.create_preventivo(
            db=db_session, cliente_id=test_cliente.id, righe=righe
        )
        fattura1, _ = preventivo_service.converti_a_fattura(
            db_session, prev1.id, TipoDocumento.TD01
        )
        assert fattura1.tipo_documento == TipoDocumento.TD01

        # TD06 - Parcella
        prev2, _ = preventivo_service.create_preventivo(
            db=db_session, cliente_id=test_cliente.id, righe=righe
        )
        fattura2, _ = preventivo_service.converti_a_fattura(
            db_session, prev2.id, TipoDocumento.TD06
        )
        assert fattura2.tipo_documento == TipoDocumento.TD06

    def test_converti_a_fattura_sequential_invoice_numbers(
        self,
        db_session: Session,
        test_cliente: Cliente,
        preventivo_service: PreventivoService,
    ):
        """Test conversion generates sequential invoice numbers."""
        righe = [
            {
                "descrizione": "Test",
                "quantita": 1,
                "prezzo_unitario": 100.00,
                "aliquota_iva": 22.00,
            }
        ]

        # Create and convert multiple preventivi
        prev1, _ = preventivo_service.create_preventivo(
            db=db_session, cliente_id=test_cliente.id, righe=righe
        )
        prev2, _ = preventivo_service.create_preventivo(
            db=db_session, cliente_id=test_cliente.id, righe=righe
        )
        prev3, _ = preventivo_service.create_preventivo(
            db=db_session, cliente_id=test_cliente.id, righe=righe
        )

        fattura1, _ = preventivo_service.converti_a_fattura(
            db_session, prev1.id, TipoDocumento.TD01
        )
        fattura2, _ = preventivo_service.converti_a_fattura(
            db_session, prev2.id, TipoDocumento.TD01
        )
        fattura3, _ = preventivo_service.converti_a_fattura(
            db_session, prev3.id, TipoDocumento.TD01
        )

        assert fattura1.numero == "1"
        assert fattura2.numero == "2"
        assert fattura3.numero == "3"

    def test_converti_a_fattura_bidirectional_relationship(
        self,
        db_session: Session,
        test_preventivo: Preventivo,
        preventivo_service: PreventivoService,
    ):
        """Test bidirectional relationship between preventivo and fattura."""
        fattura, error = preventivo_service.converti_a_fattura(
            db_session, test_preventivo.id, TipoDocumento.TD01
        )

        assert error is None

        # Test relationship from fattura to preventivo
        db_session.refresh(fattura)
        assert fattura.preventivo_id == test_preventivo.id
        assert fattura.preventivo is not None
        assert fattura.preventivo.id == test_preventivo.id

        # Test relationship from preventivo to fattura
        db_session.refresh(test_preventivo)
        assert test_preventivo.fattura is not None
        assert test_preventivo.fattura.id == fattura.id
