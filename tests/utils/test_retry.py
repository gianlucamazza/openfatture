"""Comprehensive test suite for unified retry logic.

Tests cover:
- RetryConfig validation and delay calculation
- Successful retry after failures
- Retry exhaustion
- Exception type filtering
- Jitter behavior
- Custom retry callbacks
- Sync wrapper
- Pre-configured strategies
"""

from unittest.mock import AsyncMock, Mock

import pytest

from openfatture.utils.retry import (
    AI_PROVIDER_RETRY,
    DATABASE_RETRY,
    NETWORK_RETRY,
    RATE_LIMIT_RETRY,
    RetryConfig,
    retry_async,
    retry_sync,
)

# ============================================================================
# RetryConfig Tests
# ============================================================================


class TestRetryConfig:
    """Test RetryConfig validation and delay calculation."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RetryConfig()

        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.backoff_factor == 2.0
        assert config.jitter is True
        assert config.jitter_range == 0.1

    def test_custom_config(self):
        """Test custom configuration values."""
        config = RetryConfig(
            max_retries=5,
            base_delay=2.0,
            max_delay=30.0,
            backoff_factor=1.5,
            jitter=False,
        )

        assert config.max_retries == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 30.0
        assert config.backoff_factor == 1.5
        assert config.jitter is False

    def test_validation_negative_max_retries(self):
        """Test that negative max_retries raises ValueError."""
        with pytest.raises(ValueError, match="max_retries must be >= 0"):
            RetryConfig(max_retries=-1)

    def test_validation_zero_base_delay(self):
        """Test that zero or negative base_delay raises ValueError."""
        with pytest.raises(ValueError, match="base_delay must be > 0"):
            RetryConfig(base_delay=0)

        with pytest.raises(ValueError, match="base_delay must be > 0"):
            RetryConfig(base_delay=-1.0)

    def test_validation_max_delay_less_than_base(self):
        """Test that max_delay < base_delay raises ValueError."""
        with pytest.raises(ValueError, match="max_delay must be >= base_delay"):
            RetryConfig(base_delay=10.0, max_delay=5.0)

    def test_validation_backoff_factor_less_than_one(self):
        """Test that backoff_factor < 1 raises ValueError."""
        with pytest.raises(ValueError, match="backoff_factor must be >= 1"):
            RetryConfig(backoff_factor=0.5)

    def test_validation_jitter_range_out_of_bounds(self):
        """Test that jitter_range outside [0, 1] raises ValueError."""
        with pytest.raises(ValueError, match="jitter_range must be between 0 and 1"):
            RetryConfig(jitter_range=-0.1)

        with pytest.raises(ValueError, match="jitter_range must be between 0 and 1"):
            RetryConfig(jitter_range=1.5)

    def test_calculate_delay_no_jitter(self):
        """Test delay calculation without jitter."""
        config = RetryConfig(
            base_delay=1.0,
            max_delay=100.0,
            backoff_factor=2.0,
            jitter=False,
        )

        # Attempt 0: 1.0 * (2.0 ^ 0) = 1.0
        assert config.calculate_delay(0) == 1.0

        # Attempt 1: 1.0 * (2.0 ^ 1) = 2.0
        assert config.calculate_delay(1) == 2.0

        # Attempt 2: 1.0 * (2.0 ^ 2) = 4.0
        assert config.calculate_delay(2) == 4.0

        # Attempt 3: 1.0 * (2.0 ^ 3) = 8.0
        assert config.calculate_delay(3) == 8.0

    def test_calculate_delay_with_max_cap(self):
        """Test that delay is capped at max_delay."""
        config = RetryConfig(
            base_delay=1.0,
            max_delay=5.0,
            backoff_factor=2.0,
            jitter=False,
        )

        # Attempt 10: Would be 1024.0, but capped at 5.0
        assert config.calculate_delay(10) == 5.0

    def test_calculate_delay_with_jitter(self):
        """Test that jitter adds randomness within expected range."""
        config = RetryConfig(
            base_delay=10.0,
            max_delay=100.0,
            backoff_factor=2.0,
            jitter=True,
            jitter_range=0.1,  # ±10%
        )

        # Run multiple times to check range
        delays = [config.calculate_delay(0) for _ in range(100)]

        # Expected delay without jitter: 10.0
        # With ±10% jitter: 9.0 to 11.0
        assert all(9.0 <= d <= 11.0 for d in delays)
        assert min(delays) < 9.5  # Should have some low values
        assert max(delays) > 10.5  # Should have some high values


# ============================================================================
# retry_async Tests
# ============================================================================


class TestRetryAsync:
    """Test async retry functionality."""

    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self):
        """Test that successful function returns immediately."""
        func = AsyncMock(return_value="success")

        result = await retry_async(func)

        assert result == "success"
        func.assert_called_once()

    @pytest.mark.asyncio
    async def test_success_after_retries(self):
        """Test that function succeeds after some failures."""
        func = AsyncMock(
            side_effect=[
                Exception("fail 1"),
                Exception("fail 2"),
                "success",
            ]
        )

        config = RetryConfig(max_retries=3, base_delay=0.01)  # Fast for tests
        result = await retry_async(func, config=config)

        assert result == "success"
        assert func.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhaustion(self):
        """Test that exception is raised after max retries."""
        func = AsyncMock(side_effect=Exception("persistent failure"))

        config = RetryConfig(max_retries=2, base_delay=0.01)

        with pytest.raises(Exception, match="persistent failure"):
            await retry_async(func, config=config)

        assert func.call_count == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_non_retryable_exception(self):
        """Test that non-retryable exceptions are not retried."""
        func = AsyncMock(side_effect=ValueError("not retryable"))

        config = RetryConfig(
            max_retries=5,
            retryable_exceptions=(ConnectionError, TimeoutError),
        )

        with pytest.raises(ValueError, match="not retryable"):
            await retry_async(func, config=config)

        func.assert_called_once()  # No retries

    @pytest.mark.asyncio
    async def test_retryable_exception_filter(self):
        """Test that only specified exceptions are retried."""
        func = AsyncMock(
            side_effect=[
                ConnectionError("retryable"),
                "success",
            ]
        )

        config = RetryConfig(
            max_retries=3,
            base_delay=0.01,
            retryable_exceptions=(ConnectionError, TimeoutError),
        )

        result = await retry_async(func, config=config)

        assert result == "success"
        assert func.call_count == 2

    @pytest.mark.asyncio
    async def test_on_retry_callback(self):
        """Test that on_retry callback is called for each retry."""
        func = AsyncMock(
            side_effect=[
                Exception("fail 1"),
                Exception("fail 2"),
                "success",
            ]
        )

        callback = AsyncMock()
        config = RetryConfig(max_retries=3, base_delay=0.01)

        result = await retry_async(func, config=config, on_retry=callback)

        assert result == "success"
        assert callback.call_count == 2  # Called for 2 failures

        # Check callback arguments
        calls = callback.call_args_list
        assert isinstance(calls[0][0][0], Exception)  # First arg is exception
        assert calls[0][0][1] == 1  # Second arg is attempt number
        assert calls[1][0][1] == 2

    @pytest.mark.asyncio
    async def test_on_retry_callback_failure_doesnt_stop_retry(self):
        """Test that callback failures don't prevent retries."""
        func = AsyncMock(side_effect=[Exception("fail"), "success"])

        callback = AsyncMock(side_effect=Exception("callback error"))
        config = RetryConfig(max_retries=2, base_delay=0.01)

        result = await retry_async(func, config=config, on_retry=callback)

        assert result == "success"  # Still succeeds despite callback error

    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self):
        """Test that delays follow exponential backoff."""
        func = AsyncMock(
            side_effect=[
                Exception("fail 1"),
                Exception("fail 2"),
                Exception("fail 3"),
                "success",
            ]
        )

        config = RetryConfig(
            max_retries=4,
            base_delay=0.1,
            backoff_factor=2.0,
            jitter=False,
        )

        import time

        start = time.time()
        result = await retry_async(func, config=config)
        duration = time.time() - start

        assert result == "success"

        # Expected delays: 0.1 + 0.2 + 0.4 = 0.7 seconds
        # Allow some tolerance for execution time
        assert 0.6 < duration < 1.0

    @pytest.mark.asyncio
    async def test_zero_retries(self):
        """Test behavior with max_retries=0."""
        func = AsyncMock(side_effect=Exception("immediate fail"))

        config = RetryConfig(max_retries=0)

        with pytest.raises(Exception, match="immediate fail"):
            await retry_async(func, config=config)

        func.assert_called_once()  # No retries


