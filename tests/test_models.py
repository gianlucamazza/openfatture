"""Test suite for database models."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from openfatture.storage.database.base import Base
from openfatture.storage.database.models import (
    Cliente,
    Fattura,
    RigaFattura,
    StatoFattura,
    TipoDocumento,
)


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()


def test_create_cliente(db_session):
    """Test creating a client."""
    cliente = Cliente(
        denominazione="Test Client",
        partita_iva="12345678903",
        codice_fiscale="RSSMRA80A01H501U",
        codice_destinatario="ABC1234",
    )

    db_session.add(cliente)
    db_session.commit()

    assert cliente.id is not None
    assert cliente.denominazione == "Test Client"


def test_create_fattura(db_session):
    """Test creating an invoice."""
    # Create client first
    cliente = Cliente(
        denominazione="Test Client",
        partita_iva="12345678903",
    )
    db_session.add(cliente)
    db_session.flush()

    # Create invoice
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
    db_session.commit()

    assert fattura.id is not None
    assert fattura.numero == "1"
    assert fattura.totale == Decimal("1220.00")


def test_fattura_with_righe(db_session):
    """Test creating invoice with line items."""
    cliente = Cliente(denominazione="Test Client")
    db_session.add(cliente)
    db_session.flush()

    fattura = Fattura(
        numero="1",
        anno=2025,
        data_emissione=date.today(),
        cliente_id=cliente.id,
        tipo_documento=TipoDocumento.TD01,
        stato=StatoFattura.BOZZA,
        imponibile=Decimal("100.00"),
        iva=Decimal("22.00"),
        totale=Decimal("122.00"),
    )
    db_session.add(fattura)
    db_session.flush()

    # Add line items
    riga = RigaFattura(
        fattura_id=fattura.id,
        numero_riga=1,
        descrizione="Test service",
        quantita=Decimal("1"),
        prezzo_unitario=Decimal("100.00"),
        aliquota_iva=Decimal("22.00"),
        imponibile=Decimal("100.00"),
        iva=Decimal("22.00"),
        totale=Decimal("122.00"),
    )
    db_session.add(riga)
    db_session.commit()

    # Verify relationship
    assert len(fattura.righe) == 1
    assert fattura.righe[0].descrizione == "Test service"
