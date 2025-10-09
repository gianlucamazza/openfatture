"""Unit tests for rate limiter."""

import time
from unittest.mock import patch

import pytest

from openfatture.utils.rate_limiter import (
    ExponentialBackoff,
    RateLimiter,
    SlidingWindowRateLimiter,
    retry_with_backoff,
)

pytestmark = pytest.mark.unit


class TestRateLimiter:
    """Tests for RateLimiter."""

    def test_init(self):
        """Test initialization."""
        limiter = RateLimiter(max_calls=10, period=60)

        assert limiter.max_calls == 10
        assert limiter.period == 60
        assert len(limiter.calls) == 0

    def test_acquire_first_call(self):
        """Test acquiring permission on first call."""
        limiter = RateLimiter(max_calls=5, period=10)

        success = limiter.acquire(blocking=False)

        assert success is True
        assert len(limiter.calls) == 1

    def test_acquire_within_limit(self):
        """Test acquiring within rate limit."""
        limiter = RateLimiter(max_calls=5, period=10)

        # Acquire 5 times (at limit)
        for _ in range(5):
            assert limiter.acquire(blocking=False) is True

        assert len(limiter.calls) == 5

    def test_acquire_exceeds_limit_non_blocking(self):
        """Test acquiring when limit exceeded (non-blocking)."""
        limiter = RateLimiter(max_calls=3, period=10)

        # Acquire 3 times (at limit)
        for _ in range(3):
            assert limiter.acquire(blocking=False) is True

        # 4th call should fail
        success = limiter.acquire(blocking=False)
        assert success is False

    def test_acquire_old_calls_expire(self):
        """Test that old calls outside window are removed."""
        limiter = RateLimiter(max_calls=2, period=1)  # 1 second window

        # Make 2 calls
        assert limiter.acquire(blocking=False) is True
        assert limiter.acquire(blocking=False) is True

        # Should be at limit
        assert limiter.acquire(blocking=False) is False

        # Wait for window to expire
        time.sleep(1.1)

        # Should be able to acquire again
        assert limiter.acquire(blocking=False) is True

    def test_get_wait_time_no_wait(self):
        """Test get_wait_time when no wait needed."""
        limiter = RateLimiter(max_calls=5, period=10)

        wait_time = limiter.get_wait_time()

        assert wait_time == 0.0

    def test_get_wait_time_with_wait(self):
        """Test get_wait_time when at limit."""
        limiter = RateLimiter(max_calls=2, period=10)

        # Fill up the limit
        limiter.acquire(blocking=False)
        limiter.acquire(blocking=False)

        # Should need to wait
        wait_time = limiter.get_wait_time()
        assert wait_time > 0
        assert wait_time <= 10

    def test_reset(self):
        """Test resetting the rate limiter."""
        limiter = RateLimiter(max_calls=2, period=10)

        limiter.acquire(blocking=False)
        limiter.acquire(blocking=False)
        assert len(limiter.calls) == 2

        limiter.reset()

        assert len(limiter.calls) == 0
        # Should be able to acquire again
        assert limiter.acquire(blocking=False) is True

    def test_decorator_usage(self):
        """Test using rate limiter as decorator."""
        limiter = RateLimiter(max_calls=2, period=10)

        call_count = 0

        @limiter
        def test_func():
            nonlocal call_count
            call_count += 1
            return "success"

        # First 2 calls should succeed immediately
        assert test_func() == "success"
        assert test_func() == "success"
        assert call_count == 2

    def test_acquire_with_timeout(self):
        """Test acquire with timeout."""
        limiter = RateLimiter(max_calls=1, period=10)

        # First acquire succeeds
        assert limiter.acquire(blocking=False) is True

        # Second with short timeout should fail
        success = limiter.acquire(blocking=True, timeout=0.2)
        assert success is False


