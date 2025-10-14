"""Tests for RAG embedding generation.

Tests embedding strategies (OpenAI and SentenceTransformers) with mocked APIs.

Run with: pytest tests/ai/rag/test_embeddings.py -v
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openfatture.ai.rag.config import RAGConfig
from openfatture.ai.rag.embeddings import (
    OpenAIEmbeddings,
    SentenceTransformerEmbeddings,
    create_embeddings,
)


@pytest.fixture
def mock_openai_response():
    """Create mock OpenAI embedding response."""
    # Mock single embedding response
    single_response = MagicMock()
    single_response.data = [MagicMock(embedding=[0.1] * 1536)]

    # Mock batch embedding response
    batch_response = MagicMock()
    batch_response.data = [
        MagicMock(embedding=[0.1] * 1536),
        MagicMock(embedding=[0.2] * 1536),
        MagicMock(embedding=[0.3] * 1536),
    ]

    return {"single": single_response, "batch": batch_response}


@pytest.fixture
def mock_embedding_cache():
    """Create mock embedding cache."""
    cache = MagicMock()
    cache_storage = {}

    async def mock_get(key):
        return cache_storage.get(key)

    async def mock_set(key, value):
        cache_storage[key] = value

    cache.get = AsyncMock(side_effect=mock_get)
    cache.set = AsyncMock(side_effect=mock_set)

    return cache


@pytest.mark.asyncio
class TestOpenAIEmbeddings:
    """Test OpenAI embeddings provider."""

    async def test_openai_embeddings_initialization(self):
        """Test OpenAI embeddings initializes correctly."""
        with patch("openai.AsyncOpenAI"):
            embeddings = OpenAIEmbeddings(
                api_key="test-key",
                model="text-embedding-3-small",
            )

            assert embeddings.model == "text-embedding-3-small"
            assert embeddings.dimension == 1536
            assert embeddings.model_name == "text-embedding-3-small"

    async def test_embed_text_single(self, mock_openai_response):
        """Test generating embedding for single text."""
        with patch("openai.AsyncOpenAI") as mock_openai_class:
            # Setup mock client
            mock_client = MagicMock()
            mock_client.embeddings.create = AsyncMock(
                return_value=mock_openai_response["single"]
            )
            mock_openai_class.return_value = mock_client

            embeddings = OpenAIEmbeddings(api_key="test-key")

            # Generate embedding
            result = await embeddings.embed_text("Test text")

            # Verify
            assert isinstance(result, list)
            assert len(result) == 1536
            assert result[0] == 0.1
            mock_client.embeddings.create.assert_called_once()

    async def test_embed_batch(self, mock_openai_response):
        """Test generating embeddings for multiple texts."""
        with patch("openai.AsyncOpenAI") as mock_openai_class:
            mock_client = MagicMock()
            mock_client.embeddings.create = AsyncMock(
                return_value=mock_openai_response["batch"]
            )
            mock_openai_class.return_value = mock_client

            embeddings = OpenAIEmbeddings(api_key="test-key")

            # Generate batch embeddings
            texts = ["Text 1", "Text 2", "Text 3"]
            results = await embeddings.embed_batch(texts)

            # Verify
            assert len(results) == 3
            assert all(len(emb) == 1536 for emb in results)
            assert results[0][0] == 0.1
            assert results[1][0] == 0.2
            assert results[2][0] == 0.3

    async def test_embed_text_with_cache_miss(
        self, mock_openai_response, mock_embedding_cache
    ):
        """Test embedding with cache miss."""
        with patch("openai.AsyncOpenAI") as mock_openai_class:
            mock_client = MagicMock()
            mock_client.embeddings.create = AsyncMock(
                return_value=mock_openai_response["single"]
            )
            mock_openai_class.return_value = mock_client

            embeddings = OpenAIEmbeddings(
                api_key="test-key",
                cache=mock_embedding_cache,
            )

            # Generate embedding (cache miss)
            result = await embeddings.embed_text("Test text")

            # Verify API was called
            assert mock_client.embeddings.create.call_count == 1
            # Verify cache was set
            assert mock_embedding_cache.set.call_count == 1

    async def test_embed_text_with_cache_hit(
        self, mock_openai_response, mock_embedding_cache
    ):
        """Test embedding with cache hit."""
        with patch("openai.AsyncOpenAI") as mock_openai_class:
            mock_client = MagicMock()
            mock_client.embeddings.create = AsyncMock(
                return_value=mock_openai_response["single"]
            )
            mock_openai_class.return_value = mock_client

            embeddings = OpenAIEmbeddings(
                api_key="test-key",
                cache=mock_embedding_cache,
            )

            # First call (cache miss)
            result1 = await embeddings.embed_text("Test text")

            # Second call (cache hit)
            result2 = await embeddings.embed_text("Test text")

            # Verify API was called only once
            assert mock_client.embeddings.create.call_count == 1
            # Results should be identical
            assert result1 == result2

    async def test_embed_text_error_handling(self):
        """Test error handling in embedding generation."""
        with patch("openai.AsyncOpenAI") as mock_openai_class:
            mock_client = MagicMock()
            mock_client.embeddings.create = AsyncMock(
                side_effect=Exception("API Error")
            )
            mock_openai_class.return_value = mock_client

            embeddings = OpenAIEmbeddings(api_key="test-key")

            # Should raise exception
            with pytest.raises(Exception, match="API Error"):
                await embeddings.embed_text("Test text")

    async def test_different_model_dimensions(self):
        """Test dimension property for different models."""
        with patch("openai.AsyncOpenAI"):
            # text-embedding-3-small
            emb_small = OpenAIEmbeddings(
                api_key="test-key",
                model="text-embedding-3-small",
            )
            assert emb_small.dimension == 1536

            # text-embedding-3-large
            emb_large = OpenAIEmbeddings(
                api_key="test-key",
                model="text-embedding-3-large",
            )
            assert emb_large.dimension == 3072

            # text-embedding-ada-002
            emb_ada = OpenAIEmbeddings(
                api_key="test-key",
                model="text-embedding-ada-002",
            )
            assert emb_ada.dimension == 1536


@pytest.mark.asyncio
class TestSentenceTransformerEmbeddings:
    """Test SentenceTransformer embeddings provider."""

    async def test_sentence_transformer_initialization(self):
        """Test SentenceTransformer initializes correctly."""
        with patch("openfatture.ai.rag.embeddings.SentenceTransformer"):
            embeddings = SentenceTransformerEmbeddings(
                model_name="all-MiniLM-L6-v2"
            )

            assert embeddings.model_name == "all-MiniLM-L6-v2"
            assert embeddings.dimension == 384

    async def test_embed_text_sentence_transformer(self):
        """Test embedding generation with SentenceTransformer."""
        with patch("openfatture.ai.rag.embeddings.SentenceTransformer") as mock_st:
            # Mock model encode method
            import numpy as np

            mock_model = MagicMock()
            mock_embedding = np.array([0.5] * 384)
            mock_model.encode.return_value = mock_embedding
            mock_st.return_value = mock_model

            embeddings = SentenceTransformerEmbeddings(
                model_name="all-MiniLM-L6-v2"
            )

            # Generate embedding
            result = await embeddings.embed_text("Test text")

            # Verify
            assert isinstance(result, list)
            assert len(result) == 384
            assert result[0] == 0.5
            mock_model.encode.assert_called_once_with("Test text")

    async def test_embed_batch_sentence_transformer(self):
        """Test batch embedding with SentenceTransformer."""
        with patch("openfatture.ai.rag.embeddings.SentenceTransformer") as mock_st:
            import numpy as np

            mock_model = MagicMock()
            mock_embeddings = np.array([
                [0.1] * 384,
                [0.2] * 384,
                [0.3] * 384,
            ])
            mock_model.encode.return_value = mock_embeddings
            mock_st.return_value = mock_model

            embeddings = SentenceTransformerEmbeddings(
                model_name="all-MiniLM-L6-v2"
            )

            # Generate batch embeddings
            texts = ["Text 1", "Text 2", "Text 3"]
            results = await embeddings.embed_batch(texts)

            # Verify
            assert len(results) == 3
            assert all(len(emb) == 384 for emb in results)
            assert results[0][0] == 0.1
            assert results[1][0] == 0.2


@pytest.mark.asyncio
class TestEmbeddingFactory:
    """Test embedding factory function."""

    async def test_create_openai_embeddings(self):
        """Test factory creates OpenAI embeddings."""
        config = RAGConfig(
            embedding_provider="openai",
            embedding_model="text-embedding-3-small",
        )

        with patch("openai.AsyncOpenAI"):
            embeddings = create_embeddings(config, api_key="test-key")

            assert isinstance(embeddings, OpenAIEmbeddings)
            assert embeddings.model == "text-embedding-3-small"

    async def test_create_sentence_transformer_embeddings(self):
        """Test factory creates SentenceTransformer embeddings."""
        config = RAGConfig(
            embedding_provider="sentence-transformers",
            embedding_model="all-MiniLM-L6-v2",
        )

        with patch("openfatture.ai.rag.embeddings.SentenceTransformer"):
            embeddings = create_embeddings(config)

            assert isinstance(embeddings, SentenceTransformerEmbeddings)
            assert embeddings.model_name == "all-MiniLM-L6-v2"

    async def test_create_embeddings_missing_api_key(self):
        """Test factory raises error when OpenAI API key missing."""
        config = RAGConfig(
            embedding_provider="openai",
            embedding_model="text-embedding-3-small",
        )

        with pytest.raises(ValueError, match="OpenAI API key required"):
            create_embeddings(config, api_key=None)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