# ============================================================================
# retry_sync Tests
# ============================================================================


class TestRetrySync:
    """Test synchronous retry wrapper."""

    def test_success_on_first_attempt(self):
        """Test that successful sync function returns immediately."""
        func = Mock(return_value="success")

        result = retry_sync(func)

        assert result == "success"
        func.assert_called_once()

    def test_success_after_retries(self):
        """Test that sync function succeeds after failures."""
        func = Mock(
            side_effect=[
                Exception("fail 1"),
                Exception("fail 2"),
                "success",
            ]
        )

        config = RetryConfig(max_retries=3, base_delay=0.01)
        result = retry_sync(func, config=config)

        assert result == "success"
        assert func.call_count == 3

    def test_retry_exhaustion(self):
        """Test that exception is raised after max retries in sync mode."""
        func = Mock(side_effect=Exception("persistent failure"))

        config = RetryConfig(max_retries=2, base_delay=0.01)

        with pytest.raises(Exception, match="persistent failure"):
            retry_sync(func, config=config)

        assert func.call_count == 3

    def test_on_retry_callback_sync(self):
        """Test that sync on_retry callback works."""
        func = Mock(side_effect=[Exception("fail"), "success"])

        callback = Mock()
        config = RetryConfig(max_retries=2, base_delay=0.01)

        result = retry_sync(func, config=config, on_retry=callback)

        assert result == "success"
        callback.assert_called_once()


