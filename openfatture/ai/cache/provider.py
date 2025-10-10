"""Cached LLM provider wrapper.

This module provides a wrapper that adds caching to any LLM provider.
"""

import hashlib
import json
from collections.abc import AsyncIterator
from typing import Any, Optional

from openfatture.ai.cache.config import CacheConfig, get_cache_config
from openfatture.ai.cache.memory import LRUCache
from openfatture.ai.cache.strategy import CacheStrategy
from openfatture.ai.domain.message import Message
from openfatture.ai.domain.response import AgentResponse
from openfatture.ai.providers.base import BaseLLMProvider
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class CachedProvider:
    """Wrapper that adds caching to any LLM provider.

    This class wraps an existing LLM provider and adds caching capabilities
    to reduce API calls and costs.

    Features:
    - Automatic cache key generation from messages
    - Configurable cache strategy (LRU by default)
    - Cache hit/miss tracking
    - Bypass option for streaming

    Example:
        >>> from openfatture.ai.providers import OpenAIProvider
        >>> from openfatture.ai.cache import CachedProvider, CacheConfig
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
    """

    def __init__(
        self,
        provider: BaseLLMProvider,
        config: Optional[CacheConfig] = None,
        cache: Optional[CacheStrategy] = None,
    ) -> None:
        """Initialize cached provider.

        Args:
            provider: Base LLM provider to wrap
            config: Cache configuration (uses defaults if None)
            cache: Custom cache strategy (creates LRU if None)
        """
        self.provider = provider
        self.config = config or get_cache_config()

        # Create cache if not provided
        if cache is None:
            if self.config.strategy == "lru":
                self._cache = LRUCache(
                    max_size=self.config.max_size,
                    default_ttl=self.config.default_ttl,
                    cleanup_interval=self.config.cleanup_interval,
                )
            else:
                # Future: Support semantic cache
                raise NotImplementedError(
                    f"Cache strategy '{self.config.strategy}' not yet implemented"
                )
        else:
            self._cache = cache

        logger.info(
            "cached_provider_initialized",
            provider=provider.provider_name,
            model=provider.model,
            strategy=self.config.strategy,
            max_size=self.config.max_size,
        )

    def _generate_cache_key(
        self,
        messages: list[Message],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """Generate cache key from request parameters.

        Args:
            messages: Conversation messages
            system_prompt: System prompt
            temperature: Generation temperature
            max_tokens: Maximum tokens
            **kwargs: Additional parameters

        Returns:
            Cache key (SHA256 hash)
        """
        # Build cache key data
        key_data = {
            "provider": self.provider.provider_name,
            "model": self.provider.model,
            "messages": [msg.to_dict() for msg in messages],
            "system_prompt": system_prompt,
            "temperature": temperature or self.provider.temperature,
            "max_tokens": max_tokens or self.provider.max_tokens,
            # Include relevant kwargs
            "kwargs": {k: v for k, v in kwargs.items() if k not in ["stream"]},
        }

        # Convert to JSON (sorted for deterministic hashing)
        key_json = json.dumps(key_data, sort_keys=True)

        # Hash to create cache key
        cache_key = hashlib.sha256(key_json.encode()).hexdigest()

        return cache_key

    async def generate(
        self,
        messages: list[Message],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        bypass_cache: bool = False,
        **kwargs: Any,
    ) -> AgentResponse:
        """Generate response with caching.

        Args:
            messages: Conversation messages
            system_prompt: System prompt
            temperature: Generation temperature
            max_tokens: Maximum tokens
            bypass_cache: Skip cache and force API call
            **kwargs: Provider-specific arguments

        Returns:
            AgentResponse
        """
        # Check if caching is enabled
        if not self.config.enabled or bypass_cache:
            logger.debug("cache_bypassed", reason="disabled or bypass_cache=True")
            return await self.provider.generate(
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

        # Generate cache key
        cache_key = self._generate_cache_key(
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        # Try to get from cache
        cached_response = await self._cache.get(cache_key)

        if cached_response is not None:
            logger.info(
                "cache_hit",
                provider=self.provider.provider_name,
                model=self.provider.model,
                cache_key=cache_key[:16],
            )
            return cached_response

        # Cache miss - call provider
        logger.debug(
            "cache_miss",
            provider=self.provider.provider_name,
            model=self.provider.model,
            cache_key=cache_key[:16],
        )

        response = await self.provider.generate(
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        # Cache the response
        await self._cache.set(cache_key, response)

        logger.debug(
            "response_cached",
            cache_key=cache_key[:16],
            tokens=response.usage.total_tokens if response.usage else 0,
        )

        return response

    async def stream(
        self,
        messages: list[Message],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream response (bypasses cache).

        Streaming responses are not cached because they are consumed
        incrementally and cannot be reliably cached.

        Args:
            messages: Conversation messages
            system_prompt: System prompt
            temperature: Generation temperature
            max_tokens: Maximum tokens
            **kwargs: Provider-specific arguments

        Yields:
            Response tokens
        """
        logger.debug("stream_bypasses_cache")

        async for chunk in self.provider.stream(
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        ):
            yield chunk

    def count_tokens(self, text: str) -> int:
        """Count tokens (delegates to provider)."""
        return self.provider.count_tokens(text)

    def estimate_cost(self, usage: Any) -> float:
        """Estimate cost (delegates to provider)."""
        return self.provider.estimate_cost(usage)

    async def health_check(self) -> bool:
        """Health check (delegates to provider)."""
        return await self.provider.health_check()

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return f"cached_{self.provider.provider_name}"

    @property
    def supports_streaming(self) -> bool:
        """Check if provider supports streaming."""
        return self.provider.supports_streaming

    @property
    def supports_tools(self) -> bool:
        """Check if provider supports tools."""
        return self.provider.supports_tools

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        stats = self._cache.get_stats()

        # Add savings estimation
        if stats["total_requests"] > 0:
            # Assume average cost per request
            avg_cost_per_request = 0.01  # $0.01 per request (rough estimate)
            estimated_savings = stats["hits"] * avg_cost_per_request

            stats["estimated_savings_usd"] = estimated_savings

        return stats

    async def clear_cache(self) -> None:
        """Clear all cached responses."""
        await self._cache.clear()
        logger.info("cache_cleared")

    async def shutdown(self) -> None:
        """Shutdown cache and cleanup resources."""
        if hasattr(self._cache, "shutdown"):
            await self._cache.shutdown()
        logger.info("cached_provider_shutdown")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"CachedProvider("
            f"provider={self.provider.provider_name}, "
            f"cache={self._cache})"
        )
