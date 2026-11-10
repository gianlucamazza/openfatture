"""E2E tests for AI agents using real OpenAI provider.

Requires OPENFATTURE_AI_OPENAI_API_KEY to be set.
Run with: pytest -m "openai and e2e"
"""

import pytest

pytestmark = pytest.mark.asyncio


@pytest.mark.openai
@pytest.mark.e2e
class TestOpenAIProviderCapabilities:
    """Test OpenAI provider specific capabilities."""

    async def test_streaming_support(self, openai_provider):
        """Test that OpenAI provider supports streaming."""
        from openfatture.ai.domain.message import Message, Role

        assert openai_provider.supports_streaming

        # Test basic streaming (must use Message objects, not dicts)
        messages = [Message(role=Role.USER, content="Hello")]
        tokens = []
        async for token in openai_provider.stream(messages):
            tokens.append(token)
            if len(tokens) >= 5:  # Get first few tokens
                break

        assert len(tokens) > 0
        assert all(isinstance(token, str) for token in tokens)

    async def test_tool_calling_support(self, openai_provider):
        """Test that OpenAI provider supports tool calling."""
        assert openai_provider.supports_tools

    async def test_token_counting_accuracy(self, openai_provider):
        """Test token counting is reasonable."""
        text = "Questo è un testo di prova per contare i token."
        tokens = openai_provider.count_tokens(text)

        # Should be reasonable estimate (Italian text)
        assert 10 <= tokens <= 20

        # Empty text should be 0
        assert openai_provider.count_tokens("") == 0

    async def test_cost_estimation(self, openai_provider):
        """Test cost estimation for different token counts."""
        from openfatture.ai.domain.response import UsageMetrics

        # Low usage
        low_usage = UsageMetrics(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        low_cost = openai_provider.estimate_cost(low_usage)
        assert low_cost > 0

        # High usage
        high_usage = UsageMetrics(prompt_tokens=1000, completion_tokens=500, total_tokens=1500)
        high_cost = openai_provider.estimate_cost(high_usage)
        assert high_cost > low_cost  # Higher usage should cost more

    async def test_health_check_reliability(self, openai_provider):
        """Test health check works consistently."""
        # Should pass multiple times
        for _ in range(3):
            healthy = await openai_provider.health_check()
            assert healthy is True
