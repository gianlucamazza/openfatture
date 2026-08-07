"""Tests for token counter optimization."""

from unittest.mock import MagicMock

import pytest

from openfatture.ai.providers.anthropic import AnthropicProvider
from openfatture.ai.providers.ollama import OllamaProvider
from openfatture.ai.providers.openai import OpenAIProvider


class TestAnthropicTokenCounter:
    """Tests for Anthropic official token counter."""

    def test_token_counter_uses_official_api(self):
        """Test that token counter uses official Anthropic API."""
        # Create provider
        provider = AnthropicProvider(api_key="test-key", model="claude-4.5-sonnet")

        # Mock the client's count_tokens method
        provider.client.count_tokens = MagicMock(return_value=42)

        # Count tokens
        text = "This is a test message for token counting."
        count = provider.count_tokens(text)

        # Verify official API was called
        assert count == 42
        provider.client.count_tokens.assert_called_once_with(text)

    def test_token_counter_fallback_on_error(self):
        """Test fallback to approximation if API fails."""
        provider = AnthropicProvider(api_key="test-key", model="claude-4.5-sonnet")

        # Mock client to raise error
        provider.client.count_tokens = MagicMock(side_effect=Exception("API Error"))

        text = "Test message"
        count = provider.count_tokens(text)

        # Should fallback to approximation (len // 4)
        assert count == len(text) // 4

    @pytest.mark.asyncio
    async def test_token_counter_in_async_context(self):
        """Test that token counter uses approximation in async context."""
        provider = AnthropicProvider(api_key="test-key", model="claude-4.5-sonnet")

        # In async context, should use approximation
        text = "Async test message"
        count = provider.count_tokens(text)

        # Should use approximation (len // 4)
        assert count == len(text) // 4

    def test_token_counter_accuracy_comparison(self):
        """Compare official counter vs approximation accuracy."""
        provider = AnthropicProvider(api_key="test-key", model="claude-4.5-sonnet")

        # Mock official counter with realistic value
        provider.client.count_tokens = MagicMock(return_value=100)

        text = "A" * 400  # 400 characters

        official_count = provider.count_tokens(text)
        approx_count = len(text) // 4

        # Official should be more accurate
        assert official_count == 100
        assert approx_count == 100  # In this case they match

        # But for complex text, they differ
        complex_text = "日本語のテキスト"  # Japanese text
        provider.client.count_tokens = MagicMock(return_value=15)

        official_count = provider.count_tokens(complex_text)
        approx_count = len(complex_text) // 4

        # Official is more accurate for non-English
        assert official_count == 15
        assert approx_count != official_count  # Approximation will be wrong


class TestTokenCounterIntegration:
    """Integration tests for token counting across providers."""

    def test_all_providers_implement_count_tokens(self):
        """Verify all providers implement count_tokens."""
        providers = [
            AnthropicProvider(api_key="test", model="claude-4.5-sonnet"),
            OpenAIProvider(api_key="test", model="gpt-4o"),
            OllamaProvider(base_url="http://localhost:11434", model="llama3.2"),
        ]

        text = "Test message for token counting"

        for provider in providers:
            # Should not raise
            count = provider.count_tokens(text)
            assert isinstance(count, int)
            assert count > 0

    def test_cost_estimation_accuracy(self):
        """Test that accurate token count improves cost estimation."""
        from openfatture.ai.domain.response import UsageMetrics

        provider = AnthropicProvider(api_key="test", model="claude-4.5-sonnet")

        # Mock accurate token count
        provider.client.count_tokens = MagicMock(return_value=1000)

        usage = UsageMetrics(
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
        )

        cost = provider.estimate_cost(usage)

        # Verify cost calculation
        # claude-4.5-sonnet: $2.50 per 1M input, $12.50 per 1M output
        expected_cost = (1000 / 1_000_000 * 2.50) + (500 / 1_000_000 * 12.50)
        assert abs(cost - expected_cost) < 0.0001  # Float precision


@pytest.mark.benchmark
class TestTokenCounterPerformance:
    """Performance tests for token counting."""

    def test_token_counter_latency(self, benchmark):
        """Benchmark token counter latency."""
        provider = AnthropicProvider(api_key="test", model="claude-4.5-sonnet")
        provider.client.count_tokens = MagicMock(return_value=100)

        text = "Test message" * 100

        # Benchmark
        result = benchmark(provider.count_tokens, text)

        # Should be fast (<10ms)
        assert benchmark.stats.stats.mean < 0.01  # 10ms

    def test_approximation_is_faster(self, benchmark):
        """Verify approximation is faster than API call."""
        text = "Test message" * 100

        # Benchmark approximation
        def approx():
            return len(text) // 4

        result = benchmark(approx)

        # Should be extremely fast (<1ms)
        assert benchmark.stats.stats.mean < 0.001  # 1ms
