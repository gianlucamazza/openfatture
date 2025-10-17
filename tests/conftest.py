"""
Pytest configuration and global fixtures.

This module provides shared fixtures used across all tests.
"""

import os
import tempfile
from collections.abc import Generator
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from openfatture.storage.database.base import Base
from openfatture.storage.database.models import (
    Cliente,
    Fattura,
    RigaFattura,
    StatoFattura,
    TipoDocumento,
)
from openfatture.utils.config import Settings

# Test constants - use secure test values
TEST_PEC_PASSWORD = "test_pec_password_secure_123"


@pytest.fixture(scope="session")
def test_data_dir() -> Generator[Path, None, None]:
    """Create temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="function")
def db_engine():
    """Create an in-memory SQLite database engine for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()  # Properly close all database connections


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """
    Create a database session for testing.

    Each test gets a fresh session with automatic rollback.
    """
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()

    yield session

    session.rollback()
    session.close()


@pytest.fixture
def test_settings(test_data_dir: Path) -> Settings:
    """Create test settings with temporary directories."""
    settings = Settings(
        database_url="sqlite:///:memory:",
        data_dir=test_data_dir / "data",
        archivio_dir=test_data_dir / "archivio",
        certificates_dir=test_data_dir / "certificates",
        vector_store_path=test_data_dir / "vector_store",
        # Company data for testing
        cedente_denominazione="Test Company SRL",
        cedente_partita_iva="12345678903",
        cedente_codice_fiscale="TSTCMP80A01H501X",
        cedente_regime_fiscale="RF19",
        cedente_indirizzo="Via Test 123",
        cedente_cap="00100",
        cedente_comune="Roma",
        cedente_provincia="RM",
        cedente_nazione="IT",
        # PEC for testing
        pec_address="test@pec.example.com",
        pec_password=TEST_PEC_PASSWORD,
        pec_smtp_server="smtp.test.com",
        pec_smtp_port=465,
    )

    # Create directories
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.archivio_dir.mkdir(parents=True, exist_ok=True)
    settings.certificates_dir.mkdir(parents=True, exist_ok=True)

    return settings


@pytest.fixture
def sample_cliente(db_session: Session) -> Cliente:
    """Create a sample client for testing."""
    cliente = Cliente(
        denominazione="Acme Corporation",
        partita_iva="12345678901",
        codice_fiscale="CMPACM80A01H501Z",
        codice_destinatario="ABC1234",
        pec="acme@pec.it",
        indirizzo="Via Roma 1",
        cap="20100",
        comune="Milano",
        provincia="MI",
        nazione="IT",
        email="contact@acme.com",
        telefono="+39 02 12345678",
    )

    db_session.add(cliente)
    db_session.commit()
    db_session.refresh(cliente)

    return cliente


@pytest.fixture
def sample_fattura(db_session: Session, sample_cliente: Cliente) -> Fattura:
    """Create a sample invoice with line items."""
    fattura = Fattura(
        numero="1",
        anno=2025,
        data_emissione=date(2025, 1, 15),
        cliente_id=sample_cliente.id,
        tipo_documento=TipoDocumento.TD01,
        stato=StatoFattura.BOZZA,
        imponibile=Decimal("1000.00"),
        iva=Decimal("220.00"),
        totale=Decimal("1220.00"),
    )

    db_session.add(fattura)
    db_session.flush()

    # Add line items
    righe = [
        RigaFattura(
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
        ),
    ]

    for riga in righe:
        db_session.add(riga)

    db_session.commit()
    db_session.refresh(fattura)

    return fattura


