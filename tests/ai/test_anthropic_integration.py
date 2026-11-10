"""E2E tests for AI agents using real Anthropic provider.

Requires OPENFATTURE_AI_ANTHROPIC_API_KEY to be set.
Run with: pytest -m "anthropic and e2e"
"""

import pytest


@pytest.mark.anthropic
@pytest.mark.e2e
class TestAnthropicProviderCapabilities:
    """Test Anthropic provider specific capabilities."""

    async def test_streaming_support(self, anthropic_provider):
        """Test that Anthropic provider supports streaming."""
        assert anthropic_provider.supports_streaming

        # Test basic streaming
        messages = [{"role": "user", "content": "Hello"}]
        tokens = []
        async for token in anthropic_provider.stream(messages):
            tokens.append(token)
            if len(tokens) >= 5:  # Get first few tokens
                break

        assert len(tokens) > 0
        assert all(isinstance(token, str) for token in tokens)

    async def test_tool_calling_support(self, anthropic_provider):
        """Test that Anthropic provider supports tool calling."""
        assert anthropic_provider.supports_tools

    async def test_token_counting_accuracy(self, anthropic_provider):
        """Test token counting is reasonable."""
        text = "Questo è un testo di prova per contare i token."
        tokens = anthropic_provider.count_tokens(text)

        # Should be reasonable estimate (Anthropic uses different tokenizer)
        assert 10 <= tokens <= 25

        # Empty text should be 0
        assert anthropic_provider.count_tokens("") == 0

    async def test_cost_estimation(self, anthropic_provider):
        """Test cost estimation for different token counts."""
        from openfatture.ai.domain.response import UsageMetrics

        # Low usage
        low_usage = UsageMetrics(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        low_cost = anthropic_provider.estimate_cost(low_usage)
        assert low_cost > 0

        # High usage
        high_usage = UsageMetrics(prompt_tokens=1000, completion_tokens=500, total_tokens=1500)
        high_cost = anthropic_provider.estimate_cost(high_usage)
        assert high_cost > low_cost  # Higher usage should cost more

    async def test_health_check_reliability(self, anthropic_provider):
        """Test health check works consistently."""
        # Should pass multiple times
        for _ in range(3):
            healthy = await anthropic_provider.health_check()
            assert healthy is True
