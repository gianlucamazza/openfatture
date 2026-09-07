"""Shared fixtures for end-to-end performance tests."""

import tempfile
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from openfatture.ai.rag.config import RAGConfig
from openfatture.ai.rag.embeddings import SentenceTransformerEmbeddings
from openfatture.ai.rag.indexing import InvoiceIndexer
from openfatture.ai.rag.retrieval import SemanticRetriever
from openfatture.ai.rag.vector_store import VectorStore
from openfatture.storage.database.base import Base
from tests.performance.fixtures import generate_clients, generate_invoices


def _mock_e2e_session(monkeypatch, session):
    """Mock the _get_session function for E2E tests."""
    from openfatture.ai.rag import indexing

    def _get_test_session():
        return session

    monkeypatch.setattr(indexing, "_get_session", _get_test_session)


@pytest.fixture
def e2e_temp_dirs():
    """Create temporary directories for E2E tests."""
    with tempfile.TemporaryDirectory() as db_dir, tempfile.TemporaryDirectory() as chroma_dir:
        yield {
            "db_dir": Path(db_dir),
            "chroma_dir": Path(chroma_dir),
        }


@pytest.fixture
def e2e_database(e2e_temp_dirs):
    """Create database with test data for E2E tests."""
    db_path = e2e_temp_dirs["db_dir"] / "e2e_test.db"
    engine = create_engine(f"sqlite:///{db_path}", echo=False)

    # Create tables
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # Generate test data
    clienti = generate_clients(count=50, seed=1000)
    for cliente in clienti:
        session.add(cliente)
    session.commit()

    # Refresh to get IDs
    for cliente in clienti:
        session.refresh(cliente)

    fatture = generate_invoices(clienti, count=200, year=2025, seed=1000)
    for fattura in fatture:
        session.add(fattura)
    session.commit()

    yield session, clienti, fatture

    session.close()
    engine.dispose()


@pytest.fixture
def e2e_vector_store(e2e_temp_dirs):
    """Create vector store for E2E tests with real local embeddings."""
    config = RAGConfig(
        persist_directory=e2e_temp_dirs["chroma_dir"],
        collection_name="e2e_test",
        embedding_provider="sentence-transformers",
        embedding_model="all-MiniLM-L6-v2",
        batch_size=50,
    )

    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    store = VectorStore(config, embeddings)

    # Ensure clean state
    if store.count() > 0:
        store.reset()

    yield store

    # Cleanup
    store.reset()


@pytest.fixture
def e2e_indexer(e2e_vector_store, e2e_database, monkeypatch):
    """Create invoice indexer for E2E tests with mocked database session."""
    session, clienti, fatture = e2e_database
    _mock_e2e_session(monkeypatch, session)
    return InvoiceIndexer(e2e_vector_store)


@pytest.fixture
def e2e_retriever(e2e_vector_store):
    """Create semantic retriever for E2E tests."""
    return SemanticRetriever(e2e_vector_store)


@pytest_asyncio.fixture
async def e2e_system_indexed(e2e_database, e2e_indexer):
    """E2E system with database and indexed invoices."""
    session, clienti, fatture = e2e_database

    # Index all invoices
    await e2e_indexer.index_all_invoices(batch_size=50)

    yield session, clienti, fatture, e2e_indexer

    # Cleanup handled by individual fixtures
