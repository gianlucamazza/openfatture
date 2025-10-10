"""Tests for CachedProvider wrapper."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from openfatture.ai.cache import CachedProvider, CacheConfig, LRUCache
from openfatture.ai.domain.message import Message, Role
from openfatture.ai.domain.response import AgentResponse, ResponseStatus, UsageMetrics
from openfatture.ai.providers.base import BaseLLMProvider


@pytest.fixture
def mock_provider():
    """Create a mock LLM provider."""
    provider = MagicMock(spec=BaseLLMProvider)
    provider.provider_name = "mock"
    provider.model = "mock-1"
    provider.temperature = 0.7
    provider.max_tokens = 2000

    # Mock generate method
    async def mock_generate(messages, **kwargs):
        return AgentResponse(
            content="This is a mock response",
            status=ResponseStatus.SUCCESS,
            model="mock-1",
            provider="mock",
            usage=UsageMetrics(
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15,
                estimated_cost_usd=0.001,
            ),
            latency_ms=100.0,
        )

    provider.generate = AsyncMock(side_effect=mock_generate)

    # Mock stream method
    async def mock_stream(messages, **kwargs):
        chunks = ["This ", "is ", "a ", "stream"]
        for chunk in chunks:
            yield chunk

    provider.stream = mock_stream

    # Mock other methods
    provider.count_tokens = MagicMock(return_value=10)
    provider.estimate_cost = MagicMock(return_value=0.001)
    provider.health_check = AsyncMock(return_value=True)
    provider.supports_streaming = True
    provider.supports_tools = True

    return provider


@pytest.mark.asyncio
class TestCachedProvider:
    """Tests for CachedProvider."""

    async def test_cached_provider_initialization(self, mock_provider):
        """Test cached provider initialization."""
        config = CacheConfig(max_size=100, default_ttl=3600)
        cached = CachedProvider(mock_provider, config)

        assert cached.provider == mock_provider
        assert cached.config == config
        assert isinstance(cached._cache, LRUCache)

        await cached.shutdown()

    async def test_cached_provider_with_default_config(self, mock_provider):
        """Test initialization with default config."""
        cached = CachedProvider(mock_provider)

        assert cached.config is not None
        assert cached.config.enabled is True

        await cached.shutdown()

    async def test_cache_hit_on_duplicate_request(self, mock_provider):
        """Test that duplicate requests hit cache."""
        config = CacheConfig(max_size=100, default_ttl=3600)
        cached = CachedProvider(mock_provider, config)

        try:
            messages = [Message(role=Role.USER, content="Hello")]

            # First request - should call provider
            response1 = await cached.generate(messages)
            assert response1.content == "This is a mock response"
            assert mock_provider.generate.call_count == 1

            # Second identical request - should hit cache
            response2 = await cached.generate(messages)
            assert response2.content == "This is a mock response"
            assert mock_provider.generate.call_count == 1  # No additional call

            # Responses should be identical
            assert response1 == response2

        finally:
            await cached.shutdown()

    async def test_cache_miss_on_different_messages(self, mock_provider):
        """Test that different messages don't hit cache."""
        config = CacheConfig(max_size=100, default_ttl=3600)
        cached = CachedProvider(mock_provider, config)

        try:
            messages1 = [Message(role=Role.USER, content="Hello")]
            messages2 = [Message(role=Role.USER, content="Goodbye")]

            # First request
            await cached.generate(messages1)
            assert mock_provider.generate.call_count == 1

            # Different request - should miss cache
            await cached.generate(messages2)
            assert mock_provider.generate.call_count == 2

        finally:
            await cached.shutdown()

    async def test_cache_miss_on_different_temperature(self, mock_provider):
        """Test that different temperature creates different cache key."""
        config = CacheConfig(max_size=100, default_ttl=3600)
        cached = CachedProvider(mock_provider, config)

        try:
            messages = [Message(role=Role.USER, content="Hello")]

            # Request with temperature 0.7
            await cached.generate(messages, temperature=0.7)
            assert mock_provider.generate.call_count == 1

            # Same message but different temperature - should miss cache
            await cached.generate(messages, temperature=0.9)
            assert mock_provider.generate.call_count == 2

        finally:
            await cached.shutdown()

    async def test_bypass_cache_flag(self, mock_provider):
        """Test bypass_cache flag skips cache."""
        config = CacheConfig(max_size=100, default_ttl=3600)
        cached = CachedProvider(mock_provider, config)

        try:
            messages = [Message(role=Role.USER, content="Hello")]

            # First request
            await cached.generate(messages)
            assert mock_provider.generate.call_count == 1

            # Same request with bypass_cache=True
            await cached.generate(messages, bypass_cache=True)
            assert mock_provider.generate.call_count == 2  # Called again

        finally:
            await cached.shutdown()

    async def test_cache_disabled_in_config(self, mock_provider):
        """Test that cache can be disabled via config."""
        config = CacheConfig(enabled=False)
        cached = CachedProvider(mock_provider, config)

        try:
            messages = [Message(role=Role.USER, content="Hello")]

            # Multiple identical requests
            await cached.generate(messages)
            await cached.generate(messages)

            # Should call provider both times (cache disabled)
            assert mock_provider.generate.call_count == 2

        finally:
            await cached.shutdown()

    async def test_stream_bypasses_cache(self, mock_provider):
        """Test that streaming always bypasses cache."""
        config = CacheConfig(max_size=100, default_ttl=3600)
        cached = CachedProvider(mock_provider, config)

        try:
            messages = [Message(role=Role.USER, content="Hello")]

            # Stream response
            chunks = []
            async for chunk in cached.stream(messages):
                chunks.append(chunk)

            assert chunks == ["This ", "is ", "a ", "stream"]

            # Cache should still be empty
            stats = cached.get_cache_stats()
            assert stats["size"] == 0

        finally:
            await cached.shutdown()

    async def test_cache_stats(self, mock_provider):
        """Test cache statistics."""
        config = CacheConfig(max_size=100, default_ttl=3600)
        cached = CachedProvider(mock_provider, config)

        try:
            messages = [Message(role=Role.USER, content="Hello")]

            # Generate some cache activity
            await cached.generate(messages)  # Miss
            await cached.generate(messages)  # Hit
            await cached.generate(messages)  # Hit

            stats = cached.get_cache_stats()

            assert stats["size"] == 1
            assert stats["hits"] == 2
            assert stats["misses"] == 1
            assert stats["hit_rate"] == 2 / 3
            assert "estimated_savings_usd" in stats

        finally:
            await cached.shutdown()

    async def test_clear_cache(self, mock_provider):
        """Test cache clearing."""
        config = CacheConfig(max_size=100, default_ttl=3600)
        cached = CachedProvider(mock_provider, config)

        try:
            messages = [Message(role=Role.USER, content="Hello")]

            # Add to cache
            await cached.generate(messages)
            stats = cached.get_cache_stats()
            assert stats["size"] == 1

            # Clear cache
            await cached.clear_cache()
            stats = cached.get_cache_stats()
            assert stats["size"] == 0

            # Next request should miss cache
            await cached.generate(messages)
            assert mock_provider.generate.call_count == 2

        finally:
            await cached.shutdown()

    async def test_count_tokens_delegates(self, mock_provider):
        """Test that count_tokens delegates to provider."""
        cached = CachedProvider(mock_provider)

        try:
            count = cached.count_tokens("Hello world")
            assert count == 10
            mock_provider.count_tokens.assert_called_once_with("Hello world")

        finally:
            await cached.shutdown()

    async def test_estimate_cost_delegates(self, mock_provider):
        """Test that estimate_cost delegates to provider."""
        cached = CachedProvider(mock_provider)

        try:
            usage = UsageMetrics(
                prompt_tokens=10, completion_tokens=5, total_tokens=15
            )
            cost = cached.estimate_cost(usage)
            assert cost == 0.001
            mock_provider.estimate_cost.assert_called_once_with(usage)

        finally:
            await cached.shutdown()

    async def test_health_check_delegates(self, mock_provider):
        """Test that health_check delegates to provider."""
        cached = CachedProvider(mock_provider)

        try:
            healthy = await cached.health_check()
            assert healthy is True
            mock_provider.health_check.assert_called_once()

        finally:
            await cached.shutdown()

    async def test_provider_name_property(self, mock_provider):
        """Test provider name includes 'cached' prefix."""
        cached = CachedProvider(mock_provider)

        try:
            assert cached.provider_name == "cached_mock"

        finally:
            await cached.shutdown()

    async def test_supports_streaming_property(self, mock_provider):
        """Test supports_streaming delegates to provider."""
        cached = CachedProvider(mock_provider)

        try:
            assert cached.supports_streaming is True

        finally:
            await cached.shutdown()

    async def test_supports_tools_property(self, mock_provider):
        """Test supports_tools delegates to provider."""
        cached = CachedProvider(mock_provider)

        try:
            assert cached.supports_tools is True

        finally:
            await cached.shutdown()

    async def test_cache_key_generation_deterministic(self, mock_provider):
        """Test that cache key generation is deterministic."""
        cached = CachedProvider(mock_provider)

        try:
            messages = [Message(role=Role.USER, content="Hello")]

            key1 = cached._generate_cache_key(messages, temperature=0.7)
            key2 = cached._generate_cache_key(messages, temperature=0.7)

            # Same inputs should produce same key
            assert key1 == key2

            # Different inputs should produce different key
            key3 = cached._generate_cache_key(messages, temperature=0.9)
            assert key1 != key3

        finally:
            await cached.shutdown()

    async def test_repr(self, mock_provider):
        """Test string representation."""
        cached = CachedProvider(mock_provider)

        try:
            repr_str = repr(cached)
            assert "CachedProvider" in repr_str
            assert "mock" in repr_str

        finally:
            await cached.shutdown()


