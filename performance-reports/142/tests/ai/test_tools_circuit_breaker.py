"""Tests for tool circuit breaker integration.

Tests focus on circuit breaker functionality in ToolRegistry,
ensuring proper integration with tool execution.
"""

from unittest.mock import patch

import pytest

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType, ToolResult
from openfatture.ai.tools.registry import ToolRegistry


class TestToolCircuitBreaker:
    """Test circuit breaker integration in ToolRegistry."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = ToolRegistry()

        # Create a mock tool
        self.mock_tool = Tool(
            name="test_tool",
            description="Test tool for circuit breaker testing",
            category="test",
            func=lambda: None,  # Mock function
            parameters=[
                ToolParameter(
                    name="param1",
                    type=ToolParameterType.STRING,
                    description="Test parameter",
                    required=True,
                )
            ],
        )

        # Register the tool
        self.registry.register(self.mock_tool)

    def test_circuit_breaker_creation(self):
        """Test that circuit breakers are created for tools."""
        # Get circuit breaker for the tool
        breaker = self.registry.get_circuit_breaker("test_tool")

        assert breaker is not None
        assert breaker.name == "tool_test_tool"
        assert breaker.state.state.value == "closed"

    def test_resilience_config_read_tools(self):
        """Test resilience config for read operations."""
        config = self.registry._get_resilience_config("search_invoices")

        assert config.failure_threshold == 10  # Higher tolerance
        assert config.success_threshold == 3  # Need more successes
        assert config.timeout_seconds == 30  # Faster recovery
        assert config.half_open_max_calls == 5  # More calls in half-open

    def test_resilience_config_write_tools(self):
        """Test resilience config for write operations."""
        config = self.registry._get_resilience_config("create_invoice")

        assert config.failure_threshold == 3  # Lower tolerance
        assert config.success_threshold == 1  # Single success closes
        assert config.timeout_seconds == 120  # Longer recovery
        assert config.half_open_max_calls == 2  # Fewer calls in half-open

    def test_resilience_config_default(self):
        """Test default resilience config."""
        config = self.registry._get_resilience_config("unknown_tool")

        # Should use CircuitBreakerConfig defaults
        assert config.failure_threshold == 5
        assert config.success_threshold == 2
        assert config.timeout_seconds == 60
        assert config.half_open_max_calls == 3

    @patch("openfatture.ai.tools.registry.ToolRegistry._get_metrics")
    @pytest.mark.asyncio
    async def test_execute_tool_circuit_breaker_open(self, mock_get_metrics):
        """Test tool execution when circuit breaker is open."""
        mock_get_metrics.return_value = None

        # Get circuit breaker and force it open
        breaker = self.registry.get_circuit_breaker("test_tool")

        # Simulate failures to open circuit
        for _ in range(6):  # More than failure_threshold (5)
            breaker.record_failure()

        assert breaker.state.state.value == "open"

        # Execute tool - should fail due to circuit breaker
        result = await self.registry.execute_tool("test_tool", {"param1": "value"})

        # Should return circuit breaker error
        assert not result.success
        assert result.error_type == "circuit_breaker_open"
        assert result.error is not None
        assert "circuit breaker is open" in result.error.lower()
        assert result.circuit_breaker_state == "open"

    @patch("openfatture.ai.tools.registry.ToolRegistry._get_metrics")
    @pytest.mark.asyncio
    async def test_execute_tool_circuit_breaker_success(self, mock_get_metrics):
        """Test successful tool execution records circuit breaker success."""
        mock_get_metrics.return_value = None

        # Mock successful tool execution by patching the tool's func
        original_func = self.mock_tool.func

        async def mock_success_func(**kwargs):
            return ToolResult(success=True, data="test result", tool_name="test_tool")

        self.mock_tool.func = mock_success_func

        try:
            result = await self.registry.execute_tool("test_tool", {"param1": "value"})

            # Should record success
            breaker = self.registry.get_circuit_breaker("test_tool")
            assert breaker.state.state.value == "closed"
            assert result.success
            assert result.circuit_breaker_state == "closed"
        finally:
            # Restore original function
            self.mock_tool.func = original_func

    @patch("openfatture.ai.tools.registry.ToolRegistry._get_metrics")
    @pytest.mark.asyncio
    async def test_execute_tool_circuit_breaker_failure(self, mock_get_metrics):
        """Test failed tool execution records circuit breaker failure."""
        mock_get_metrics.return_value = None

        # Mock failed tool execution by making the func raise an exception
        original_func = self.mock_tool.func

        async def mock_failure_func(**kwargs):
            raise ValueError("Test error")

        self.mock_tool.func = mock_failure_func

        try:
            result = await self.registry.execute_tool("test_tool", {"param1": "value"})

            # Should record failure
            breaker = self.registry.get_circuit_breaker("test_tool")
            assert breaker.state.failure_count == 1
            assert not result.success
            assert result.circuit_breaker_state == "closed"  # Still closed after 1 failure
            assert result.error_type == "ValueError"
        finally:
            # Restore original function
            self.mock_tool.func = original_func

    def test_reset_circuit_breaker(self):
        """Test manual circuit breaker reset."""
        breaker = self.registry.get_circuit_breaker("test_tool")

        # Simulate failures
        for _ in range(6):
            breaker.record_failure()

        assert breaker.state.state.value == "open"

        # Reset circuit breaker
        result = self.registry.reset_circuit_breaker("test_tool")

        assert result is True
        assert breaker.state.state.value == "closed"
        assert breaker.state.failure_count == 0

    def test_reset_nonexistent_circuit_breaker(self):
        """Test reset of non-existent circuit breaker."""
        result = self.registry.reset_circuit_breaker("nonexistent_tool")

        assert result is False

    def test_get_circuit_breaker_stats(self):
        """Test circuit breaker statistics."""
        # Create a circuit breaker
        breaker = self.registry.get_circuit_breaker("test_tool")

        # Simulate some activity - record failure
        breaker.record_failure()

        stats = self.registry.get_circuit_breaker_stats()

        assert "test_tool" in stats
        assert stats["test_tool"]["state"] == "closed"
        assert stats["test_tool"]["failure_count"] == 1
        assert (
            stats["test_tool"]["success_count"] == 0
        )  # Success count only increments in half-open state

    def test_registry_stats_include_circuit_breakers(self):
        """Test that registry stats include circuit breaker information."""
        # Create a circuit breaker
        self.registry.get_circuit_breaker("test_tool")

        stats = self.registry.get_stats()

        assert "circuit_breakers" in stats
        assert stats["circuit_breakers"]["total"] == 1
        assert stats["circuit_breakers"]["by_state"]["closed"] == 1
        assert stats["circuit_breakers"]["by_state"]["open"] == 0
        assert stats["circuit_breakers"]["by_state"]["half_open"] == 0
        assert "test_tool" in stats["circuit_breakers"]["details"]
