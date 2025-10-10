"""Embedding generation strategies for RAG system.

This module provides embedding generation using different providers:
- OpenAI (text-embedding-3-small, text-embedding-3-large)
- Sentence Transformers (local models)
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import hashlib
import json

from openfatture.ai.rag.config import RAGConfig
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class EmbeddingStrategy(ABC):
    """Abstract base class for embedding strategies.

    All embedding providers must implement this interface.
    """

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Get embedding dimension."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get model name."""
        pass


class OpenAIEmbeddings(EmbeddingStrategy):
    """OpenAI embedding strategy.

    Uses OpenAI's embedding API (text-embedding-3-small, text-embedding-3-large).

    Example:
        >>> embeddings = OpenAIEmbeddings(api_key="sk-...", model="text-embedding-3-small")
        >>> vector = await embeddings.embed_text("Example text")
        >>> len(vector)
        1536
    """

    # Dimension mapping for OpenAI models
    MODEL_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        cache: Optional[any] = None,
    ) -> None:
        """Initialize OpenAI embeddings.

        Args:
            api_key: OpenAI API key
            model: Model name (default: text-embedding-3-small)
            cache: Optional cache for embeddings
        """
        self.api_key = api_key
        self.model = model
        self.cache = cache

        # Initialize OpenAI client
        from openai import AsyncOpenAI

        self.client = AsyncOpenAI(api_key=api_key)

        logger.info(
            "openai_embeddings_initialized",
            model=self.model,
            dimension=self.dimension,
        )

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        # Check cache first
        if self.cache:
            cache_key = self._generate_cache_key(text)
            cached = await self.cache.get(cache_key)
            if cached is not None:
                logger.debug("embedding_cache_hit", model=self.model)
                return cached

        try:
            # Call OpenAI API
            response = await self.client.embeddings.create(
                input=text,
                model=self.model,
            )

            embedding = response.data[0].embedding

            # Cache result
            if self.cache:
                await self.cache.set(cache_key, embedding)

            logger.debug(
                "embedding_generated",
                model=self.model,
                text_length=len(text),
            )

            return embedding

        except Exception as e:
            logger.error(
                "embedding_generation_failed",
                error=str(e),
                model=self.model,
            )
            raise

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        try:
            # Batch API call
            response = await self.client.embeddings.create(
                input=texts,
                model=self.model,
            )

            embeddings = [item.embedding for item in response.data]

            logger.info(
                "batch_embeddings_generated",
                model=self.model,
                count=len(texts),
            )

            return embeddings

        except Exception as e:
            logger.error(
                "batch_embedding_failed",
                error=str(e),
                model=self.model,
                count=len(texts),
            )
            raise

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return self.MODEL_DIMENSIONS.get(self.model, 1536)

    @property
    def model_name(self) -> str:
        """Get model name."""
        return self.model

    def _generate_cache_key(self, text: str) -> str:
        """Generate cache key for text embedding.

        Args:
            text: Input text

        Returns:
            Cache key (SHA256 hash)
        """
        key_data = {"model": self.model, "text": text}
        key_json = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_json.encode()).hexdigest()


class SentenceTransformerEmbeddings(EmbeddingStrategy):
    """Sentence Transformers embedding strategy.

    Uses local sentence-transformers models (all-MiniLM-L6-v2, etc.).

    Example:
        >>> embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        >>> vector = await embeddings.embed_text("Example text")
        >>> len(vector)
        384
    """

    # Dimension mapping for common models
    MODEL_DIMENSIONS = {
        "all-MiniLM-L6-v2": 384,
        "all-mpnet-base-v2": 768,
        "paraphrase-multilingual-MiniLM-L12-v2": 384,
    }

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: Optional[str] = None,
    ) -> None:
        """Initialize Sentence Transformers embeddings.

        Args:
            model_name: Model name (default: all-MiniLM-L6-v2)
            device: Device to use (cpu, cuda, mps)
        """
        self.model_name_str = model_name
        self.device = device

        # Lazy import (optional dependency)
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )

        # Load model
        self.model = SentenceTransformer(model_name, device=device)

        logger.info(
            "sentence_transformers_initialized",
            model=self.model_name_str,
            dimension=self.dimension,
            device=device or "auto",
        )

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        try:
            # Encode (runs in thread pool to avoid blocking)
            import asyncio

            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, self.model.encode, text
            )

            logger.debug(
                "embedding_generated",
                model=self.model_name_str,
                text_length=len(text),
            )

            return embedding.tolist()

        except Exception as e:
            logger.error(
                "embedding_generation_failed",
                error=str(e),
                model=self.model_name_str,
            )
            raise

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        try:
            # Batch encode
            import asyncio

            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, self.model.encode, texts
            )

            logger.info(
                "batch_embeddings_generated",
                model=self.model_name_str,
                count=len(texts),
            )

            return embeddings.tolist()

        except Exception as e:
            logger.error(
                "batch_embedding_failed",
                error=str(e),
                model=self.model_name_str,
                count=len(texts),
            )
            raise

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return self.MODEL_DIMENSIONS.get(self.model_name_str, 384)

    @property
    def model_name(self) -> str:
        """Get model name."""
        return self.model_name_str


def create_embeddings(config: RAGConfig, api_key: Optional[str] = None, cache: Optional[any] = None) -> EmbeddingStrategy:
    """Factory function to create embedding strategy.

    Args:
        config: RAG configuration
        api_key: API key (required for OpenAI)
        cache: Optional cache for embeddings

    Returns:
        EmbeddingStrategy instance

    Raises:
        ValueError: If provider is not supported
    """
    if config.embedding_provider == "openai":
        if not api_key:
            raise ValueError("OpenAI API key required for OpenAI embeddings")

        return OpenAIEmbeddings(
            api_key=api_key,
            model=config.embedding_model,
            cache=cache if config.enable_caching else None,
        )

    elif config.embedding_provider == "sentence-transformers":
        return SentenceTransformerEmbeddings(
            model_name=config.embedding_model,
        )

    else:
        raise ValueError(
            f"Unsupported embedding provider: {config.embedding_provider}"
        )
