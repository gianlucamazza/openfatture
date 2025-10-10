"""Vector store implementation using ChromaDB.

This module provides a wrapper around ChromaDB for persistent vector storage
and semantic search.
"""

import uuid
from datetime import datetime
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings

from openfatture.ai.rag.config import RAGConfig
from openfatture.ai.rag.embeddings import EmbeddingStrategy
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class VectorStore:
    """Vector store using ChromaDB for persistent storage.

    Features:
    - Persistent storage with automatic checkpointing
    - Metadata filtering for advanced search
    - Batch operations for efficiency
    - Automatic embedding generation
    - Incremental indexing support

    Example:
        >>> config = RAGConfig()
        >>> embeddings = create_embeddings(config, api_key="...")
        >>> store = VectorStore(config, embeddings)
        >>>
        >>> # Add documents
        >>> await store.add_documents(
        ...     documents=["Doc 1", "Doc 2"],
        ...     metadatas=[{"type": "invoice"}, {"type": "invoice"}],
        ...     ids=["inv-1", "inv-2"],
        ... )
        >>>
        >>> # Search
        >>> results = await store.search(
        ...     query="Find invoice",
        ...     top_k=5,
        ...     filters={"type": "invoice"},
        ... )
    """

    def __init__(
        self,
        config: RAGConfig,
        embedding_strategy: EmbeddingStrategy,
    ) -> None:
        """Initialize vector store.

        Args:
            config: RAG configuration
            embedding_strategy: Embedding strategy for vectorization
        """
        self.config = config
        self.embedding_strategy = embedding_strategy

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(config.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        # Get or create collection
        self.collection: Collection = self.client.get_or_create_collection(
            name=config.collection_name,
            metadata={"dimension": embedding_strategy.dimension},
        )

        logger.info(
            "vector_store_initialized",
            collection=config.collection_name,
            dimension=embedding_strategy.dimension,
            persist_directory=str(config.persist_directory),
            document_count=self.collection.count(),
        )

    async def add_documents(
        self,
        documents: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> list[str]:
        """Add documents to the vector store.

        Args:
            documents: List of document texts
            metadatas: Optional list of metadata dicts
            ids: Optional list of document IDs (generated if None)

        Returns:
            List of document IDs
        """
        if not documents:
            return []

        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]

        # Generate embeddings
        logger.info(
            "generating_embeddings",
            count=len(documents),
            model=self.embedding_strategy.model_name,
        )

        embeddings = await self.embedding_strategy.embed_batch(documents)

        # Add timestamp to metadata
        if metadatas is None:
            metadatas = [{}] * len(documents)

        for metadata in metadatas:
            metadata["indexed_at"] = datetime.now().isoformat()
            metadata["embedding_model"] = self.embedding_strategy.model_name

        # Add to collection
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )

        logger.info(
            "documents_added",
            count=len(documents),
            collection=self.config.collection_name,
            total_count=self.collection.count(),
        )

        return ids

    async def search(
        self,
        query: str,
        top_k: int | None = None,
        filters: dict[str, Any] | None = None,
        min_similarity: float | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar documents.

        Args:
            query: Search query text
            top_k: Number of results to return (default: config.top_k)
            filters: Optional metadata filters
            min_similarity: Minimum similarity threshold (default: config.similarity_threshold)

        Returns:
            List of result dictionaries with:
            - id: Document ID
            - document: Document text
            - metadata: Document metadata
            - similarity: Similarity score (0-1)
        """
        if top_k is None:
            top_k = self.config.top_k

        if min_similarity is None:
            min_similarity = self.config.similarity_threshold

        # Generate query embedding
        query_embedding = await self.embedding_strategy.embed_text(query)

        # Build ChromaDB where clause for filters
        where = filters if filters else None

        # Search collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
        )

        # Process results
        processed_results = []

        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                # ChromaDB returns distance, convert to similarity (1 - distance)
                distance = results["distances"][0][i] if results["distances"] else 1.0
                similarity = 1.0 - distance

                # Filter by similarity threshold
                if similarity < min_similarity:
                    continue

                processed_results.append(
                    {
                        "id": doc_id,
                        "document": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "similarity": similarity,
                    }
                )

        logger.info(
            "search_completed",
            query_length=len(query),
            results_count=len(processed_results),
            top_k=top_k,
            min_similarity=min_similarity,
        )

        return processed_results

    async def update_document(
        self,
        doc_id: str,
        document: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Update an existing document.

        Args:
            doc_id: Document ID
            document: New document text (if changing)
            metadata: New metadata (merged with existing)
        """
        # Get existing document
        existing = self.collection.get(ids=[doc_id])

        if not existing["ids"]:
            raise ValueError(f"Document {doc_id} not found")

        # Prepare update
        update_doc = document if document is not None else existing["documents"][0]
        update_metadata = existing["metadatas"][0] if existing["metadatas"] else {}

        if metadata:
            update_metadata.update(metadata)

        update_metadata["updated_at"] = datetime.now().isoformat()

        # Generate new embedding if document changed
        if document is not None:
            embedding = await self.embedding_strategy.embed_text(document)
        else:
            embedding = existing["embeddings"][0]

        # Update collection
        self.collection.update(
            ids=[doc_id],
            documents=[update_doc],
            embeddings=[embedding],
            metadatas=[update_metadata],
        )

        logger.info("document_updated", doc_id=doc_id)

    async def delete_documents(self, ids: list[str]) -> None:
        """Delete documents by IDs.

        Args:
            ids: List of document IDs to delete
        """
        self.collection.delete(ids=ids)

        logger.info(
            "documents_deleted",
            count=len(ids),
            total_count=self.collection.count(),
        )

    async def delete_by_filter(self, filters: dict[str, Any]) -> int:
        """Delete documents matching filters.

        Args:
            filters: Metadata filters

        Returns:
            Number of documents deleted
        """
        # Get matching documents
        results = self.collection.get(where=filters)

        if results["ids"]:
            count = len(results["ids"])
            self.collection.delete(ids=results["ids"])

            logger.info(
                "documents_deleted_by_filter",
                count=count,
                filters=filters,
            )

            return count

        return 0

    def get_document(self, doc_id: str) -> dict[str, Any] | None:
        """Get a document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Document dict or None if not found
        """
        results = self.collection.get(ids=[doc_id])

        if results["ids"]:
            return {
                "id": results["ids"][0],
                "document": results["documents"][0],
                "metadata": results["metadatas"][0] if results["metadatas"] else {},
            }

        return None

    def count(self) -> int:
        """Get total document count.

        Returns:
            Number of documents in collection
        """
        return self.collection.count()

    def reset(self) -> None:
        """Delete all documents from collection.

        Warning: This is destructive and cannot be undone!
        """
        logger.warning("resetting_collection", collection=self.config.collection_name)

        # Delete collection and recreate
        self.client.delete_collection(self.config.collection_name)

        self.collection = self.client.get_or_create_collection(
            name=self.config.collection_name,
            metadata={"dimension": self.embedding_strategy.dimension},
        )

        logger.info("collection_reset", collection=self.config.collection_name)

    def get_stats(self) -> dict[str, Any]:
        """Get collection statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "collection_name": self.config.collection_name,
            "document_count": self.collection.count(),
            "embedding_dimension": self.embedding_strategy.dimension,
            "embedding_model": self.embedding_strategy.model_name,
            "persist_directory": str(self.config.persist_directory),
        }