# ============================================================================
# Pre-configured Strategies Tests
# ============================================================================


class TestPreConfiguredStrategies:
    """Test pre-configured retry strategies."""

    def test_network_retry_config(self):
        """Test NETWORK_RETRY configuration."""
        assert NETWORK_RETRY.max_retries == 5
        assert NETWORK_RETRY.base_delay == 0.5
        assert NETWORK_RETRY.max_delay == 5.0
        assert NETWORK_RETRY.backoff_factor == 2.0

    def test_rate_limit_retry_config(self):
        """Test RATE_LIMIT_RETRY configuration."""
        assert RATE_LIMIT_RETRY.max_retries == 10
        assert RATE_LIMIT_RETRY.base_delay == 5.0
        assert RATE_LIMIT_RETRY.max_delay == 120.0

    def test_database_retry_config(self):
        """Test DATABASE_RETRY configuration."""
        assert DATABASE_RETRY.max_retries == 3
        assert DATABASE_RETRY.base_delay == 1.0
        assert DATABASE_RETRY.max_delay == 10.0

    def test_ai_provider_retry_config(self):
        """Test AI_PROVIDER_RETRY configuration."""
        assert AI_PROVIDER_RETRY.max_retries == 5
        assert AI_PROVIDER_RETRY.base_delay == 2.0
        assert AI_PROVIDER_RETRY.max_delay == 60.0
        assert AI_PROVIDER_RETRY.backoff_factor == 2.5

    @pytest.mark.asyncio
    async def test_network_retry_in_practice(self):
        """Test using NETWORK_RETRY in a realistic scenario."""
        func = AsyncMock(
            side_effect=[
                ConnectionError("network error 1"),
                ConnectionError("network error 2"),
                "success",
            ]
        )

        result = await retry_async(func, config=NETWORK_RETRY)

        assert result == "success"
        assert func.call_count == 3
