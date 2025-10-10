"""Semantic retrieval for RAG system.

This module provides semantic search and retrieval functionality.
"""

from dataclasses import dataclass
from typing import Any

from openfatture.ai.rag.vector_store import VectorStore
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievalResult:
    """Result from semantic retrieval.

    Attributes:
        document: Retrieved document text
        metadata: Document metadata
        similarity: Similarity score (0-1)
        invoice_id: Invoice ID (if applicable)
        client_name: Client name (if applicable)
    """

    document: str
    metadata: dict[str, Any]
    similarity: float
    invoice_id: int | None = None
    client_name: str | None = None

    def __post_init__(self):
        """Extract common fields from metadata."""
        if self.metadata:
            self.invoice_id = self.metadata.get("invoice_id")
            self.client_name = self.metadata.get("client_name")


class SemanticRetriever:
    """Semantic retrieval for RAG system.

    Features:
    - Query-based retrieval with filters
    - Client-specific search
    - Date range filtering
    - Relevance reranking
    - Result deduplication

    Example:
        >>> retriever = SemanticRetriever(vector_store)
        >>> results = await retriever.retrieve(
        ...     query="Find invoices for web development",
        ...     top_k=5,
        ...     client_id=123,
        ... )
    """

    def __init__(self, vector_store: VectorStore) -> None:
        """Initialize semantic retriever.

        Args:
            vector_store: Vector store instance
        """
        self.vector_store = vector_store

        logger.info("semantic_retriever_initialized")

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        client_id: int | None = None,
        min_similarity: float | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        """Retrieve relevant documents.

        Args:
            query: Search query
            top_k: Number of results to return
            client_id: Optional client ID filter
            min_similarity: Minimum similarity threshold
            filters: Additional metadata filters

        Returns:
            List of RetrievalResult objects
        """
        # Build filters
        search_filters = filters or {}

        if client_id:
            search_filters["client_id"] = client_id

        # Ensure we only search invoices
        search_filters["type"] = "invoice"

        # Search vector store
        raw_results = await self.vector_store.search(
            query=query,
            top_k=top_k,
            filters=search_filters if search_filters else None,
            min_similarity=min_similarity,
        )

        # Convert to RetrievalResult objects
        results = [
            RetrievalResult(
                document=r["document"],
                metadata=r["metadata"],
                similarity=r["similarity"],
            )
            for r in raw_results
        ]

        logger.info(
            "retrieval_completed",
            query_length=len(query),
            results_count=len(results),
            top_k=top_k,
        )

        return results

    async def retrieve_similar_invoices(
        self,
        invoice_id: int,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """Find invoices similar to a given invoice.

        Args:
            invoice_id: Invoice ID to find similar invoices for
            top_k: Number of similar invoices to return

        Returns:
            List of similar invoices
        """
        # Get the invoice document
        doc_id = f"invoice-{invoice_id}"
        doc = self.vector_store.get_document(doc_id)

        if not doc:
            raise ValueError(f"Invoice {invoice_id} not found in vector store")

        # Search for similar documents
        results = await self.retrieve(
            query=doc["document"],
            top_k=top_k + 1,  # +1 because the invoice itself will be in results
        )

        # Filter out the invoice itself
        filtered_results = [r for r in results if r.invoice_id != invoice_id]

        return filtered_results[:top_k]

    async def retrieve_by_client(
        self,
        client_id: int,
        query: str | None = None,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """Retrieve invoices for a specific client.

        Args:
            client_id: Client ID
            query: Optional search query
            top_k: Number of results

        Returns:
            List of client invoices
        """
        if query:
            # Semantic search within client invoices
            results = await self.retrieve(
                query=query,
                top_k=top_k,
                client_id=client_id,
            )
        else:
            # Get all client invoices (sorted by relevance to generic query)
            results = await self.retrieve(
                query="fatture del cliente",  # Generic query
                top_k=top_k,
                client_id=client_id,
            )

        logger.info(
            "client_invoices_retrieved",
            client_id=client_id,
            count=len(results),
        )

        return results

    async def retrieve_by_date_range(
        self,
        query: str,
        start_date: str,
        end_date: str,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """Retrieve invoices within a date range.

        Args:
            query: Search query
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            top_k: Number of results

        Returns:
            List of invoices in date range
        """
        # Note: ChromaDB doesn't support range queries directly
        # We retrieve more results and filter manually

        results = await self.retrieve(
            query=query,
            top_k=top_k * 3,  # Get more to filter
        )

        # Filter by date range
        filtered_results = [
            r
            for r in results
            if r.metadata.get("date") and start_date <= r.metadata["date"] <= end_date
        ]

        logger.info(
            "date_range_retrieval",
            start_date=start_date,
            end_date=end_date,
            results_count=len(filtered_results),
        )

        return filtered_results[:top_k]

    async def retrieve_high_value_invoices(
        self,
        query: str,
        min_amount: float,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """Retrieve high-value invoices.

        Args:
            query: Search query
            min_amount: Minimum invoice amount
            top_k: Number of results

        Returns:
            List of high-value invoices
        """
        # Retrieve more results to filter
        results = await self.retrieve(
            query=query,
            top_k=top_k * 3,
        )

        # Filter by amount
        filtered_results = [r for r in results if r.metadata.get("amount", 0) >= min_amount]

        # Sort by amount (descending)
        filtered_results.sort(
            key=lambda x: x.metadata.get("amount", 0),
            reverse=True,
        )

        logger.info(
            "high_value_retrieval",
            min_amount=min_amount,
            results_count=len(filtered_results),
        )

        return filtered_results[:top_k]

    def format_results(self, results: list[RetrievalResult]) -> str:
        """Format retrieval results as text.

        Args:
            results: List of retrieval results

        Returns:
            Formatted text summary
        """
        if not results:
            return "Nessun risultato trovato"

        lines = [f"Trovati {len(results)} risultati:\n"]

        for i, result in enumerate(results, 1):
            lines.append(
                f"{i}. {result.client_name} - "
                f"€{result.metadata.get('amount', 0):.2f} "
                f"(Similarity: {result.similarity:.2%})"
            )

            # Add invoice number if available
            if result.metadata.get("invoice_number"):
                lines[-1] += (
                    f" - Fattura {result.metadata['invoice_number']}/"
                    f"{result.metadata.get('invoice_year', '')}"
                )

        return "\n".join(lines)