@pytest.mark.asyncio
class TestCachedProviderIntegration:
    """Integration tests for CachedProvider."""

    async def test_multiple_messages_caching(self, mock_provider):
        """Test caching with multiple messages in conversation."""
        config = CacheConfig(max_size=100, default_ttl=3600)
        cached = CachedProvider(mock_provider, config)

        try:
            messages = [
                Message(role=Role.USER, content="Hello"),
                Message(role=Role.ASSISTANT, content="Hi there"),
                Message(role=Role.USER, content="How are you?"),
            ]

            # First request
            await cached.generate(messages)
            assert mock_provider.generate.call_count == 1

            # Same conversation - should hit cache
            await cached.generate(messages)
            assert mock_provider.generate.call_count == 1

        finally:
            await cached.shutdown()

    async def test_system_prompt_affects_cache_key(self, mock_provider):
        """Test that system prompt affects cache key."""
        config = CacheConfig(max_size=100, default_ttl=3600)
        cached = CachedProvider(mock_provider, config)

        try:
            messages = [Message(role=Role.USER, content="Hello")]

            # Request with system prompt
            await cached.generate(messages, system_prompt="You are helpful")
            assert mock_provider.generate.call_count == 1

            # Same message, different system prompt - should miss cache
            await cached.generate(messages, system_prompt="You are concise")
            assert mock_provider.generate.call_count == 2

            # Same message and system prompt - should hit cache
            await cached.generate(messages, system_prompt="You are helpful")
            assert mock_provider.generate.call_count == 2  # No additional call

        finally:
            await cached.shutdown()

    async def test_high_volume_caching(self, mock_provider):
        """Test caching with high volume of requests."""
        config = CacheConfig(max_size=50, default_ttl=3600)
        cached = CachedProvider(mock_provider, config)

        try:
            # Generate 100 requests with 50 unique messages
            for i in range(100):
                msg_index = i % 50  # Cycle through 50 unique messages
                messages = [Message(role=Role.USER, content=f"Message {msg_index}")]
                await cached.generate(messages)

            # Should have called provider 50 times (once per unique message)
            assert mock_provider.generate.call_count == 50

            # Cache should be at max size
            stats = cached.get_cache_stats()
            assert stats["size"] == 50

            # Hit rate should be 50% (50 hits out of 100 requests)
            assert stats["hit_rate"] == 0.5

        finally:
            await cached.shutdown()
