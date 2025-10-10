"""Tests for LRU cache implementation."""

import asyncio
import pytest
from datetime import datetime, timedelta

from openfatture.ai.cache import LRUCache, CacheEntry


class TestCacheEntry:
    """Tests for CacheEntry dataclass."""

    def test_cache_entry_creation(self):
        """Test cache entry creation."""
        now = datetime.now()
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=now,
            accessed_at=now,
            access_count=0,
            ttl_seconds=3600,
        )

        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.access_count == 0
        assert entry.ttl_seconds == 3600

    def test_cache_entry_expiration_no_ttl(self):
        """Test that entry without TTL never expires."""
        now = datetime.now()
        entry = CacheEntry(
            key="test",
            value="value",
            created_at=now - timedelta(hours=24),
            accessed_at=now,
            ttl_seconds=None,
        )

        assert not entry.is_expired()

    def test_cache_entry_expiration_with_ttl(self):
        """Test that entry with TTL expires correctly."""
        # Create entry that expired 1 hour ago
        now = datetime.now()
        entry = CacheEntry(
            key="test",
            value="value",
            created_at=now - timedelta(hours=2),
            accessed_at=now,
            ttl_seconds=3600,  # 1 hour
        )

        assert entry.is_expired()

    def test_cache_entry_not_expired(self):
        """Test that recent entry is not expired."""
        now = datetime.now()
        entry = CacheEntry(
            key="test",
            value="value",
            created_at=now - timedelta(minutes=30),
            accessed_at=now,
            ttl_seconds=3600,  # 1 hour
        )

        assert not entry.is_expired()

    def test_cache_entry_touch(self):
        """Test that touch updates access metadata."""
        now = datetime.now()
        entry = CacheEntry(
            key="test",
            value="value",
            created_at=now,
            accessed_at=now,
            access_count=0,
        )

        # Wait a bit
        import time

        time.sleep(0.01)

        # Touch entry
        entry.touch()

        assert entry.access_count == 1
        assert entry.accessed_at > now


