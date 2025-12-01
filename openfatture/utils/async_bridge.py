"""Unified async/sync bridge with proper event loop handling.

This module provides a standardized way to bridge between async and sync code,
replacing 19+ different implementations scattered across the codebase.

Modern best practices (2025):
- Uses asyncio.run() as the primary mechanism (Python 3.7+)
- Handles nested event loops (Streamlit, Jupyter)
- Thread-safe execution with proper cleanup
- Support for lifespan management (CLI commands)
- Context propagation for observability

Usage:
    # Basic async->sync bridge
    result = run_async(async_function())

    # With lifespan context (CLI commands)
    result = run_with_lifespan(async_function())

    # Check if running in async context
    if is_async_context():
        result = await async_function()
    else:
        result = run_async(async_function())

Migration from old patterns:
    # OLD (inconsistent)
    asyncio.run(coro)                    # Various places
    loop.run_until_complete(coro)        # Legacy
    nest_asyncio.apply()                 # Streamlit-specific

    # NEW (unified)
    run_async(coro)                      # Everywhere
"""

import asyncio
import threading
from collections.abc import Coroutine
from contextlib import contextmanager
from typing import Any, TypeVar

from openfatture.utils.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")

# Thread-local storage for event loop detection
_thread_local = threading.local()


def is_async_context() -> bool:
    """Check if currently running in an async context.

    Returns:
        True if there's a running event loop in current thread

    Examples:
        async def my_function():
            if is_async_context():
                # Can use await directly
                result = await async_operation()
            else:
                # Need to bridge to sync
                result = run_async(async_operation())
    """
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


def run_async(
    coro: Coroutine[Any, Any, T],
    *,
    debug: bool = False,
) -> T:
    """Execute async coroutine in sync context with proper loop handling.

    This is the primary async->sync bridge. It handles:
    - Creating new event loop if none exists
    - Nested loop detection (Streamlit, Jupyter)
    - Proper cleanup and exception propagation
    - Context variable propagation
    - Debug mode for development

    Args:
        coro: Async coroutine to execute
        debug: Enable debug mode for event loop (default: False)

    Returns:
        The return value of the coroutine

    Raises:
        Any exception raised by the coroutine

    Examples:
        # Simple usage
        result = run_async(async_function())

        # With arguments
        result = run_async(async_function(arg1, arg2))

        # Debug mode
        result = run_async(async_function(), debug=True)

    Note:
        Prefer using async/await natively when possible. Use this only
        when you need to call async code from sync context (CLI, scripts).
    """
    # Check if we're already in an async context
    try:
        loop = asyncio.get_running_loop()

        # We're in a running loop - this is a nested scenario
        # This happens in Streamlit, Jupyter, or async test frameworks
        logger.debug(
            "nested_event_loop_detected",
            thread=threading.current_thread().name,
        )

        # Try to use nest_asyncio for nested execution
        try:
            import nest_asyncio

            nest_asyncio.apply()
            return loop.run_until_complete(coro)
        except ImportError:
            logger.warning(
                "nested_loop_without_nest_asyncio",
                message="Install nest_asyncio for nested async support",
            )
            # Fall through to create new loop in thread
            return _run_in_thread(coro)

    except RuntimeError:
        # No running loop - this is the normal case
        pass

    # Create and run with new event loop (Python 3.7+ recommended way)
    try:
        return asyncio.run(coro, debug=debug)
    except Exception as e:
        logger.error(
            "async_bridge_failed",
            error=str(e),
            error_type=type(e).__name__,
        )
        raise


def _run_in_thread(coro: Coroutine[Any, Any, T]) -> T:
    """Run coroutine in a new thread with its own event loop.

    This is used when we detect a nested loop but nest_asyncio is not available.
    Creates a new thread with its own event loop to avoid conflicts.

    Args:
        coro: Coroutine to execute

    Returns:
        The return value of the coroutine
    """
    import concurrent.futures

    def run_in_new_loop():
        """Thread target function."""
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_in_new_loop)
        return future.result()


def run_with_lifespan(
    coro: Coroutine[Any, Any, T],
    *,
    debug: bool = False,
) -> T:
    """Execute async coroutine with CLI lifespan management.

    This is specifically for CLI commands that need proper startup/shutdown
    of application resources (database connections, HTTP clients, etc.).

    The lifespan context ensures:
    - Database connections are initialized
    - HTTP clients are properly configured
    - Resources are cleaned up on exit
    - Graceful shutdown on Ctrl+C

    Args:
        coro: Async coroutine to execute
        debug: Enable debug mode (default: False)

    Returns:
        The return value of the coroutine

    Examples:
        # CLI command with database access
        @app.command()
        def my_command():
            result = run_with_lifespan(async_my_command())
            print(result)

        async def async_my_command():
            # Database and other resources are available here
            async with get_db_session() as db:
                return db.query(Model).all()

    Note:
        Only use this for CLI commands. Web applications handle lifespan
        differently through ASGI lifecycle events.
    """
    from openfatture.cli.lifespan import run_sync_with_lifespan

    return run_sync_with_lifespan(coro, debug=debug)


