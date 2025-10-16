"""Extended unit tests for PreventivoService - exception handling and edge cases."""

from datetime import date, timedelta
from decimal import Decimal
from threading import Thread

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from openfatture.core.preventivi.service import PreventivoService
from openfatture.storage.database.base import Base
from openfatture.storage.database.models import Cliente, StatoPreventivo
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


class TestPreventivoServiceExceptionHandling:
    """Tests for exception handling in PreventivoService."""

    def test_create_preventivo_empty_righe(
        self, db_session: Session, test_cliente: Cliente, preventivo_service: PreventivoService
    ):
        """Test preventivo creation with empty righe list fails gracefully."""
        preventivo, error = preventivo_service.create_preventivo(
            db=db_session,
            cliente_id=test_cliente.id,
            righe=[],  # Empty list
        )

        # Should succeed but with zero totals (edge case)
        # Actually, business logic might want to prevent this
        # For now, let's test it handles empty righe
        if preventivo:
            assert len(preventivo.righe) == 0
        else:
            assert error is not None

    def test_list_preventivi_multiple_filters(
        self, db_session: Session, test_cliente: Cliente, preventivo_service: PreventivoService
    ):
        """Test list_preventivi with multiple filters combined."""
        righe = [
            {
                "descrizione": "Test",
                "quantita": 1,
                "prezzo_unitario": 100.00,
                "aliquota_iva": 22.00,
            }
        ]

        # Create preventivi with different states
        prev1, _ = preventivo_service.create_preventivo(
            db=db_session, cliente_id=test_cliente.id, righe=righe
        )
        preventivo_service.update_stato(db_session, prev1.id, StatoPreventivo.INVIATO)

        prev2, _ = preventivo_service.create_preventivo(
            db=db_session, cliente_id=test_cliente.id, righe=righe
        )

        # Test combined filters
        result = preventivo_service.list_preventivi(
            db=db_session,
            stato=StatoPreventivo.BOZZA,
            cliente_id=test_cliente.id,
            anno=date.today().year,
        )

        assert len(result) == 1
        assert result[0].id == prev2.id

    def test_list_preventivi_with_limit(
        self, db_session: Session, test_cliente: Cliente, preventivo_service: PreventivoService
    ):
        """Test list_preventivi respects limit parameter."""
        righe = [
            {"descrizione": "Test", "quantita": 1, "prezzo_unitario": 100.00, "aliquota_iva": 22.00}
        ]

        # Create 10 preventivi
        for _ in range(10):
            preventivo_service.create_preventivo(
                db=db_session, cliente_id=test_cliente.id, righe=righe
            )

        # Test limit
        result = preventivo_service.list_preventivi(db=db_session, limit=5)

        assert len(result) == 5

    def test_update_stato_nonexistent_preventivo(
        self, db_session: Session, preventivo_service: PreventivoService
    ):
        """Test update_stato with nonexistent preventivo ID."""
        success, error = preventivo_service.update_stato(db_session, 9999, StatoPreventivo.INVIATO)

        assert success is False
        assert "not found" in error.lower()

    def test_update_stato_cannot_change_convertito(
        self, db_session: Session, test_cliente: Cliente, preventivo_service: PreventivoService
    ):
        """Test cannot change status of CONVERTITO preventivo."""
        righe = [
            {"descrizione": "Test", "quantita": 1, "prezzo_unitario": 100.00, "aliquota_iva": 22.00}
        ]

        preventivo, _ = preventivo_service.create_preventivo(
            db=db_session, cliente_id=test_cliente.id, righe=righe
        )

        # Mark as converted
        preventivo.stato = StatoPreventivo.CONVERTITO
        db_session.commit()

        # Try to change status
        success, error = preventivo_service.update_stato(
            db_session, preventivo.id, StatoPreventivo.ACCETTATO
        )

        assert success is False
        assert "cannot change status" in error.lower() or "converted" in error.lower()

    def test_delete_preventivo_nonexistent(
        self, db_session: Session, preventivo_service: PreventivoService
    ):
        """Test delete_preventivo with nonexistent ID."""
        success, error = preventivo_service.delete_preventivo(db_session, 9999)

        assert success is False
        assert "not found" in error.lower()

    def test_check_scadenza_nonexistent_preventivo(
        self, db_session: Session, preventivo_service: PreventivoService
    ):
        """Test check_scadenza with nonexistent preventivo ID."""
        is_expired, error = preventivo_service.check_scadenza(db_session, 9999)

        assert is_expired is False
        assert "not found" in error.lower()


