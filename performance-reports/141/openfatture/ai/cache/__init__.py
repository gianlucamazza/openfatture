"""OpenFatture AI Caching System.

This module provides caching strategies for LLM responses to reduce API costs
and improve response times.

Example Usage:
    >>> from openfatture.ai.cache import CachedProvider, CacheConfig
    >>> from openfatture.ai.providers import OpenAIProvider
    >>>
    >>> # Create base provider
    >>> provider = OpenAIProvider(api_key="sk-...")
    >>>
    >>> # Wrap with caching
    >>> config = CacheConfig(max_size=1000, default_ttl=3600)
    >>> cached_provider = CachedProvider(provider, config)
    >>>
    >>> # Use as normal - caching is automatic
    >>> response = await cached_provider.generate(messages)
    >>>
    >>> # Get cache statistics
    >>> stats = cached_provider.get_cache_stats()
    >>> print(f"Hit rate: {stats['hit_rate']:.2%}")
    >>> print(f"Savings: ${stats['estimated_savings_usd']:.2f}")
"""

from openfatture.ai.cache.config import (
    DEFAULT_CACHE_CONFIG,
    CacheConfig,
    get_cache_config,
)
from openfatture.ai.cache.memory import LRUCache
from openfatture.ai.cache.provider import CachedProvider
from openfatture.ai.cache.strategy import CacheEntry, CacheStrategy
from openfatture.ai.cache.tool_cache import ToolResultCache, get_tool_cache

__all__ = [
    # Strategy
    "CacheStrategy",
    "CacheEntry",
    # Implementations
    "LRUCache",
    "CachedProvider",
    "ToolResultCache",
    "get_tool_cache",
    # Configuration
    "CacheConfig",
    "DEFAULT_CACHE_CONFIG",
    "get_cache_config",
]
