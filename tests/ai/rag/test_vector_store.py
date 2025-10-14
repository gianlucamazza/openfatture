"""Tests for RAG vector store (ChromaDB wrapper).

Tests core vector store operations with in-memory ChromaDB.

Run with: pytest tests/ai/rag/test_vector_store.py -v
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openfatture.ai.rag.config import RAGConfig
from openfatture.ai.rag.embeddings import EmbeddingStrategy
from openfatture.ai.rag.vector_store import VectorStore


@pytest.fixture
def mock_embedding_strategy():
    """Create mock embedding strategy."""
    strategy = MagicMock(spec=EmbeddingStrategy)
    strategy.dimension = 384
    strategy.model_name = "mock-embedder"

    # Mock embedding generation
    async def mock_embed_text(text):
        # Generate deterministic embedding based on text length
        return [0.1 * len(text)] * 384

    async def mock_embed_batch(texts):
        return [[0.1 * len(text)] * 384 for text in texts]

    strategy.embed_text = AsyncMock(side_effect=mock_embed_text)
    strategy.embed_batch = AsyncMock(side_effect=mock_embed_batch)

    return strategy


@pytest.fixture
def temp_rag_config():
    """Create RAG config with temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = RAGConfig(
            persist_directory=Path(tmpdir) / "chroma",
            collection_name="test_collection",
        )
        yield config


@pytest.mark.asyncio
class TestVectorStore:
    """Test VectorStore operations."""

    async def test_vector_store_initialization(
        self, temp_rag_config, mock_embedding_strategy
    ):
        """Test vector store initializes correctly."""
        store = VectorStore(temp_rag_config, mock_embedding_strategy)

        assert store.config == temp_rag_config
        assert store.embedding_strategy == mock_embedding_strategy
        assert store.collection is not None
        assert store.count() == 0

    async def test_add_documents(self, temp_rag_config, mock_embedding_strategy):
        """Test adding documents to vector store."""
        store = VectorStore(temp_rag_config, mock_embedding_strategy)

        documents = ["Document 1", "Document 2", "Document 3"]
        metadatas = [
            {"type": "invoice", "year": 2025},
            {"type": "invoice", "year": 2025},
            {"type": "client", "year": 2024},
        ]

        ids = await store.add_documents(documents, metadatas)

        assert len(ids) == 3
        assert store.count() == 3
        # Verify embeddings were generated
        assert mock_embedding_strategy.embed_batch.call_count == 1

    async def test_search_documents(self, temp_rag_config, mock_embedding_strategy):
        """Test searching for similar documents."""
        store = VectorStore(temp_rag_config, mock_embedding_strategy)

        # Add test documents
        documents = [
            "Software development services",
            "Graphic design consultation",
            "IT infrastructure management",
        ]
        await store.add_documents(documents)

        # Search
        results = await store.search("software development", top_k=2)

        assert len(results) <= 2
        if results:
            assert "document" in results[0]
            assert "similarity" in results[0]
            assert "metadata" in results[0]

    async def test_search_with_filters(self, temp_rag_config, mock_embedding_strategy):
        """Test searching with metadata filters."""
        store = VectorStore(temp_rag_config, mock_embedding_strategy)

        documents = ["Doc 2024", "Doc 2025 A", "Doc 2025 B"]
        metadatas = [
            {"year": 2024},
            {"year": 2025},
            {"year": 2025},
        ]

        await store.add_documents(documents, metadatas)

        # Search with filter
        results = await store.search(
            "document",
            top_k=5,
            filters={"year": 2025},
        )

        # Should only return 2025 documents
        assert all(r["metadata"].get("year") == 2025 for r in results)

    async def test_get_document(self, temp_rag_config, mock_embedding_strategy):
        """Test retrieving document by ID."""
        store = VectorStore(temp_rag_config, mock_embedding_strategy)

        documents = ["Test document"]
        ids = await store.add_documents(documents)
        doc_id = ids[0]

        # Get document
        doc = store.get_document(doc_id)

        assert doc is not None
        assert doc["id"] == doc_id
        assert doc["document"] == "Test document"
        assert "metadata" in doc

    async def test_delete_documents(self, temp_rag_config, mock_embedding_strategy):
        """Test deleting documents."""
        store = VectorStore(temp_rag_config, mock_embedding_strategy)

        documents = ["Doc 1", "Doc 2", "Doc 3"]
        ids = await store.add_documents(documents)

        # Delete first document
        await store.delete_documents([ids[0]])

        assert store.count() == 2
        assert store.get_document(ids[0]) is None

    async def test_count(self, temp_rag_config, mock_embedding_strategy):
        """Test document count."""
        store = VectorStore(temp_rag_config, mock_embedding_strategy)

        assert store.count() == 0

        await store.add_documents(["Doc 1", "Doc 2"])
        assert store.count() == 2

        await store.add_documents(["Doc 3"])
        assert store.count() == 3

    async def test_get_stats(self, temp_rag_config, mock_embedding_strategy):
        """Test getting collection statistics."""
        store = VectorStore(temp_rag_config, mock_embedding_strategy)

        await store.add_documents(["Test doc"])

        stats = store.get_stats()

        assert stats["collection_name"] == "test_collection"
        assert stats["document_count"] == 1
        assert stats["embedding_dimension"] == 384
        assert stats["embedding_model"] == "mock-embedder"

    async def test_reset_collection(self, temp_rag_config, mock_embedding_strategy):
        """Test resetting collection."""
        store = VectorStore(temp_rag_config, mock_embedding_strategy)

        # Add documents
        await store.add_documents(["Doc 1", "Doc 2", "Doc 3"])
        assert store.count() == 3

        # Reset
        store.reset()

        assert store.count() == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