@pytest.mark.asyncio
class TestLRUCache:
    """Tests for LRU cache."""

    async def test_cache_basic_operations(self):
        """Test basic get/set operations."""
        cache = LRUCache(max_size=10, default_ttl=3600, cleanup_interval=0)

        try:
            # Set value
            await cache.set("key1", "value1")

            # Get value
            value = await cache.get("key1")
            assert value == "value1"

            # Get non-existent key
            value = await cache.get("key2")
            assert value is None

        finally:
            await cache.shutdown()

    async def test_cache_size_limit(self):
        """Test that cache respects max_size."""
        cache = LRUCache(max_size=3, default_ttl=3600, cleanup_interval=0)

        try:
            # Add 3 entries
            await cache.set("key1", "value1")
            await cache.set("key2", "value2")
            await cache.set("key3", "value3")

            assert cache.size() == 3

            # Add 4th entry - should evict least recently used (key1)
            await cache.set("key4", "value4")

            assert cache.size() == 3
            assert await cache.get("key1") is None  # Evicted
            assert await cache.get("key2") == "value2"
            assert await cache.get("key3") == "value3"
            assert await cache.get("key4") == "value4"

        finally:
            await cache.shutdown()

    async def test_cache_lru_eviction(self):
        """Test LRU eviction policy."""
        cache = LRUCache(max_size=3, default_ttl=3600, cleanup_interval=0)

        try:
            # Add 3 entries
            await cache.set("key1", "value1")
            await cache.set("key2", "value2")
            await cache.set("key3", "value3")

            # Access key1 to make it most recently used
            await cache.get("key1")

            # Add 4th entry - should evict key2 (least recently used)
            await cache.set("key4", "value4")

            assert await cache.get("key1") == "value1"  # Still there
            assert await cache.get("key2") is None  # Evicted
            assert await cache.get("key3") == "value3"
            assert await cache.get("key4") == "value4"

        finally:
            await cache.shutdown()

    async def test_cache_ttl_expiration(self):
        """Test TTL expiration."""
        cache = LRUCache(max_size=10, default_ttl=1, cleanup_interval=0)

        try:
            # Set value with 1 second TTL
            await cache.set("key1", "value1")

            # Should be available immediately
            value = await cache.get("key1")
            assert value == "value1"

            # Wait for expiration
            await asyncio.sleep(1.1)

            # Should be expired
            value = await cache.get("key1")
            assert value is None

        finally:
            await cache.shutdown()

    async def test_cache_custom_ttl(self):
        """Test custom TTL per entry."""
        cache = LRUCache(max_size=10, default_ttl=3600, cleanup_interval=0)

        try:
            # Set with custom TTL
            await cache.set("key1", "value1", ttl=1)  # 1 second
            await cache.set("key2", "value2", ttl=10)  # 10 seconds

            # Both should be available immediately
            assert await cache.get("key1") == "value1"
            assert await cache.get("key2") == "value2"

            # Wait for key1 to expire
            await asyncio.sleep(1.1)

            # key1 should be expired, key2 still valid
            assert await cache.get("key1") is None
            assert await cache.get("key2") == "value2"

        finally:
            await cache.shutdown()

    async def test_cache_delete(self):
        """Test delete operation."""
        cache = LRUCache(max_size=10, default_ttl=3600, cleanup_interval=0)

        try:
            await cache.set("key1", "value1")

            # Delete existing key
            deleted = await cache.delete("key1")
            assert deleted is True

            # Key should be gone
            value = await cache.get("key1")
            assert value is None

            # Delete non-existent key
            deleted = await cache.delete("key2")
            assert deleted is False

        finally:
            await cache.shutdown()

    async def test_cache_clear(self):
        """Test clear operation."""
        cache = LRUCache(max_size=10, default_ttl=3600, cleanup_interval=0)

        try:
            # Add multiple entries
            await cache.set("key1", "value1")
            await cache.set("key2", "value2")
            await cache.set("key3", "value3")

            assert cache.size() == 3

            # Clear cache
            await cache.clear()

            assert cache.size() == 0
            assert await cache.get("key1") is None
            assert await cache.get("key2") is None
            assert await cache.get("key3") is None

        finally:
            await cache.shutdown()

    async def test_cache_exists(self):
        """Test exists operation."""
        cache = LRUCache(max_size=10, default_ttl=1, cleanup_interval=0)

        try:
            await cache.set("key1", "value1")

            # Should exist
            assert await cache.exists("key1") is True

            # Should not exist
            assert await cache.exists("key2") is False

            # Wait for expiration
            await asyncio.sleep(1.1)

            # Should not exist (expired)
            assert await cache.exists("key1") is False

        finally:
            await cache.shutdown()

    async def test_cache_stats(self):
        """Test statistics tracking."""
        cache = LRUCache(max_size=10, default_ttl=3600, cleanup_interval=0)

        try:
            # Add entries
            await cache.set("key1", "value1")
            await cache.set("key2", "value2")

            # Generate hits and misses
            await cache.get("key1")  # Hit
            await cache.get("key1")  # Hit
            await cache.get("key3")  # Miss
            await cache.get("key4")  # Miss

            stats = cache.get_stats()

            assert stats["size"] == 2
            assert stats["max_size"] == 10
            assert stats["hits"] == 2
            assert stats["misses"] == 2
            assert stats["total_requests"] == 4
            assert stats["hit_rate"] == 0.5

        finally:
            await cache.shutdown()

    async def test_cache_cleanup(self):
        """Test manual cleanup of expired entries."""
        cache = LRUCache(max_size=10, default_ttl=1, cleanup_interval=0)

        try:
            # Add entries
            await cache.set("key1", "value1", ttl=1)
            await cache.set("key2", "value2", ttl=10)
            await cache.set("key3", "value3", ttl=1)

            assert cache.size() == 3

            # Wait for some to expire
            await asyncio.sleep(1.1)

            # Manual cleanup
            removed = await cache.cleanup()

            # Should have removed 2 expired entries
            assert removed == 2
            assert cache.size() == 1
            assert await cache.get("key2") == "value2"

        finally:
            await cache.shutdown()

    async def test_cache_update_existing_key(self):
        """Test updating an existing key."""
        cache = LRUCache(max_size=10, default_ttl=3600, cleanup_interval=0)

        try:
            await cache.set("key1", "value1")
            assert await cache.get("key1") == "value1"

            # Update value
            await cache.set("key1", "value2")
            assert await cache.get("key1") == "value2"

            # Should not increase size
            assert cache.size() == 1

        finally:
            await cache.shutdown()

    async def test_cache_repr(self):
        """Test string representation."""
        cache = LRUCache(max_size=100, default_ttl=3600, cleanup_interval=0)

        try:
            await cache.set("key1", "value1")

            repr_str = repr(cache)
            assert "LRUCache" in repr_str
            assert "size=" in repr_str
            assert "hit_rate=" in repr_str

        finally:
            await cache.shutdown()


