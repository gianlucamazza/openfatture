"""RAG (Retrieval-Augmented Generation) configuration.

This module defines configuration settings for the RAG system using Pydantic.
"""

from pathlib import Path
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


class RAGConfig(BaseModel):
    """RAG system configuration settings.

    Example:
        >>> config = RAGConfig(
        ...     enabled=True,
        ...     embedding_model="text-embedding-3-small",
        ...     collection_name="invoices",
        ... )
    """

    # General settings
    enabled: bool = Field(
        default=True,
        description="Enable RAG system",
    )

    # ChromaDB settings
    persist_directory: Path = Field(
        default=Path(".chroma"),
        description="ChromaDB persistent storage directory",
    )

    collection_name: str = Field(
        default="openfatture",
        description="ChromaDB collection name",
    )

    # Embedding settings
    embedding_provider: Literal["openai", "sentence-transformers"] = Field(
        default="openai",
        description="Embedding provider (openai or sentence-transformers)",
    )

    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Embedding model name",
    )

    embedding_dimension: int = Field(
        default=1536,
        ge=1,
        description="Embedding vector dimension",
    )

    # Retrieval settings
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of results to retrieve",
    )

    similarity_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score threshold (0.0-1.0)",
    )

    # Indexing settings
    batch_size: int = Field(
        default=100,
        ge=1,
        description="Batch size for indexing operations",
    )

    enable_incremental: bool = Field(
        default=True,
        description="Enable incremental indexing",
    )

    # Performance settings
    enable_caching: bool = Field(
        default=True,
        description="Enable embedding caching",
    )

    cache_ttl: int = Field(
        default=3600,
        ge=0,
        description="Cache TTL in seconds",
    )

    @field_validator("persist_directory")
    @classmethod
    def validate_persist_directory(cls, v: Path) -> Path:
        """Ensure persist directory exists."""
        v = v.expanduser().resolve()
        v.mkdir(parents=True, exist_ok=True)
        return v

    class Config:
        """Pydantic config."""

        frozen = False
        extra = "forbid"


# Default configuration
DEFAULT_RAG_CONFIG = RAGConfig()


def get_rag_config() -> RAGConfig:
    """Get RAG configuration from environment.

    Reads RAG settings from environment variables:
    - OPENFATTURE_RAG_ENABLED: Enable/disable RAG
    - OPENFATTURE_RAG_PERSIST_DIR: ChromaDB storage directory
    - OPENFATTURE_RAG_COLLECTION: Collection name
    - OPENFATTURE_RAG_EMBEDDING_PROVIDER: Embedding provider
    - OPENFATTURE_RAG_EMBEDDING_MODEL: Embedding model
    - OPENFATTURE_RAG_TOP_K: Number of results
    - OPENFATTURE_RAG_SIMILARITY_THRESHOLD: Similarity threshold

    Returns:
        RAGConfig instance with settings from environment
    """
    import os

    return RAGConfig(
        enabled=os.getenv("OPENFATTURE_RAG_ENABLED", "true").lower() == "true",
        persist_directory=Path(
            os.getenv("OPENFATTURE_RAG_PERSIST_DIR", ".chroma")
        ),
        collection_name=os.getenv("OPENFATTURE_RAG_COLLECTION", "openfatture"),
        embedding_provider=os.getenv(
            "OPENFATTURE_RAG_EMBEDDING_PROVIDER", "openai"
        ),
        embedding_model=os.getenv(
            "OPENFATTURE_RAG_EMBEDDING_MODEL", "text-embedding-3-small"
        ),
        top_k=int(os.getenv("OPENFATTURE_RAG_TOP_K", "5")),
        similarity_threshold=float(
            os.getenv("OPENFATTURE_RAG_SIMILARITY_THRESHOLD", "0.7")
        ),
        enable_caching=os.getenv("OPENFATTURE_RAG_ENABLE_CACHING", "true").lower()
        == "true",
    )
