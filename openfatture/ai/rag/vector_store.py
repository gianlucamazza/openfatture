"""Vector store implementation using ChromaDB.

This module provides a wrapper around ChromaDB for persistent vector storage
and semantic search.
"""

import uuid
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any, cast

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
        metadata_dicts: list[dict[str, str | int | float | bool | None]]
        if metadatas is None:
            metadata_dicts = [{} for _ in documents]
        else:
            metadata_dicts = [_coerce_metadata_dict(metadata) for metadata in metadatas]

        timestamp = datetime.now().isoformat()
        for metadata in metadata_dicts:
            metadata["indexed_at"] = timestamp
            metadata["embedding_model"] = self.embedding_strategy.model_name

        embedding_matrix: list[Sequence[float]] = [list(vector) for vector in embeddings]
        metadata_payload = cast(list[Mapping[str, Any]], metadata_dicts)

        # Add to collection
        self.collection.add(
            documents=list(documents),
            embeddings=embedding_matrix,
            metadatas=metadata_payload,
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
        query_embeddings_payload: list[Sequence[float]] = [list(query_embedding)]

        # Build ChromaDB where clause for filters
        where = filters if filters else None

        # Search collection
        results = self.collection.query(
            query_embeddings=query_embeddings_payload,
            n_results=top_k,
            where=where,
        )

        # Process results
        processed_results = []

        ids_result = cast(Sequence[Sequence[str]] | None, results.get("ids"))
        documents_result = cast(Sequence[Sequence[str]] | None, results.get("documents"))
        metadatas_result = cast(
            Sequence[Sequence[Mapping[str, Any]]] | None, results.get("metadatas")
        )
        distances_result = cast(Sequence[Sequence[float]] | None, results.get("distances"))

        if ids_result and len(ids_result) > 0:
            doc_ids = ids_result[0]
            documents_list = documents_result[0] if documents_result else []
            metadatas_list = metadatas_result[0] if metadatas_result else []
            distances_list = distances_result[0] if distances_result else []

            for index, doc_id in enumerate(doc_ids):
                document_text = documents_list[index] if index < len(documents_list) else ""
                metadata_raw = metadatas_list[index] if index < len(metadatas_list) else {}
                distance = distances_list[index] if index < len(distances_list) else 1.0

                # ChromaDB returns distance, convert to similarity (1 - distance)
                similarity = 1.0 - distance

                # Filter by similarity threshold
                if similarity < min_similarity:
                    continue

                processed_results.append(
                    {
                        "id": doc_id,
                        "document": document_text,
                        "metadata": _coerce_metadata_dict(dict(metadata_raw)),
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

        ids_result = cast(list[str] | None, existing.get("ids"))
        if not ids_result:
            raise ValueError(f"Document {doc_id} not found")

        # Prepare update
        documents_result = cast(list[str] | None, existing.get("documents"))
        update_doc = document if document is not None else (documents_result or [""])[0]

        metadatas_result = cast(list[Mapping[str, Any]] | None, existing.get("metadatas"))
        update_metadata = _coerce_metadata_dict(
            dict(metadatas_result[0]) if metadatas_result else {}
        )

        if metadata:
            update_metadata.update(_coerce_metadata_dict(metadata))

        update_metadata["updated_at"] = datetime.now().isoformat()

        # Generate new embedding if document changed
        if document is not None:
            embedding_vector = await self.embedding_strategy.embed_text(document)
        else:
            embeddings_result = cast(list[list[float]] | None, existing.get("embeddings"))
            if embeddings_result and embeddings_result[0]:
                embedding_vector = list(embeddings_result[0])
            else:
                embedding_vector = await self.embedding_strategy.embed_text(update_doc)

        # Update collection
        embedding_payload: list[Sequence[float]] = [list(embedding_vector)]

        self.collection.update(
            ids=[doc_id],
            documents=[update_doc],
            embeddings=embedding_payload,
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

        ids_value = results.get("ids")
        ids_list = list(ids_value) if isinstance(ids_value, list) else None

        if ids_list:
            count = len(ids_list)
            self.collection.delete(ids=ids_list)

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

        ids_value = results.get("ids")
        documents_value = results.get("documents")
        metadatas_value = results.get("metadatas")

        if isinstance(ids_value, list) and ids_value:
            document_text = documents_value[0] if isinstance(documents_value, list) else ""
            metadata_raw = (
                metadatas_value[0] if isinstance(metadatas_value, list) and metadatas_value else {}
            )
            return {
                "id": ids_value[0],
                "document": document_text,
                "metadata": _coerce_metadata_dict(dict(metadata_raw)),
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
        self.client.delete_collection(name=self.config.collection_name)

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


MetadataValue = str | int | float | bool | None


def _coerce_metadata_dict(metadata: Mapping[str, Any]) -> dict[str, MetadataValue]:
    """Convert metadata values to supported scalar types."""
    typed_metadata: dict[str, MetadataValue] = {}
    for key, value in metadata.items():
        if isinstance(value, str | int | float | bool) or value is None:
            typed_metadata[key] = value
        else:
            typed_metadata[key] = str(value)
    return typed_metadata
