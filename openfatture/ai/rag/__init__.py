"""OpenFatture RAG (Retrieval-Augmented Generation) System.

This module provides semantic search and retrieval functionality using
ChromaDB vector store and embeddings.

Example Usage:
    >>> from openfatture.ai.rag import RAGSystem
    >>> from openfatture.ai.rag.config import RAGConfig
    >>>
    >>> # Initialize RAG system
    >>> config = RAGConfig()
    >>> rag = await RAGSystem.create(config, api_key="sk-...")
    >>>
    >>> # Index invoices
    >>> await rag.index_all_invoices()
    >>>
    >>> # Semantic search
    >>> results = await rag.search("Find web development invoices")
    >>>
    >>> # Get similar invoices
    >>> similar = await rag.find_similar_invoices(invoice_id=123)
"""

from typing import Optional

from openfatture.ai.rag.config import DEFAULT_RAG_CONFIG, RAGConfig, get_rag_config
from openfatture.ai.rag.embeddings import (
    EmbeddingStrategy,
    OpenAIEmbeddings,
    SentenceTransformerEmbeddings,
    create_embeddings,
)
from openfatture.ai.rag.indexing import InvoiceIndexer
from openfatture.ai.rag.knowledge_indexer import KnowledgeIndexer
from openfatture.ai.rag.retrieval import RetrievalResult, SemanticRetriever
from openfatture.ai.rag.vector_store import VectorStore
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class RAGSystem:
    """High-level RAG system interface.

    Combines vector store, indexing, and retrieval functionality
    into a single unified API.

    Example:
        >>> rag = await RAGSystem.create(config, api_key="sk-...")
        >>> await rag.index_all_invoices()
        >>> results = await rag.search("web development")
    """

    def __init__(
        self,
        config: RAGConfig,
        vector_store: VectorStore,
        indexer: InvoiceIndexer,
        retriever: SemanticRetriever,
    ) -> None:
        """Initialize RAG system.

        Use RAGSystem.create() factory method instead of direct instantiation.

        Args:
            config: RAG configuration
            vector_store: Vector store instance
            indexer: Invoice indexer instance
            retriever: Semantic retriever instance
        """
        self.config = config
        self.vector_store = vector_store
        self.indexer = indexer
        self.retriever = retriever

        logger.info("rag_system_initialized")

    @classmethod
    async def create(
        cls,
        config: RAGConfig | None = None,
        api_key: str | None = None,
    ) -> "RAGSystem":
        """Create and initialize RAG system.

        Args:
            config: RAG configuration (uses defaults if None)
            api_key: API key for embeddings (required for OpenAI)

        Returns:
            Initialized RAGSystem instance
        """
        if config is None:
            config = get_rag_config()

        # Create embedding strategy
        embeddings = create_embeddings(config, api_key=api_key)

        # Create vector store
        vector_store = VectorStore(config, embeddings)

        # Create indexer and retriever
        indexer = InvoiceIndexer(vector_store)
        retriever = SemanticRetriever(vector_store)

        return cls(config, vector_store, indexer, retriever)

    async def index_all_invoices(
        self,
        batch_size: int = 100,
        year: int | None = None,
    ) -> int:
        """Index all invoices.

        Args:
            batch_size: Batch size for processing
            year: Optional year filter

        Returns:
            Number of invoices indexed
        """
        return await self.indexer.index_all_invoices(
            batch_size=batch_size,
            year=year,
        )

    async def index_invoice(self, invoice_id: int) -> str:
        """Index a single invoice.

        Args:
            invoice_id: Invoice ID

        Returns:
            Document ID
        """
        return await self.indexer.index_invoice(invoice_id)

    async def search(
        self,
        query: str,
        top_k: int = 5,
        client_id: int | None = None,
        min_similarity: float | None = None,
    ) -> list[RetrievalResult]:
        """Semantic search for invoices.

        Args:
            query: Search query
            top_k: Number of results
            client_id: Optional client filter
            min_similarity: Minimum similarity threshold

        Returns:
            List of retrieval results
        """
        return await self.retriever.retrieve(
            query=query,
            top_k=top_k,
            client_id=client_id,
            min_similarity=min_similarity,
        )

    async def find_similar_invoices(
        self,
        invoice_id: int,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """Find invoices similar to a given invoice.

        Args:
            invoice_id: Invoice ID
            top_k: Number of similar invoices

        Returns:
            List of similar invoices
        """
        return await self.retriever.retrieve_similar_invoices(
            invoice_id=invoice_id,
            top_k=top_k,
        )

    async def get_client_invoices(
        self,
        client_id: int,
        query: str | None = None,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """Get invoices for a specific client.

        Args:
            client_id: Client ID
            query: Optional search query
            top_k: Number of results

        Returns:
            List of client invoices
        """
        return await self.retriever.retrieve_by_client(
            client_id=client_id,
            query=query,
            top_k=top_k,
        )

    def get_stats(self) -> dict:
        """Get RAG system statistics.

        Returns:
            Dictionary with stats
        """
        return self.vector_store.get_stats()

    async def reindex_year(self, year: int) -> int:
        """Reindex all invoices for a year.

        Args:
            year: Year to reindex

        Returns:
            Number of invoices reindexed
        """
        return await self.indexer.reindex_year(year)


__all__ = [
    # Main API
    "RAGSystem",
    # Configuration
    "RAGConfig",
    "get_rag_config",
    "DEFAULT_RAG_CONFIG",
    # Components
    "VectorStore",
    "InvoiceIndexer",
    "KnowledgeIndexer",
    "SemanticRetriever",
    "RetrievalResult",
    # Embeddings
    "EmbeddingStrategy",
    "OpenAIEmbeddings",
    "SentenceTransformerEmbeddings",
    "create_embeddings",
]
