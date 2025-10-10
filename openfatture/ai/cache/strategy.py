"""Cache strategy interface and base implementations.

This module defines the abstract base class for all caching strategies
used in the OpenFatture AI system.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, TypeVar, Generic
from dataclasses import dataclass
from datetime import datetime

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """Represents a cached entry with metadata.

    Attributes:
        key: Cache key
        value: Cached value
        created_at: Timestamp when entry was created
        accessed_at: Timestamp when entry was last accessed
        access_count: Number of times entry was accessed
        ttl_seconds: Time-to-live in seconds (None = no expiration)
    """

    key: str
    value: T
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    ttl_seconds: Optional[int] = None

    def is_expired(self) -> bool:
        """Check if entry has expired based on TTL.

        Returns:
            True if entry is expired, False otherwise
        """
        if self.ttl_seconds is None:
            return False

        age = (datetime.now() - self.created_at).total_seconds()
        return age > self.ttl_seconds

    def touch(self) -> None:
        """Update access metadata."""
        self.accessed_at = datetime.now()
        self.access_count += 1


class CacheStrategy(ABC, Generic[T]):
    """Abstract base class for cache strategies.

    All cache implementations must inherit from this class and implement
    the required methods.
    """

    @abstractmethod
    async def get(self, key: str) -> Optional[T]:
        """Retrieve value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found and not expired, None otherwise
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """Store value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = use default)
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Remove value from cache.

        Args:
            key: Cache key

        Returns:
            True if key was found and deleted, False otherwise
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all entries from cache."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists and is not expired, False otherwise
        """
        pass

    @abstractmethod
    def size(self) -> int:
        """Get number of entries in cache.

        Returns:
            Number of cache entries
        """
        pass

    @abstractmethod
    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats (hits, misses, size, etc.)
        """
        pass

    @abstractmethod
    async def cleanup(self) -> int:
        """Remove expired entries.

        Returns:
            Number of entries removed
        """
        pass