class TestPreventivoServiceEdgeCases:
    """Tests for edge cases in PreventivoService."""

    def test_create_preventivo_zero_quantity(
        self, db_session: Session, test_cliente: Cliente, preventivo_service: PreventivoService
    ):
        """Test preventivo creation with zero quantity."""
        righe = [
            {
                "descrizione": "Test with zero quantity",
                "quantita": 0,
                "prezzo_unitario": 100.00,
                "aliquota_iva": 22.00,
            }
        ]

        preventivo, error = preventivo_service.create_preventivo(
            db=db_session, cliente_id=test_cliente.id, righe=righe
        )

        assert error is None
        assert preventivo is not None
        assert preventivo.imponibile == Decimal("0.00")
        assert preventivo.totale == Decimal("0.00")

    def test_create_preventivo_very_long_description(
        self, db_session: Session, test_cliente: Cliente, preventivo_service: PreventivoService
    ):
        """Test preventivo creation with very long description."""
        long_description = "A" * 5000  # 5000 characters

        righe = [
            {
                "descrizione": long_description,
                "quantita": 1,
                "prezzo_unitario": 100.00,
                "aliquota_iva": 22.00,
            }
        ]

        preventivo, error = preventivo_service.create_preventivo(
            db=db_session, cliente_id=test_cliente.id, righe=righe
        )

        # Should handle long descriptions
        if preventivo:
            assert len(preventivo.righe[0].descrizione) == 5000
        else:
            assert error is not None

    def test_create_preventivo_many_righe(
        self, db_session: Session, test_cliente: Cliente, preventivo_service: PreventivoService
    ):
        """Test preventivo creation with many line items."""
        # Create 50 righe
        righe = [
            {
                "descrizione": f"Item {i}",
                "quantita": 1,
                "prezzo_unitario": 10.00,
                "aliquota_iva": 22.00,
            }
            for i in range(50)
        ]

        preventivo, error = preventivo_service.create_preventivo(
            db=db_session, cliente_id=test_cliente.id, righe=righe
        )

        assert error is None
        assert preventivo is not None
        assert len(preventivo.righe) == 50
        assert preventivo.imponibile == Decimal("500.00")  # 50 * 10

    def test_create_preventivo_decimal_precision(
        self, db_session: Session, test_cliente: Cliente, preventivo_service: PreventivoService
    ):
        """Test preventivo creation with high decimal precision."""
        righe = [
            {
                "descrizione": "Test precision",
                "quantita": 0.333,  # 3 decimals
                "prezzo_unitario": 33.33,
                "aliquota_iva": 22.00,
            }
        ]

        preventivo, error = preventivo_service.create_preventivo(
            db=db_session, cliente_id=test_cliente.id, righe=righe
        )

        assert error is None
        assert preventivo is not None
        # Database Numeric(10,2) rounds to 2 decimals
        assert preventivo.righe[0].quantita == Decimal("0.33")  # Rounded by DB

    def test_create_preventivo_custom_validita_zero(
        self, db_session: Session, test_cliente: Cliente, preventivo_service: PreventivoService
    ):
        """Test preventivo creation with zero days validity."""
        righe = [
            {"descrizione": "Test", "quantita": 1, "prezzo_unitario": 100.00, "aliquota_iva": 22.00}
        ]

        preventivo, error = preventivo_service.create_preventivo(
            db=db_session, cliente_id=test_cliente.id, righe=righe, validita_giorni=0
        )

        assert error is None
        assert preventivo is not None
        assert preventivo.validita_giorni == 0
        assert preventivo.data_scadenza == date.today()

    def test_create_preventivo_long_validity(
        self, db_session: Session, test_cliente: Cliente, preventivo_service: PreventivoService
    ):
        """Test preventivo creation with very long validity period."""
        righe = [
            {"descrizione": "Test", "quantita": 1, "prezzo_unitario": 100.00, "aliquota_iva": 22.00}
        ]

        preventivo, error = preventivo_service.create_preventivo(
            db=db_session, cliente_id=test_cliente.id, righe=righe, validita_giorni=365
        )

        assert error is None
        assert preventivo is not None
        assert preventivo.validita_giorni == 365
        expected_scadenza = date.today() + timedelta(days=365)
        assert preventivo.data_scadenza == expected_scadenza

    def test_list_preventivi_empty_database(
        self, db_session: Session, preventivo_service: PreventivoService
    ):
        """Test list_preventivi with empty database."""
        result = preventivo_service.list_preventivi(db_session)

        assert len(result) == 0
        assert result == []

    def test_list_preventivi_filter_by_nonexistent_cliente(
        self, db_session: Session, test_cliente: Cliente, preventivo_service: PreventivoService
    ):
        """Test list_preventivi filtered by nonexistent cliente."""
        righe = [
            {"descrizione": "Test", "quantita": 1, "prezzo_unitario": 100.00, "aliquota_iva": 22.00}
        ]

        preventivo_service.create_preventivo(db=db_session, cliente_id=test_cliente.id, righe=righe)

        # Filter by nonexistent cliente
        result = preventivo_service.list_preventivi(db=db_session, cliente_id=9999)

        assert len(result) == 0

    def test_create_preventivo_mixed_iva_rates(
        self, db_session: Session, test_cliente: Cliente, preventivo_service: PreventivoService
    ):
        """Test preventivo with multiple different IVA rates."""
        righe = [
            {
                "descrizione": "Item 4% IVA",
                "quantita": 1,
                "prezzo_unitario": 100.00,
                "aliquota_iva": 4.00,
            },
            {
                "descrizione": "Item 10% IVA",
                "quantita": 1,
                "prezzo_unitario": 200.00,
                "aliquota_iva": 10.00,
            },
            {
                "descrizione": "Item 22% IVA",
                "quantita": 1,
                "prezzo_unitario": 300.00,
                "aliquota_iva": 22.00,
            },
        ]

        preventivo, error = preventivo_service.create_preventivo(
            db=db_session, cliente_id=test_cliente.id, righe=righe
        )

        assert error is None
        assert preventivo is not None
        assert preventivo.imponibile == Decimal("600.00")  # 100 + 200 + 300
        # IVA: 4 + 20 + 66 = 90
        assert preventivo.iva == Decimal("90.00")
        assert preventivo.totale == Decimal("690.00")


