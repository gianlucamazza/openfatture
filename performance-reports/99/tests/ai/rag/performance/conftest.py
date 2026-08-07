"""Shared fixtures for RAG performance tests."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from openfatture.ai.rag.config import RAGConfig
from openfatture.ai.rag.embeddings import EmbeddingStrategy, SentenceTransformerEmbeddings
from openfatture.ai.rag.vector_store import VectorStore
from tests.performance.fixtures import generate_rag_documents


@pytest.fixture
def perf_rag_config():
    """RAG config for performance testing with temporary storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = RAGConfig(
            persist_directory=Path(tmpdir) / "chroma_perf",
            collection_name="perf_test",
            embedding_provider="sentence-transformers",
            embedding_model="all-MiniLM-L6-v2",
            top_k=10,
            similarity_threshold=0.7,
            batch_size=100,
            enable_caching=True,
        )
        yield config


@pytest.fixture
def mock_fast_embeddings():
    """Mock embedding strategy with fast generation.

    Uses deterministic embeddings for performance testing
    without actual model inference overhead.
    """
    strategy = MagicMock(spec=EmbeddingStrategy)
    strategy.dimension = 384
    strategy.model_name = "fast-mock-embedder"

    async def mock_embed_text(text: str) -> list[float]:
        """Generate deterministic embedding based on text hash."""
        # Use text hash for deterministic but varied embeddings
        text_hash = hash(text)
        base_val = (text_hash % 1000) / 1000.0
        return [base_val + (i * 0.001) for i in range(384)]

    async def mock_embed_batch(texts: list[str]) -> list[list[float]]:
        """Generate batch of embeddings."""
        return [await mock_embed_text(text) for text in texts]

    strategy.embed_text = AsyncMock(side_effect=mock_embed_text)
    strategy.embed_batch = AsyncMock(side_effect=mock_embed_batch)

    return strategy


@pytest.fixture
def real_local_embeddings():
    """Real SentenceTransformers embeddings for realistic performance testing.

    Uses local model (no API calls) for reproducible benchmarks.
    """
    return SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")


@pytest.fixture
def perf_vector_store(perf_rag_config, mock_fast_embeddings):
    """Vector store for performance testing with fast mock embeddings."""
    store = VectorStore(perf_rag_config, mock_fast_embeddings)

    # Ensure clean state
    if store.count() > 0:
        store.reset()

    yield store

    # Cleanup
    store.reset()


@pytest_asyncio.fixture
async def perf_vector_store_with_data(perf_vector_store):
    """Vector store pre-populated with 100 test documents."""
    documents_data = generate_rag_documents(count=100, seed=42)

    documents = [d["text"] for d in documents_data]
    metadatas = [d["metadata"] for d in documents_data]
    ids = [f"doc-{i}" for i in range(len(documents))]

    await perf_vector_store.add_documents(documents=documents, metadatas=metadatas, ids=ids)

    assert perf_vector_store.count() == 100

    yield perf_vector_store


@pytest.fixture
def rag_test_documents_small():
    """Generate 10 test documents for small-scale tests."""
    return generate_rag_documents(count=10, seed=100)


@pytest.fixture
def rag_test_documents_medium():
    """Generate 100 test documents for medium-scale tests."""
    return generate_rag_documents(count=100, seed=200)


@pytest.fixture
def rag_test_documents_large():
    """Generate 1000 test documents for large-scale tests."""
    return generate_rag_documents(count=1000, seed=300)


@pytest.fixture
def sample_queries():
    """Sample search queries for retrieval testing."""
    return [
        "Fattura per consulenza informatica",
        "Cliente Tech Solutions pagamento €1000",
        "Sviluppo software gennaio 2025",
        "Servizi di marketing digitale",
        "Manutenzione sistemi IT P.IVA",
    ]


@pytest.fixture
def mock_indexer_session(monkeypatch):
    """Mock the _get_session function to return a test session.

    This fixture should be used with perf_db_with_invoices_* fixtures
    to inject the test database session into InvoiceIndexer.

    Usage:
        @pytest.fixture
        def indexer_with_db(perf_db_with_invoices_small, mock_indexer_session, perf_vector_store):
            session, clienti, fatture = perf_db_with_invoices_small
            mock_indexer_session(session)
            return InvoiceIndexer(perf_vector_store)
    """

    def _mock_session(session):
        """Inject a test session into the indexer."""
        from openfatture.ai.rag import indexing

        def _get_test_session():
            return session

        monkeypatch.setattr(indexing, "_get_session", _get_test_session)

    return _mock_session
