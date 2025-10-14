"""Tool result caching for read operations.

This module provides caching for tool execution results to improve performance
and reduce database load for read-heavy operations.
"""

import hashlib
import json
from collections.abc import Awaitable, Callable
from typing import Any

from openfatture.ai.cache.memory import LRUCache
from openfatture.ai.tools.models import ToolResult
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class ToolResultCache:
    """
    Cache for tool execution results.

    Provides caching for read operations to improve performance and reduce
    database load. Uses LRU eviction policy with configurable TTL.

    Features:
    - Automatic cache key generation from tool parameters
    - TTL-based expiration
    - Cache statistics and monitoring
    - Selective caching (only for read operations)
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 300,  # 5 minutes
    ):
        """
        Initialize tool result cache.

        Args:
            max_size: Maximum number of cached results
            default_ttl: Default TTL in seconds for cached results
        """
        self.cache: LRUCache[ToolResult] = LRUCache(max_size=max_size, default_ttl=default_ttl)
        self.read_operations = {
            # Invoice tools
            "search_invoices",
            "get_invoice_details",
            "get_invoice_stats",
            # Client tools
            "search_clients",
            "get_client_details",
            "get_client_stats",
            # Knowledge tools
            "search_knowledge",
            "get_knowledge_details",
        }

        logger.info(
            "tool_cache_initialized",
            max_size=max_size,
            default_ttl=default_ttl,
            read_operations=len(self.read_operations),
        )

    def _generate_cache_key(self, tool_name: str, parameters: dict[str, Any]) -> str:
        """
        Generate a deterministic cache key from tool name and parameters.

        Args:
            tool_name: Name of the tool
            parameters: Tool parameters

        Returns:
            Cache key string
        """
        # Sort parameters for consistent key generation
        sorted_params = {k: parameters[k] for k in sorted(parameters.keys())}

        # Create hash of tool_name + parameters
        key_data = {
            "tool": tool_name,
            "params": sorted_params,
        }

        key_json = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.sha256(key_json.encode()).hexdigest()[:16]  # Short hash

        return f"tool:{tool_name}:{key_hash}"

    def is_cacheable(self, tool_name: str) -> bool:
        """
        Check if a tool operation should be cached.

        Args:
            tool_name: Name of the tool

        Returns:
            True if the operation should be cached
        """
        return tool_name in self.read_operations

    async def get_cached_result(
        self,
        tool_name: str,
        parameters: dict[str, Any],
    ) -> ToolResult | None:
        """
        Get cached result for a tool execution.

        Args:
            tool_name: Name of the tool
            parameters: Tool parameters

        Returns:
            Cached ToolResult if available, None otherwise
        """
        if not self.is_cacheable(tool_name):
            return None

        cache_key = self._generate_cache_key(tool_name, parameters)
        cached_result = await self.cache.get(cache_key)

        if cached_result:
            # Mark as cache hit in the result
            cached_result.cache_hit = True
            cached_result.cache_key = cache_key

            logger.debug(
                "tool_cache_hit",
                tool_name=tool_name,
                cache_key=cache_key,
            )

            return cached_result

        return None

    async def cache_result(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        result: ToolResult,
        ttl: int | None = None,
    ) -> None:
        """
        Cache a tool execution result.

        Args:
            tool_name: Name of the tool
            parameters: Tool parameters
            result: ToolResult to cache
            ttl: Time-to-live in seconds (None = use default)
        """
        if not self.is_cacheable(tool_name) or not result.success:
            return

        cache_key = self._generate_cache_key(tool_name, parameters)

        # Create a copy of the result for caching
        cached_result = ToolResult(
            success=result.success,
            data=result.data,
            error=result.error,
            error_type=result.error_type,
            tool_name=result.tool_name,
            metadata=result.metadata.copy(),
            execution_time=result.execution_time,
            retries=result.retries,
            cache_hit=False,  # Will be set to True when retrieved
            cache_key=cache_key,
        )

        await self.cache.set(cache_key, cached_result, ttl=ttl)

        logger.debug(
            "tool_cache_set",
            tool_name=tool_name,
            cache_key=cache_key,
            ttl=ttl,
        )

    async def invalidate_tool_cache(self, tool_name: str) -> int:
        """
        Invalidate all cached results for a specific tool.

        Useful when data has been modified and cache needs to be cleared.

        Args:
            tool_name: Name of the tool to invalidate

        Returns:
            Number of entries invalidated
        """
        # This is a simplified implementation - in a real system,
        # we'd need to track which keys belong to which tools
        # For now, we'll clear the entire cache when any write operation occurs
        stats_before = self.cache.get_stats()
        await self.cache.clear()

        invalidated = stats_before["size"]
        logger.info(
            "tool_cache_invalidated",
            tool_name=tool_name,
            entries_invalidated=invalidated,
        )

        return invalidated

    async def get_or_execute(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        execute_func: Callable[[], Awaitable[ToolResult]],
    ) -> ToolResult:
        """
        Get cached result or execute the tool function.

        Args:
            tool_name: Name of the tool
            parameters: Tool parameters
            execute_func: Function to execute if not cached

        Returns:
            ToolResult (cached or freshly executed)
        """
        # Try to get from cache first
        cached_result = await self.get_cached_result(tool_name, parameters)
        if cached_result:
            return cached_result

        # Execute the function
        result = await execute_func()

        # Cache successful results
        if result.success:
            await self.cache_result(tool_name, parameters, result)

        return result

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        cache_stats = self.cache.get_stats()
        return {
            **cache_stats,
            "cacheable_operations": len(self.read_operations),
        }

    async def clear(self) -> None:
        """Clear all cached results."""
        await self.cache.clear()
        logger.info("tool_cache_cleared")

    async def cleanup(self) -> int:
        """
        Remove expired entries.

        Returns:
            Number of entries removed
        """
        return await self.cache.cleanup()


# Global cache instance
_tool_cache: ToolResultCache | None = None


def get_tool_cache() -> ToolResultCache:
    """
    Get the global tool result cache instance.

    Returns:
        Global ToolResultCache instance
    """
    global _tool_cache

    if _tool_cache is None:
        _tool_cache = ToolResultCache()

    return _tool_cache