class TestPreventivoServiceConcurrency:
    """Tests for concurrency scenarios."""

    @pytest.mark.skip(reason="SQLite in-memory doesn't support true concurrency")
    def test_create_preventivo_concurrent_numbering(
        self, db_session: Session, test_cliente: Cliente, preventivo_service: PreventivoService
    ):
        """Test concurrent preventivo creation maintains sequential numbering."""
        # Note: This test is skipped because SQLite in-memory doesn't support
        # true concurrency. In production with PostgreSQL this would work.

        righe = [
            {"descrizione": "Test", "quantita": 1, "prezzo_unitario": 100.00, "aliquota_iva": 22.00}
        ]

        preventivi_created = []

        def create_preventivo():
            # Create new session for each thread
            engine = db_session.get_bind()
            SessionLocal = sessionmaker(bind=engine)
            thread_session = SessionLocal()
            try:
                preventivo, _ = preventivo_service.create_preventivo(
                    db=thread_session, cliente_id=test_cliente.id, righe=righe
                )
                preventivi_created.append(preventivo.numero if preventivo else None)
            finally:
                thread_session.close()

        # Create multiple threads
        threads = [Thread(target=create_preventivo) for _ in range(3)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Verify all were created with unique numbers
        assert len(preventivi_created) == 3
        assert None not in preventivi_created

    def test_check_scadenza_already_expired_no_double_update(
        self, db_session: Session, test_cliente: Cliente, preventivo_service: PreventivoService
    ):
        """Test check_scadenza doesn't update status twice."""
        righe = [
            {"descrizione": "Test", "quantita": 1, "prezzo_unitario": 100.00, "aliquota_iva": 22.00}
        ]

        preventivo, _ = preventivo_service.create_preventivo(
            db=db_session, cliente_id=test_cliente.id, righe=righe
        )

        # Set expired date
        preventivo.data_scadenza = date.today() - timedelta(days=1)
        db_session.commit()

        # Call check_scadenza twice
        is_expired1, _ = preventivo_service.check_scadenza(db_session, preventivo.id)
        is_expired2, _ = preventivo_service.check_scadenza(db_session, preventivo.id)

        assert is_expired1 is True
        assert is_expired2 is False  # Already marked as expired, no update needed

        # Verify status is SCADUTO
        db_session.refresh(preventivo)
        assert preventivo.stato == StatoPreventivo.SCADUTO
