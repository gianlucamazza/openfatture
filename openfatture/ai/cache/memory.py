"""In-memory cache implementations.

This module provides memory-based caching strategies including LRU cache
with TTL support.
"""

import asyncio
from collections import OrderedDict
from datetime import datetime
from typing import Any, Optional, TypeVar

from openfatture.ai.cache.strategy import CacheEntry, CacheStrategy
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class LRUCache(CacheStrategy[T]):
    """Least Recently Used (LRU) cache with TTL support.

    Features:
    - LRU eviction policy when max_size is reached
    - Optional TTL (time-to-live) per entry
    - Automatic cleanup of expired entries
    - Thread-safe operations
    - Hit/miss statistics tracking

    Example:
        >>> cache = LRUCache(max_size=100, default_ttl=3600)
        >>> await cache.set("key1", "value1")
        >>> value = await cache.get("key1")
        >>> stats = cache.get_stats()
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: Optional[int] = 3600,
        cleanup_interval: int = 300,
    ) -> None:
        """Initialize LRU cache.

        Args:
            max_size: Maximum number of entries (default: 1000)
            default_ttl: Default TTL in seconds (default: 3600, None = no expiration)
            cleanup_interval: Interval for automatic cleanup in seconds (default: 300)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval

        # OrderedDict maintains insertion order and provides O(1) move_to_end
        self._cache: OrderedDict[str, CacheEntry[T]] = OrderedDict()

        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0

        # Lock for thread safety
        self._lock = asyncio.Lock()

        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()

    def _start_cleanup_task(self) -> None:
        """Start background cleanup task."""
        if self.cleanup_interval > 0:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

    async def _periodic_cleanup(self) -> None:
        """Periodically clean up expired entries."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                removed = await self.cleanup()
                if removed > 0:
                    logger.debug(
                        "cache_cleanup",
                        removed=removed,
                        size=self.size(),
                    )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("cache_cleanup_error", error=str(e))

    async def get(self, key: str) -> Optional[T]:
        """Retrieve value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found and not expired, None otherwise
        """
        async with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._misses += 1
                logger.debug("cache_miss", key=key)
                return None

            # Check expiration
            if entry.is_expired():
                self._cache.pop(key)
                self._misses += 1
                logger.debug("cache_expired", key=key)
                return None

            # Update access metadata
            entry.touch()

            # Move to end (most recently used)
            self._cache.move_to_end(key)

            self._hits += 1
            logger.debug(
                "cache_hit",
                key=key,
                access_count=entry.access_count,
            )

            return entry.value

    async def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """Store value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = use default)
        """
        async with self._lock:
            # Check if we need to evict
            if key not in self._cache and len(self._cache) >= self.max_size:
                # Evict least recently used (first item)
                evicted_key, _ = self._cache.popitem(last=False)
                self._evictions += 1
                logger.debug("cache_eviction", evicted_key=evicted_key)

            # Create entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                accessed_at=datetime.now(),
                access_count=0,
                ttl_seconds=ttl if ttl is not None else self.default_ttl,
            )

            # Store and move to end (most recently used)
            self._cache[key] = entry
            self._cache.move_to_end(key)

            logger.debug(
                "cache_set",
                key=key,
                ttl=entry.ttl_seconds,
                size=self.size(),
            )

    async def delete(self, key: str) -> bool:
        """Remove value from cache.

        Args:
            key: Cache key

        Returns:
            True if key was found and deleted, False otherwise
        """
        async with self._lock:
            if key in self._cache:
                self._cache.pop(key)
                logger.debug("cache_delete", key=key)
                return True
            return False

    async def clear(self) -> None:
        """Clear all entries from cache."""
        async with self._lock:
            size = len(self._cache)
            self._cache.clear()
            logger.info("cache_cleared", entries_removed=size)

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists and is not expired, False otherwise
        """
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False

            if entry.is_expired():
                self._cache.pop(key)
                return False

            return True

    def size(self) -> int:
        """Get number of entries in cache.

        Returns:
            Number of cache entries
        """
        return len(self._cache)

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0

        return {
            "size": self.size(),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "default_ttl": self.default_ttl,
        }

    async def cleanup(self) -> int:
        """Remove expired entries.

        Returns:
            Number of entries removed
        """
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items() if entry.is_expired()
            ]

            for key in expired_keys:
                self._cache.pop(key)

            if expired_keys:
                logger.debug("cache_cleanup_completed", removed=len(expired_keys))

            return len(expired_keys)

    async def shutdown(self) -> None:
        """Shutdown cache and cleanup resources."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        await self.clear()
        logger.info("cache_shutdown_completed")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"LRUCache(size={self.size()}/{self.max_size}, "
            f"hit_rate={self.get_stats()['hit_rate']:.2%})"
        )