class TestExponentialBackoff:
    """Tests for ExponentialBackoff."""

    def test_init(self):
        """Test initialization."""
        backoff = ExponentialBackoff(base=1.0, max_delay=60.0)

        assert backoff.base == 1.0
        assert backoff.max_delay == 60.0

    def test_get_delay_exponential_growth(self):
        """Test delay grows exponentially."""
        backoff = ExponentialBackoff(base=1.0, max_delay=100.0, jitter=False)

        delay0 = backoff.get_delay(0)
        delay1 = backoff.get_delay(1)
        delay2 = backoff.get_delay(2)
        delay3 = backoff.get_delay(3)

        assert delay0 == 1.0  # 1 * 2^0
        assert delay1 == 2.0  # 1 * 2^1
        assert delay2 == 4.0  # 1 * 2^2
        assert delay3 == 8.0  # 1 * 2^3

    def test_get_delay_caps_at_max(self):
        """Test delay is capped at max_delay."""
        backoff = ExponentialBackoff(base=1.0, max_delay=10.0, jitter=False)

        delay10 = backoff.get_delay(10)  # Would be 1024 without cap

        assert delay10 == 10.0

    def test_get_delay_with_jitter(self):
        """Test jitter adds randomness."""
        backoff = ExponentialBackoff(base=1.0, max_delay=100.0, jitter=True)

        # Get multiple delays for same attempt
        delays = [backoff.get_delay(2) for _ in range(10)]

        # All should be around 4.0 but with variation
        for delay in delays:
            assert 2.0 <= delay <= 6.0  # base=1, attempt=2 → 4 * [0.5, 1.5]

        # Should have some variation
        assert len(set(delays)) > 1


class TestSlidingWindowRateLimiter:
    """Tests for SlidingWindowRateLimiter."""

    def test_init(self):
        """Test initialization."""
        limiter = SlidingWindowRateLimiter(max_calls=100, window=3600)

        assert limiter.max_calls == 100
        assert limiter.window == 3600
        assert len(limiter.calls) == 0

    def test_acquire_within_limit(self):
        """Test acquiring within limit."""
        limiter = SlidingWindowRateLimiter(max_calls=3, window=10)

        assert limiter.acquire(blocking=False) is True
        assert limiter.acquire(blocking=False) is True
        assert limiter.acquire(blocking=False) is True

    def test_acquire_exceeds_limit(self):
        """Test exceeding limit."""
        limiter = SlidingWindowRateLimiter(max_calls=2, window=10)

        assert limiter.acquire(blocking=False) is True
        assert limiter.acquire(blocking=False) is True
        # 3rd should fail
        assert limiter.acquire(blocking=False) is False

    def test_reset(self):
        """Test resetting limiter."""
        limiter = SlidingWindowRateLimiter(max_calls=2, window=10)

        limiter.acquire(blocking=False)
        limiter.reset()

        assert len(limiter.calls) == 0


class TestRetryWithBackoff:
    """Tests for retry_with_backoff decorator."""

    def test_success_first_attempt(self):
        """Test successful operation on first attempt."""
        call_count = 0

        @retry_with_backoff(max_attempts=3, base_delay=0.1)
        def func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = func()

        assert result == "success"
        assert call_count == 1

    def test_retry_on_failure(self):
        """Test retry after failure."""
        call_count = 0

        @retry_with_backoff(max_attempts=3, base_delay=0.1)
        def func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = func()

        assert result == "success"
        assert call_count == 3

    def test_max_attempts_exceeded(self):
        """Test all attempts fail."""
        call_count = 0

        @retry_with_backoff(max_attempts=3, base_delay=0.1)
        def func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            func()

        assert call_count == 3

    def test_specific_exceptions(self):
        """Test retrying only specific exceptions."""

        @retry_with_backoff(max_attempts=3, base_delay=0.1, exceptions=(ValueError,))
        def func():
            raise TypeError("Wrong exception")

        # Should fail immediately without retry
        with pytest.raises(TypeError):
            func()

    @patch("time.sleep")
    def test_backoff_delay(self, mock_sleep):
        """Test that backoff delays are applied."""

        @retry_with_backoff(max_attempts=3, base_delay=1.0)
        def func():
            raise ValueError("Error")

        with pytest.raises(ValueError):
            func()

        # Should have called sleep twice (not after last attempt)
        assert mock_sleep.call_count == 2
