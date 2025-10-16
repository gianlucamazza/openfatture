"""Unit tests for PreventivoService."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from openfatture.core.preventivi.service import PreventivoService
from openfatture.storage.database.base import Base
from openfatture.storage.database.models import (
    Cliente,
    StatoPreventivo,
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


class TestPreventivoServiceCreate:
    """Tests for create_preventivo method."""

    def test_create_preventivo_success(
        self, db_session: Session, test_cliente: Cliente, preventivo_service: PreventivoService
    ):
        """Test successful preventivo creation."""
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

        preventivo, error = preventivo_service.create_preventivo(
            db=db_session,
            cliente_id=test_cliente.id,
            righe=righe,
            validita_giorni=30,
            note="Test note",
            condizioni="Test conditions",
        )

        assert error is None
        assert preventivo is not None
        assert preventivo.numero == "1"
        assert preventivo.anno == date.today().year
        assert preventivo.cliente_id == test_cliente.id
        assert preventivo.validita_giorni == 30
        assert preventivo.stato == StatoPreventivo.BOZZA
        assert len(preventivo.righe) == 2
        assert preventivo.imponibile == Decimal("4000.00")
        assert preventivo.iva == Decimal("880.00")
        assert preventivo.totale == Decimal("4880.00")
        assert preventivo.note == "Test note"
        assert preventivo.condizioni == "Test conditions"

    def test_create_preventivo_invalid_cliente(
        self, db_session: Session, preventivo_service: PreventivoService
    ):
        """Test preventivo creation with invalid client."""
        righe = [
            {
                "descrizione": "Test",
                "quantita": 1,
                "prezzo_unitario": 100.00,
                "aliquota_iva": 22.00,
            }
        ]

        preventivo, error = preventivo_service.create_preventivo(
            db=db_session,
            cliente_id=9999,  # Non-existent client
            righe=righe,
        )

        assert preventivo is None
        assert "not found" in error.lower()

    def test_create_preventivo_sequential_numbers(
        self, db_session: Session, test_cliente: Cliente, preventivo_service: PreventivoService
    ):
        """Test sequential numero generation."""
        righe = [
            {
                "descrizione": "Test",
                "quantita": 1,
                "prezzo_unitario": 100.00,
                "aliquota_iva": 22.00,
            }
        ]

        prev1, _ = preventivo_service.create_preventivo(
            db=db_session, cliente_id=test_cliente.id, righe=righe
        )
        prev2, _ = preventivo_service.create_preventivo(
            db=db_session, cliente_id=test_cliente.id, righe=righe
        )
        prev3, _ = preventivo_service.create_preventivo(
            db=db_session, cliente_id=test_cliente.id, righe=righe
        )

        assert prev1.numero == "1"
        assert prev2.numero == "2"
        assert prev3.numero == "3"


class TestPreventivoServiceCRUD:
    """Tests for CRUD operations."""

    def test_get_preventivo(
        self, db_session: Session, test_cliente: Cliente, preventivo_service: PreventivoService
    ):
        """Test get_preventivo method."""
        righe = [
            {
                "descrizione": "Test",
                "quantita": 1,
                "prezzo_unitario": 100.00,
                "aliquota_iva": 22.00,
            }
        ]

        preventivo, _ = preventivo_service.create_preventivo(
            db=db_session, cliente_id=test_cliente.id, righe=righe
        )

        retrieved = preventivo_service.get_preventivo(db_session, preventivo.id)

        assert retrieved is not None
        assert retrieved.id == preventivo.id
        assert retrieved.numero == preventivo.numero

    def test_list_preventivi(
        self, db_session: Session, test_cliente: Cliente, preventivo_service: PreventivoService
    ):
        """Test list_preventivi with filters."""
        righe = [
            {
                "descrizione": "Test",
                "quantita": 1,
                "prezzo_unitario": 100.00,
                "aliquota_iva": 22.00,
            }
        ]

        # Create multiple preventivi
        for _ in range(3):
            preventivo_service.create_preventivo(
                db=db_session, cliente_id=test_cliente.id, righe=righe
            )

        # List all
        all_preventivi = preventivo_service.list_preventivi(db_session)
        assert len(all_preventivi) == 3

        # Filter by status
        bozza_preventivi = preventivo_service.list_preventivi(
            db_session, stato=StatoPreventivo.BOZZA
        )
        assert len(bozza_preventivi) == 3

    def test_update_stato(
        self, db_session: Session, test_cliente: Cliente, preventivo_service: PreventivoService
    ):
        """Test update_stato method."""
        righe = [
            {
                "descrizione": "Test",
                "quantita": 1,
                "prezzo_unitario": 100.00,
                "aliquota_iva": 22.00,
            }
        ]

        preventivo, _ = preventivo_service.create_preventivo(
            db=db_session, cliente_id=test_cliente.id, righe=righe
        )

        # Update to INVIATO
        success, error = preventivo_service.update_stato(
            db_session, preventivo.id, StatoPreventivo.INVIATO
        )

        assert success is True
        assert error is None

        retrieved = preventivo_service.get_preventivo(db_session, preventivo.id)
        assert retrieved.stato == StatoPreventivo.INVIATO

    def test_delete_preventivo(
        self, db_session: Session, test_cliente: Cliente, preventivo_service: PreventivoService
    ):
        """Test delete_preventivo method."""
        righe = [
            {
                "descrizione": "Test",
                "quantita": 1,
                "prezzo_unitario": 100.00,
                "aliquota_iva": 22.00,
            }
        ]

        preventivo, _ = preventivo_service.create_preventivo(
            db=db_session, cliente_id=test_cliente.id, righe=righe
        )

        # Delete
        success, error = preventivo_service.delete_preventivo(db_session, preventivo.id)

        assert success is True
        assert error is None

        # Verify deletion
        retrieved = preventivo_service.get_preventivo(db_session, preventivo.id)
        assert retrieved is None

    def test_delete_preventivo_converted(
        self, db_session: Session, test_cliente: Cliente, preventivo_service: PreventivoService
    ):
        """Test delete_preventivo fails for converted preventivo."""
        righe = [
            {
                "descrizione": "Test",
                "quantita": 1,
                "prezzo_unitario": 100.00,
                "aliquota_iva": 22.00,
            }
        ]

        preventivo, _ = preventivo_service.create_preventivo(
            db=db_session, cliente_id=test_cliente.id, righe=righe
        )

        # Mark as converted
        preventivo.stato = StatoPreventivo.CONVERTITO
        db_session.commit()

        # Try to delete
        success, error = preventivo_service.delete_preventivo(db_session, preventivo.id)

        assert success is False
        assert "cannot delete" in error.lower()


class TestPreventivoServiceExpiration:
    """Tests for expiration logic."""

    def test_check_scadenza_not_expired(
        self, db_session: Session, test_cliente: Cliente, preventivo_service: PreventivoService
    ):
        """Test check_scadenza for non-expired preventivo."""
        righe = [
            {
                "descrizione": "Test",
                "quantita": 1,
                "prezzo_unitario": 100.00,
                "aliquota_iva": 22.00,
            }
        ]

        preventivo, _ = preventivo_service.create_preventivo(
            db=db_session, cliente_id=test_cliente.id, righe=righe, validita_giorni=30
        )

        is_expired, error = preventivo_service.check_scadenza(db_session, preventivo.id)

        assert is_expired is False
        assert error is None

    def test_check_scadenza_expired(
        self, db_session: Session, test_cliente: Cliente, preventivo_service: PreventivoService
    ):
        """Test check_scadenza for expired preventivo."""
        righe = [
            {
                "descrizione": "Test",
                "quantita": 1,
                "prezzo_unitario": 100.00,
                "aliquota_iva": 22.00,
            }
        ]

        preventivo, _ = preventivo_service.create_preventivo(
            db=db_session, cliente_id=test_cliente.id, righe=righe, validita_giorni=1
        )

        # Manually set expiration date to past
        preventivo.data_scadenza = date.today() - timedelta(days=1)
        db_session.commit()

        is_expired, error = preventivo_service.check_scadenza(db_session, preventivo.id)

        assert is_expired is True
        assert error is None

        # Verify status updated
        retrieved = preventivo_service.get_preventivo(db_session, preventivo.id)
        assert retrieved.stato == StatoPreventivo.SCADUTO
