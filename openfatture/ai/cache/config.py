"""Cache configuration and settings.

This module defines cache settings and configuration using Pydantic.
"""

import logging
import os
from typing import Literal, cast

from pydantic import BaseModel, ConfigDict, Field


class CacheConfig(BaseModel):
    """Cache configuration settings.

    Example:
        >>> config = CacheConfig(
        ...     enabled=True,
        ...     strategy="lru",
        ...     max_size=1000,
        ...     default_ttl=3600,
        ... )
    """

    # General settings
    enabled: bool = Field(
        default=True,
        description="Enable caching system",
    )

    strategy: Literal["lru", "semantic", "hybrid"] = Field(
        default="lru",
        description="Cache strategy to use (lru, semantic, or hybrid)",
    )

    # LRU Cache settings
    max_size: int = Field(
        default=1000,
        ge=1,
        description="Maximum number of cache entries",
    )

    default_ttl: int | None = Field(
        default=3600,
        ge=0,
        description="Default TTL in seconds (None = no expiration)",
    )

    cleanup_interval: int = Field(
        default=300,
        ge=0,
        description="Cleanup interval in seconds (0 = no automatic cleanup)",
    )

    # Semantic Cache settings (for future implementation)
    similarity_threshold: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Similarity threshold for semantic cache (0.0-1.0)",
    )

    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Embedding model for semantic cache",
    )

    # Performance settings
    enable_stats: bool = Field(
        default=True,
        description="Enable statistics tracking",
    )

    log_hits: bool = Field(
        default=False,
        description="Log cache hits (verbose, for debugging)",
    )

    log_misses: bool = Field(
        default=False,
        description="Log cache misses (verbose, for debugging)",
    )

    model_config = ConfigDict(
        frozen=False,  # Allow modification
        extra="forbid",  # Reject unknown fields
    )


# Default configuration
DEFAULT_CACHE_CONFIG = CacheConfig()

_logger = logging.getLogger(__name__)


def get_cache_config() -> CacheConfig:
    """Get cache configuration from environment.

    Reads cache settings from environment variables:
    - OPENFATTURE_CACHE_ENABLED: Enable/disable caching
    - OPENFATTURE_CACHE_STRATEGY: Cache strategy
    - OPENFATTURE_CACHE_MAX_SIZE: Maximum cache size
    - OPENFATTURE_CACHE_DEFAULT_TTL: Default TTL
    - OPENFATTURE_CACHE_CLEANUP_INTERVAL: Cleanup interval

    Returns:
        CacheConfig instance with settings from environment
    """
    strategy_raw = os.getenv("OPENFATTURE_CACHE_STRATEGY", "lru")
    if strategy_raw not in {"lru", "semantic", "hybrid"}:
        _logger.warning(
            "Invalid cache strategy '%s'. Falling back to 'lru'.",
            strategy_raw,
        )
        strategy_raw = "lru"

    strategy = cast(Literal["lru", "semantic", "hybrid"], strategy_raw)

    return CacheConfig(
        enabled=os.getenv("OPENFATTURE_CACHE_ENABLED", "true").lower() == "true",
        strategy=strategy,
        max_size=int(os.getenv("OPENFATTURE_CACHE_MAX_SIZE", "1000")),
        default_ttl=int(os.getenv("OPENFATTURE_CACHE_DEFAULT_TTL", "3600")),
        cleanup_interval=int(os.getenv("OPENFATTURE_CACHE_CLEANUP_INTERVAL", "300")),
        similarity_threshold=float(os.getenv("OPENFATTURE_CACHE_SIMILARITY_THRESHOLD", "0.85")),
        embedding_model=os.getenv("OPENFATTURE_CACHE_EMBEDDING_MODEL", "text-embedding-3-small"),
        enable_stats=os.getenv("OPENFATTURE_CACHE_ENABLE_STATS", "true").lower() == "true",
        log_hits=os.getenv("OPENFATTURE_CACHE_LOG_HITS", "false").lower() == "true",
        log_misses=os.getenv("OPENFATTURE_CACHE_LOG_MISSES", "false").lower() == "true",
    )