@contextmanager
def async_context():
    """Context manager for safe async operations in sync code.

    Provides a context where async operations can be safely executed,
    with proper cleanup even if exceptions occur.

    Yields:
        A callable that executes coroutines: executor(coro) -> result

    Examples:
        with async_context() as execute:
            result1 = execute(async_func1())
            result2 = execute(async_func2())
            # Both results available, cleanup happens automatically

    Note:
        This creates a single event loop for all operations in the context,
        which is more efficient than multiple run_async() calls.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def executor(coro: Coroutine[Any, Any, T]) -> T:
        """Execute coroutine in the context's event loop."""
        return loop.run_until_complete(coro)

    try:
        yield executor
    finally:
        try:
            # Cancel all pending tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()

            # Wait for all tasks to complete
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        finally:
            loop.close()


class AsyncRunner:
    """Reusable async runner for multiple coroutines.

    Use this when you need to run multiple async operations from sync code
    without creating a new event loop each time.

    Examples:
        runner = AsyncRunner()

        result1 = runner.run(async_func1())
        result2 = runner.run(async_func2())

        runner.cleanup()  # Or use context manager

        # Context manager (recommended)
        with AsyncRunner() as runner:
            result = runner.run(async_func())
            # Automatic cleanup
    """

    def __init__(self, debug: bool = False):
        """Initialize async runner.

        Args:
            debug: Enable debug mode for event loop
        """
        self.debug = debug
        self._loop: asyncio.AbstractEventLoop | None = None

    def _ensure_loop(self) -> asyncio.AbstractEventLoop:
        """Ensure event loop exists."""
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.set_debug(self.debug)
        return self._loop

    def run(self, coro: Coroutine[Any, Any, T]) -> T:
        """Run a coroutine.

        Args:
            coro: Coroutine to execute

        Returns:
            The return value of the coroutine
        """
        loop = self._ensure_loop()
        return loop.run_until_complete(coro)

    def cleanup(self) -> None:
        """Clean up event loop and resources."""
        if self._loop and not self._loop.is_closed():
            # Cancel pending tasks
            pending = asyncio.all_tasks(self._loop)
            for task in pending:
                task.cancel()

            # Wait for cancellation
            if pending:
                self._loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

            self._loop.close()
            self._loop = None

    def __enter__(self):
        """Context manager entry."""
        self._ensure_loop()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
        return False


# Convenience functions for common patterns


def run_async_safe(
    coro: Coroutine[Any, Any, T],
    default: T | None = None,
) -> T | None:
    """Run async coroutine with exception handling.

    If the coroutine raises an exception, returns the default value
    instead of propagating the exception.

    Args:
        coro: Coroutine to execute
        default: Default value to return on exception

    Returns:
        Coroutine result or default value

    Examples:
        # Won't raise exception, returns None on error
        result = run_async_safe(risky_async_operation())

        # Return specific default
        result = run_async_safe(async_get_data(), default=[])
    """
    try:
        return run_async(coro)
    except Exception as e:
        logger.warning(
            "async_operation_failed_safely",
            error=str(e),
            error_type=type(e).__name__,
            default=default,
        )
        return default


def run_async_timeout(
    coro: Coroutine[Any, Any, T],
    timeout: float,
    default: T | None = None,
) -> T | None:
    """Run async coroutine with timeout.

    Args:
        coro: Coroutine to execute
        timeout: Timeout in seconds
        default: Default value to return on timeout

    Returns:
        Coroutine result or default value on timeout

    Raises:
        asyncio.TimeoutError: If timeout occurs and no default provided

    Examples:
        # Timeout after 5 seconds
        result = run_async_timeout(slow_operation(), timeout=5.0)

        # Return default on timeout
        result = run_async_timeout(
            slow_operation(),
            timeout=5.0,
            default="timeout occurred"
        )
    """

    async def _with_timeout():
        return await asyncio.wait_for(coro, timeout=timeout)

    try:
        return run_async(_with_timeout())
    except TimeoutError:
        if default is not None:
            logger.warning(
                "async_operation_timeout",
                timeout=timeout,
                default=default,
            )
            return default
        raise