@pytest.fixture
def sample_fattura_with_ritenuta(db_session: Session, sample_cliente: Cliente) -> Fattura:
    """Create a sample invoice with withholding tax."""
    imponibile = Decimal("1000.00")
    iva = Decimal("220.00")
    ritenuta = imponibile * Decimal("0.20")  # 20% ritenuta

    fattura = Fattura(
        numero="2",
        anno=2025,
        data_emissione=date(2025, 2, 1),
        cliente_id=sample_cliente.id,
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
    db_session.refresh(fattura)

    return fattura


@pytest.fixture
def sample_fattura_with_bollo(db_session: Session, sample_cliente: Cliente) -> Fattura:
    """Create a sample invoice with stamp duty (bollo)."""
    # Invoice with no VAT (exempt) and amount >77.47 requires bollo
    imponibile = Decimal("100.00")

    fattura = Fattura(
        numero="3",
        anno=2025,
        data_emissione=date(2025, 3, 1),
        cliente_id=sample_cliente.id,
        tipo_documento=TipoDocumento.TD01,
        stato=StatoFattura.BOZZA,
        imponibile=imponibile,
        iva=Decimal("0.00"),  # No VAT
        importo_bollo=Decimal("2.00"),
        totale=imponibile,
    )

    db_session.add(fattura)
    db_session.flush()

    riga = RigaFattura(
        fattura_id=fattura.id,
        numero_riga=1,
        descrizione="Servizio esente IVA",
        quantita=Decimal("1"),
        prezzo_unitario=imponibile,
        unita_misura="servizio",
        aliquota_iva=Decimal("0.00"),
        imponibile=imponibile,
        iva=Decimal("0.00"),
        totale=imponibile,
    )

    db_session.add(riga)
    db_session.commit()
    db_session.refresh(fattura)

    return fattura


@pytest.fixture
def multiple_clienti(db_session: Session) -> list[Cliente]:
    """Create multiple clients for testing."""
    clienti = [
        Cliente(
            denominazione=f"Client {i}",
            partita_iva=f"1234567890{i}",
            codice_destinatario=f"CODE00{i}",
        )
        for i in range(5)
    ]

    for cliente in clienti:
        db_session.add(cliente)

    db_session.commit()

    for cliente in clienti:
        db_session.refresh(cliente)

    return clienti


@pytest.fixture
def mock_pec_server(monkeypatch):
    """Mock PEC SMTP server for testing."""
    sent_emails = []

    class MockSMTP:
        def __init__(self, server, port, context=None):
            self.server = server
            self.port = port

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def login(self, username, password):
            if password == "wrong_password":
                raise Exception("Authentication failed")
            return True

        def send_message(self, msg):
            sent_emails.append(msg)
            return True

    import smtplib

    monkeypatch.setattr(smtplib, "SMTP_SSL", MockSMTP)

    return sent_emails


@pytest.fixture(autouse=True)
def reset_env():
    """Reset environment variables after each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


# Markers for test categorization
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "ai: marks tests that require AI/LLM integration")
    config.addinivalue_line("markers", "sdi: marks tests that interact with SDI")
    config.addinivalue_line("markers", "openai: marks tests that require OpenAI API key")
    config.addinivalue_line("markers", "anthropic: marks tests that require Anthropic API key")
    config.addinivalue_line("markers", "ollama: marks tests that require Ollama service")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end with real providers")


# AI Provider Fixtures
@pytest.fixture(scope="session")
def openai_api_available():
    """Check if OpenAI API key is configured."""
    from openfatture.ai.config import get_ai_settings

    settings = get_ai_settings()
    return bool(settings.openai_api_key and settings.openai_api_key.get_secret_value())


@pytest.fixture(scope="session")
def anthropic_api_available():
    """Check if Anthropic API key is configured."""
    from openfatture.ai.config import get_ai_settings

    settings = get_ai_settings()
    return bool(settings.anthropic_api_key and settings.anthropic_api_key.get_secret_value())


@pytest.fixture(scope="session")
def ollama_available():
    """Check if Ollama service is available."""
    try:
        import httpx

        response = httpx.get("http://localhost:11434/api/tags", timeout=5.0)
        return response.status_code == 200
    except Exception:
        return False


# ============================================================================
# Performance Testing Fixtures
# ============================================================================


@pytest.fixture
def perf_db_engine():
    """Create temporary SQLite database for performance testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "perf_test.db"
        engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,  # Disable SQL logging for performance
            pool_pre_ping=True,
        )

        # Create tables
        Base.metadata.create_all(engine)

        yield engine

        # Cleanup
        engine.dispose()


@pytest.fixture
def perf_db_session(perf_db_engine):
    """Create database session for performance testing."""
    SessionLocal = sessionmaker(bind=perf_db_engine)
    session = SessionLocal()

    yield session

    session.close()


@pytest.fixture
def perf_db_with_clients_small(perf_db_session):
    """Database with 10 clients for performance testing."""
    from tests.performance.fixtures import generate_clients

    clienti = generate_clients(count=10, seed=42)

    # Add to database
    for cliente in clienti:
        perf_db_session.add(cliente)
    perf_db_session.commit()

    # Refresh to get IDs
    for cliente in clienti:
        perf_db_session.refresh(cliente)

    yield perf_db_session, clienti


@pytest.fixture
def perf_db_with_clients_medium(perf_db_session):
    """Database with 100 clients for performance testing."""
    from tests.performance.fixtures import generate_clients

    clienti = generate_clients(count=100, seed=42)

    # Bulk insert for better performance
    perf_db_session.bulk_save_objects(clienti)
    perf_db_session.commit()

    # Query back to get IDs
    clienti = perf_db_session.query(Cliente).all()

    yield perf_db_session, clienti


@pytest.fixture
def perf_db_with_invoices_small(perf_db_with_clients_small):
    """Database with 10 clients and 50 invoices for performance testing."""
    from tests.performance.fixtures import generate_invoices

    session, clienti = perf_db_with_clients_small

    fatture = generate_invoices(clienti, count=50, year=2025, seed=42)

    # Add invoices
    for fattura in fatture:
        session.add(fattura)
    session.commit()

    # Refresh to get IDs
    for fattura in fatture:
        session.refresh(fattura)

    yield session, clienti, fatture


@pytest.fixture
def perf_db_with_invoices_medium(perf_db_with_clients_medium):
    """Database with 100 clients and 500 invoices for performance testing."""
    from tests.performance.fixtures import generate_invoices

    session, clienti = perf_db_with_clients_medium

    fatture = generate_invoices(clienti, count=500, year=2025, seed=42)

    # Bulk insert
    for fattura in fatture:
        session.add(fattura)
    session.commit()

    # Query back to get full objects
    fatture = session.query(Fattura).all()

    yield session, clienti, fatture


@pytest.fixture
def perf_db_with_invoices_large(perf_db_with_clients_medium):
    """Database with 100 clients and 1000 invoices for performance testing.

    Warning: This fixture is slow (~10-20s) due to relationship setup.
    Use only for scalability tests.
    """
    from tests.performance.fixtures import generate_invoices

    session, clienti = perf_db_with_clients_medium

    fatture = generate_invoices(clienti, count=1000, year=2025, seed=42)

    # Bulk insert in batches
    batch_size = 100
    for i in range(0, len(fatture), batch_size):
        batch = fatture[i : i + batch_size]
        for fattura in batch:
            session.add(fattura)
        session.commit()

    # Query back
    fatture = session.query(Fattura).all()

    yield session, clienti, fatture
