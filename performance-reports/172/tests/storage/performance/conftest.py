"""Shared fixtures for database performance tests."""

import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from openfatture.storage.database.base import Base
from openfatture.storage.database.models import Cliente, Fattura, Pagamento
from tests.performance.fixtures import generate_clients, generate_invoices, generate_payments


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
    """Database with 10 clients."""
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
    """Database with 100 clients."""
    clienti = generate_clients(count=100, seed=42)

    # Bulk insert for better performance
    perf_db_session.bulk_save_objects(clienti)
    perf_db_session.commit()

    # Query back to get IDs
    clienti = perf_db_session.query(Cliente).all()

    yield perf_db_session, clienti


@pytest.fixture
def perf_db_with_invoices_small(perf_db_with_clients_small):
    """Database with 10 clients and 50 invoices."""
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
    """Database with 100 clients and 500 invoices."""
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
    """Database with 100 clients and 1000 invoices.

    Warning: This fixture is slow (~10-20s) due to relationship setup.
    Use only for scalability tests.
    """
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


@pytest.fixture
def perf_db_with_full_dataset(perf_db_with_invoices_medium):
    """Database with clients, invoices, and payments (full dataset).

    Dataset: 100 clients, 500 invoices, ~350 payments (70% payment rate).
    """
    session, clienti, fatture = perf_db_with_invoices_medium

    pagamenti = generate_payments(fatture, payment_rate=0.7, seed=42)

    # Add payments
    for pagamento in pagamenti:
        session.add(pagamento)
    session.commit()

    # Refresh
    pagamenti = session.query(Pagamento).all()

    yield session, clienti, fatture, pagamenti


@pytest.fixture
def sample_cliente_for_query():
    """Generate a sample client for query testing."""
    clienti = generate_clients(count=1, seed=999)
    return clienti[0]


@pytest.fixture
def sample_fattura_for_query(sample_cliente_for_query):
    """Generate a sample invoice for query testing."""
    clienti = [sample_cliente_for_query]
    fatture = generate_invoices(clienti, count=1, year=2025, seed=999)
    return fatture[0]
