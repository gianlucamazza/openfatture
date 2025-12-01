"""Unified retry logic with exponential backoff and jitter.

This module provides a centralized retry mechanism to replace the 9+ different
retry implementations scattered across the codebase. It follows modern best practices:

- Exponential backoff with configurable base delay and max delay
- Optional jitter to prevent thundering herd
- Async-first design with sync wrapper
- Configurable retry strategies per use case
- Comprehensive error handling and logging

Usage:
    # Async function
    result = await retry_async(
        lambda: risky_api_call(),
        config=RetryConfig(max_retries=5, base_delay=2.0),
    )

    # Sync function
    result = retry_sync(
        lambda: risky_operation(),
        config=RetryConfig(max_retries=3),
    )

    # With custom retry callback
    async def on_retry_callback(error: Exception, attempt: int) -> None:
        logger.warning(f"Retry attempt {attempt}", error=str(error))

    result = await retry_async(
        func,
        config=RetryConfig(),
        on_retry=on_retry_callback,
    )

Migration from old patterns:
    # OLD (web/pages/5_🤖_AI_Assistant.py)
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)

    # NEW
    return await retry_async(func, RetryConfig(max_retries=max_retries))
"""

import asyncio
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TypeVar

from openfatture.utils.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


@dataclass
class RetryConfig:
    """Configuration for retry behavior.

    Attributes:
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Base delay in seconds before first retry (default: 1.0)
        max_delay: Maximum delay in seconds between retries (default: 60.0)
        backoff_factor: Exponential backoff multiplier (default: 2.0)
        jitter: Whether to add random jitter to delays (default: True)
        jitter_range: Range for jitter as fraction of delay (default: 0.1 = ±10%)
        retryable_exceptions: Tuple of exception types to retry (default: all)

    Examples:
        # Fast retries for transient errors
        RetryConfig(max_retries=5, base_delay=0.5, max_delay=5.0)

        # Slow retries for rate limiting
        RetryConfig(max_retries=10, base_delay=5.0, max_delay=120.0)

        # Retry only specific exceptions
        RetryConfig(
            max_retries=3,
            retryable_exceptions=(ConnectionError, TimeoutError)
        )
    """

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter: bool = True
    jitter_range: float = 0.1
    retryable_exceptions: tuple[type[Exception], ...] = field(default_factory=lambda: (Exception,))

    def __post_init__(self):
        """Validate configuration parameters."""
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if self.base_delay <= 0:
            raise ValueError("base_delay must be > 0")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if self.backoff_factor < 1:
            raise ValueError("backoff_factor must be >= 1")
        if not 0 <= self.jitter_range <= 1:
            raise ValueError("jitter_range must be between 0 and 1")

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a given retry attempt.

        Args:
            attempt: The retry attempt number (0-indexed)

        Returns:
            Delay in seconds, with exponential backoff and optional jitter
        """
        # Exponential backoff: delay = base_delay * (backoff_factor ^ attempt)
        delay = min(self.base_delay * (self.backoff_factor**attempt), self.max_delay)

        # Add jitter to prevent thundering herd
        if self.jitter:
            jitter_amount = delay * self.jitter_range
            jitter = random.uniform(-jitter_amount, jitter_amount)
            delay = max(0, delay + jitter)

        return delay


async def retry_async(
    func: Callable[[], Awaitable[T]],
    config: RetryConfig | None = None,
    on_retry: Callable[[Exception, int], Awaitable[None]] | None = None,
) -> T:
    """Retry an async function with exponential backoff.

    This is the primary retry function for async operations. It handles:
    - Exponential backoff with configurable parameters
    - Optional jitter to prevent thundering herd
    - Custom retry callbacks for logging/metrics
    - Selective retry based on exception type

    Args:
        func: Async function to retry (takes no arguments)
        config: Retry configuration (uses defaults if None)
        on_retry: Optional callback called before each retry
                 Signature: async def on_retry(error: Exception, attempt: int)

    Returns:
        The return value of func() on success

    Raises:
        The last exception if all retries are exhausted

    Examples:
        # Simple retry
        result = await retry_async(lambda: api_call())

        # With custom config
        result = await retry_async(
            lambda: flaky_operation(),
            config=RetryConfig(max_retries=5, base_delay=2.0),
        )

        # With retry callback for logging
        async def log_retry(error: Exception, attempt: int):
            logger.warning(f"Retry {attempt}: {error}")

        result = await retry_async(func, on_retry=log_retry)
    """
    config = config or RetryConfig()
    last_exception: Exception | None = None

    for attempt in range(config.max_retries + 1):
        try:
            # Execute the function
            return await func()

        except Exception as e:
            last_exception = e

            # Check if this exception type is retryable
            if not isinstance(e, config.retryable_exceptions):
                logger.debug(
                    "retry_skipped_non_retryable_exception",
                    exception_type=type(e).__name__,
                    error=str(e),
                )
                raise

            # Check if we have retries left
            if attempt >= config.max_retries:
                logger.error(
                    "retry_exhausted",
                    attempts=attempt + 1,
                    exception=type(e).__name__,
                    error=str(e),
                )
                raise

            # Calculate delay for this attempt
            delay = config.calculate_delay(attempt)

            # Log retry attempt
            logger.info(
                "retry_attempt",
                attempt=attempt + 1,
                max_retries=config.max_retries,
                delay_seconds=round(delay, 2),
                exception=type(e).__name__,
                error=str(e),
            )

            # Call retry callback if provided
            if on_retry:
                try:
                    await on_retry(e, attempt + 1)
                except Exception as callback_error:
                    logger.warning(
                        "retry_callback_failed",
                        error=str(callback_error),
                    )

            # Wait before next retry
            await asyncio.sleep(delay)

    # This should never be reached, but satisfy type checker
    if last_exception:
        raise last_exception
    raise RuntimeError("retry_async: unexpected code path")


def retry_sync(
    func: Callable[[], T],
    config: RetryConfig | None = None,
    on_retry: Callable[[Exception, int], None] | None = None,
) -> T:
    """Sync wrapper around retry_async for blocking operations.

    Use this when you need to retry a synchronous function. It internally
    uses asyncio.run() to execute the async retry logic.

    Args:
        func: Sync function to retry (takes no arguments)
        config: Retry configuration (uses defaults if None)
        on_retry: Optional sync callback called before each retry
                 Signature: def on_retry(error: Exception, attempt: int)

    Returns:
        The return value of func() on success

    Raises:
        The last exception if all retries are exhausted

    Examples:
        # Retry a sync API call
        result = retry_sync(
            lambda: requests.get("https://api.example.com"),
            config=RetryConfig(max_retries=5),
        )

        # With retry callback
        def log_retry(error: Exception, attempt: int):
            print(f"Retry {attempt}: {error}")

        result = retry_sync(func, on_retry=log_retry)
    """
    config = config or RetryConfig()

    # Convert sync callback to async if provided
    async def async_on_retry(error: Exception, attempt: int) -> None:
        if on_retry:
            on_retry(error, attempt)

    # Convert sync func to async
    async def async_func() -> T:
        return func()

    # Run async retry logic
    return asyncio.run(
        retry_async(
            async_func,
            config=config,
            on_retry=async_on_retry if on_retry else None,
        )
    )


# Pre-configured retry strategies for common use cases

# Fast retries for transient network errors
NETWORK_RETRY = RetryConfig(
    max_retries=5,
    base_delay=0.5,
    max_delay=5.0,
    backoff_factor=2.0,
)

# Slow retries for API rate limiting
RATE_LIMIT_RETRY = RetryConfig(
    max_retries=10,
    base_delay=5.0,
    max_delay=120.0,
    backoff_factor=2.0,
)

# Database connection retries
DATABASE_RETRY = RetryConfig(
    max_retries=3,
    base_delay=1.0,
    max_delay=10.0,
    backoff_factor=2.0,
)

# AI provider retries (long delays for quota limits)
AI_PROVIDER_RETRY = RetryConfig(
    max_retries=5,
    base_delay=2.0,
    max_delay=60.0,
    backoff_factor=2.5,
)