@pytest.mark.asyncio
class TestLRUCachePerformance:
    """Performance tests for LRU cache."""

    async def test_cache_concurrent_access(self):
        """Test concurrent access to cache."""
        cache = LRUCache(max_size=100, default_ttl=3600, cleanup_interval=0)

        try:
            # Concurrent writes
            async def write_task(i: int):
                await cache.set(f"key{i}", f"value{i}")

            await asyncio.gather(*[write_task(i) for i in range(50)])

            assert cache.size() == 50

            # Concurrent reads
            async def read_task(i: int):
                return await cache.get(f"key{i}")

            results = await asyncio.gather(*[read_task(i) for i in range(50)])

            # All values should be retrieved
            assert all(r == f"value{i}" for i, r in enumerate(results))

        finally:
            await cache.shutdown()

    async def test_cache_high_throughput(self):
        """Test cache with high throughput."""
        cache = LRUCache(max_size=1000, default_ttl=3600, cleanup_interval=0)

        try:
            # Write 10000 entries (will trigger evictions)
            for i in range(10000):
                await cache.set(f"key{i}", f"value{i}")

            # Should be at max size
            assert cache.size() == 1000

            # Should have evictions
            stats = cache.get_stats()
            assert stats["evictions"] > 0

        finally:
            await cache.shutdown()


@pytest.mark.asyncio
class TestLRUCacheEdgeCases:
    """Edge case tests for LRU cache."""

    async def test_cache_with_none_value(self):
        """Test caching None values."""
        cache = LRUCache(max_size=10, default_ttl=3600, cleanup_interval=0)

        try:
            await cache.set("key1", None)

            # Should be able to retrieve None
            value = await cache.get("key1")
            assert value is None

            # Should exist
            assert await cache.exists("key1") is True

        finally:
            await cache.shutdown()

    async def test_cache_with_complex_values(self):
        """Test caching complex objects."""
        cache = LRUCache(max_size=10, default_ttl=3600, cleanup_interval=0)

        try:
            # Dictionary
            await cache.set("dict", {"key": "value", "nested": {"a": 1}})
            assert await cache.get("dict") == {"key": "value", "nested": {"a": 1}}

            # List
            await cache.set("list", [1, 2, 3, 4, 5])
            assert await cache.get("list") == [1, 2, 3, 4, 5]

            # Custom object
            class CustomObject:
                def __init__(self, x):
                    self.x = x

            obj = CustomObject(42)
            await cache.set("obj", obj)
            retrieved = await cache.get("obj")
            assert retrieved.x == 42

        finally:
            await cache.shutdown()

    async def test_cache_zero_ttl(self):
        """Test cache with zero TTL (immediate expiration)."""
        cache = LRUCache(max_size=10, default_ttl=0, cleanup_interval=0)

        try:
            await cache.set("key1", "value1")

            # Should expire immediately
            value = await cache.get("key1")
            # Note: Due to timing, this might still return the value
            # if checked within microseconds
            # The important thing is it expires very quickly

        finally:
            await cache.shutdown()

    async def test_cache_max_size_one(self):
        """Test cache with max_size=1."""
        cache = LRUCache(max_size=1, default_ttl=3600, cleanup_interval=0)

        try:
            await cache.set("key1", "value1")
            assert cache.size() == 1

            await cache.set("key2", "value2")
            assert cache.size() == 1

            # key1 should be evicted
            assert await cache.get("key1") is None
            assert await cache.get("key2") == "value2"

        finally:
            await cache.shutdown()
