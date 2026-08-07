"""Configuration for RAG Auto-Update System.

Pydantic-based configuration for automatic knowledge base updates.
Supports environment variables for production deployment.

Environment Variables:
- OPENFATTURE_RAG_AUTO_UPDATE_ENABLED: Enable auto-updates (default: false)
- OPENFATTURE_RAG_AUTO_UPDATE_BATCH_SIZE: Batch size for updates (default: 50)
- OPENFATTURE_RAG_AUTO_UPDATE_DEBOUNCE_SECONDS: Debounce delay (default: 5)
- OPENFATTURE_RAG_AUTO_UPDATE_MAX_QUEUE_SIZE: Max queue size (default: 1000)
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class AutoUpdateConfig(BaseSettings):
    """RAG auto-update configuration.

    All settings can be overridden via environment variables with prefix:
    OPENFATTURE_RAG_AUTO_UPDATE_*

    Example:
        >>> config = AutoUpdateConfig()
        >>> print(config.enabled)
        False
        >>>
        >>> # Override via environment
        >>> os.environ['OPENFATTURE_RAG_AUTO_UPDATE_ENABLED'] = 'true'
        >>> config = AutoUpdateConfig()
        >>> print(config.enabled)
        True
    """

    model_config = SettingsConfigDict(
        env_prefix="OPENFATTURE_RAG_AUTO_UPDATE_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Core Settings
    enabled: bool = Field(
        default=False,
        description="Enable automatic RAG updates (disabled by default for safety)",
    )

    # Queue Settings
    batch_size: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Number of entities to batch in single reindex operation",
    )

    debounce_seconds: int = Field(
        default=5,
        ge=1,
        le=300,
        description="Seconds to wait before processing batched changes (debounce)",
    )

    max_queue_size: int = Field(
        default=1000,
        ge=10,
        le=10000,
        description="Maximum queue size (older items dropped if exceeded)",
    )

    # Entity Tracking
    track_invoices: bool = Field(
        default=True,
        description="Track invoice changes for auto-reindex",
    )

    track_clients: bool = Field(
        default=True,
        description="Track client changes for auto-reindex",
    )

    track_products: bool = Field(
        default=False,
        description="Track product changes for auto-reindex",
    )

    # Update Strategy
    incremental_updates: bool = Field(
        default=True,
        description="Use incremental updates instead of full reindex",
    )

    delete_on_removal: bool = Field(
        default=True,
        description="Delete from vector store when entity is deleted",
    )

    # Performance
    async_processing: bool = Field(
        default=True,
        description="Process updates asynchronously in background",
    )

    max_concurrent_updates: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum concurrent reindex operations",
    )

    # Persistence
    queue_persist_path: Path = Field(
        default=Path(".cache/rag_update_queue.json"),
        description="Path to persist pending updates queue",
    )

    persist_queue_on_shutdown: bool = Field(
        default=True,
        description="Persist queue to disk on shutdown for recovery",
    )

    # Monitoring
    log_updates: bool = Field(
        default=True,
        description="Log all auto-update operations",
    )

    metrics_enabled: bool = Field(
        default=True,
        description="Track metrics (updates/sec, queue size, etc.)",
    )

    def __post_init__(self) -> None:
        """Post-initialization setup."""
        # Create queue persist directory
        if self.persist_queue_on_shutdown:
            self.queue_persist_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(
            "rag_auto_update_config_initialized",
            enabled=self.enabled,
            batch_size=self.batch_size,
            debounce_seconds=self.debounce_seconds,
            incremental_updates=self.incremental_updates,
        )

    def get_tracked_entities(self) -> list[str]:
        """Get list of tracked entity types.

        Returns:
            List of entity type names
        """
        entities = []
        if self.track_invoices:
            entities.append("invoice")
        if self.track_clients:
            entities.append("client")
        if self.track_products:
            entities.append("product")
        return entities


# Global config instance (singleton pattern)
_config: AutoUpdateConfig | None = None


def get_auto_update_config(force_reload: bool = False) -> AutoUpdateConfig:
    """Get or create auto-update configuration.

    Args:
        force_reload: Force reload from environment

    Returns:
        AutoUpdateConfig instance
    """
    global _config

    if _config is None or force_reload:
        _config = AutoUpdateConfig()
        _config.__post_init__()

    return _config


# Default configuration for easy access
AUTO_UPDATE_CONFIG = AutoUpdateConfig()
AUTO_UPDATE_CONFIG.__post_init__()
