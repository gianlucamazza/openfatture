"""
Rate limiting utilities for API calls and email sending.

Prevents exceeding rate limits of external services (PEC servers, APIs).
"""

import time
from collections import deque
from collections.abc import Callable
from datetime import datetime, timedelta
from functools import wraps
from threading import Lock


class RateLimiter:
    """
    Token bucket rate limiter.

    Limits the rate of operations to prevent exceeding service limits.

    Usage:
        limiter = RateLimiter(max_calls=10, period=60)  # 10 calls per minute

        @limiter.limit
        def send_email():
            # ... send email
            pass
    """

    def __init__(self, max_calls: int, period: int):
        """
        Initialize rate limiter.

        Args:
            max_calls: Maximum number of calls allowed in the period
            period: Time period in seconds
        """
        self.max_calls = max_calls
        self.period = period
        self.calls: deque[float] = deque()  # Timestamps of recent calls
        self.lock = Lock()

    def __call__(self, func: Callable) -> Callable:
        """
        Decorator to apply rate limiting to a function.

        Args:
            func: Function to rate limit

        Returns:
            Wrapped function with rate limiting
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            self.acquire()
            return func(*args, **kwargs)

        return wrapper

    def acquire(self, blocking: bool = True, timeout: float | None = None) -> bool:
        """
        Acquire permission to make a call.

        Args:
            blocking: If True, blocks until permission is granted
            timeout: Maximum time to wait in seconds (only if blocking=True)

        Returns:
            True if permission granted, False otherwise
        """
        start_time = time.time()

        while True:
            with self.lock:
                now = time.time()

                # Remove old calls outside the time window
                while self.calls and self.calls[0] <= now - self.period:
                    self.calls.popleft()

                # Check if we can make a call
                if len(self.calls) < self.max_calls:
                    self.calls.append(now)
                    return True

                # Not blocking, return immediately
                if not blocking:
                    return False

                # Check timeout
                if timeout is not None and (time.time() - start_time) >= timeout:
                    return False

            # Wait a bit before retrying
            time.sleep(0.1)

    def get_wait_time(self) -> float:
        """
        Get time to wait before next call is allowed.

        Returns:
            Seconds to wait, or 0 if call can be made immediately
        """
        with self.lock:
            now = time.time()

            # Remove old calls
            while self.calls and self.calls[0] <= now - self.period:
                self.calls.popleft()

            # If we can make a call, no wait needed
            if len(self.calls) < self.max_calls:
                return 0.0

            # Calculate wait time until oldest call expires
            oldest_call = self.calls[0]
            wait_time = (oldest_call + self.period) - now
            return max(0.0, wait_time)

    def reset(self) -> None:
        """Reset the rate limiter, clearing all tracked calls."""
        with self.lock:
            self.calls.clear()


class ExponentialBackoff:
    """
    Exponential backoff for retry logic.

    Increases wait time exponentially after each failure.

    Usage:
        backoff = ExponentialBackoff(base=1, max_delay=60)

        for attempt in range(5):
            try:
                # ... operation
                break
            except Exception:
                time.sleep(backoff.get_delay(attempt))
    """

    def __init__(self, base: float = 1.0, max_delay: float = 60.0, jitter: bool = True):
        """
        Initialize exponential backoff.

        Args:
            base: Base delay in seconds
            max_delay: Maximum delay in seconds
            jitter: Add random jitter to prevent thundering herd
        """
        self.base = base
        self.max_delay = max_delay
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """
        Get delay for given attempt number.

        Args:
            attempt: Attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        # Calculate exponential delay
        delay = self.base * (2**attempt)

        # Cap at max delay
        delay = min(delay, self.max_delay)

        # Add jitter if enabled
        if self.jitter:
            import random

            delay *= random.uniform(0.5, 1.5)

        return delay


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter.

    More accurate than token bucket for bursty traffic.

    Usage:
        limiter = SlidingWindowRateLimiter(max_calls=100, window=3600)  # 100/hour
    """

    def __init__(self, max_calls: int, window: int):
        """
        Initialize sliding window rate limiter.

        Args:
            max_calls: Maximum calls in window
            window: Window size in seconds
        """
        self.max_calls = max_calls
        self.window = window
        self.calls: list[datetime] = []  # Timestamps of recent calls
        self.lock = Lock()

    def acquire(self, blocking: bool = True, timeout: float | None = None) -> bool:
        """
        Acquire permission to make a call.

        Args:
            blocking: If True, blocks until permission is granted
            timeout: Maximum time to wait

        Returns:
            True if permitted, False otherwise
        """
        start_time = time.time()

        while True:
            with self.lock:
                now = datetime.now()
                window_start = now - timedelta(seconds=self.window)

                # Remove calls outside window
                self.calls = [call_time for call_time in self.calls if call_time > window_start]

                # Check if we can make a call
                if len(self.calls) < self.max_calls:
                    self.calls.append(now)
                    return True

                # Not blocking
                if not blocking:
                    return False

                # Check timeout
                if timeout and (time.time() - start_time) >= timeout:
                    return False

            time.sleep(0.1)

    def reset(self) -> None:
        """Reset the rate limiter."""
        with self.lock:
            self.calls.clear()


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,),
):
    """
    Decorator for retrying with exponential backoff.

    Args:
        max_attempts: Maximum retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exceptions: Tuple of exceptions to catch

    Usage:
        @retry_with_backoff(max_attempts=3, base_delay=1.0)
        def send_email():
            # ... code that might fail
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            backoff = ExponentialBackoff(base=base_delay, max_delay=max_delay)

            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = backoff.get_delay(attempt)
                        time.sleep(delay)

            # All attempts failed
            if last_exception:
                raise last_exception

        return wrapper

    return decorator


def retry_with_backoff_async(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,),
):
    """
    Async decorator for retrying with exponential backoff.

    Args:
        max_attempts: Maximum retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exceptions: Tuple of exceptions to catch

    Usage:
        @retry_with_backoff_async(max_attempts=3, base_delay=1.0)
        async def fetch_data():
            # ... async code that might fail
            pass
    """
    import asyncio

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            backoff = ExponentialBackoff(base=base_delay, max_delay=max_delay)

            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = backoff.get_delay(attempt)
                        await asyncio.sleep(delay)

            # All attempts failed
            if last_exception:
                raise last_exception

        return wrapper

    return decorator


# Pre-configured rate limiters for common use cases

# PEC email rate limiter (conservative: 10 emails per minute)
pec_rate_limiter = RateLimiter(max_calls=10, period=60)

# API rate limiter (100 calls per hour)
api_rate_limiter = RateLimiter(max_calls=100, period=3600)

# Database write rate limiter (1000 writes per minute)
db_write_limiter = RateLimiter(max_calls=1000, period=60)
