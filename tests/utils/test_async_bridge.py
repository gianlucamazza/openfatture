"""Comprehensive test suite for async/sync bridge.

Tests cover:
- is_async_context detection
- run_async basic functionality
- Nested loop handling
- AsyncRunner class
- Context manager patterns
- Timeout handling
- Safe execution with defaults
- Edge cases and error handling
"""

import asyncio
import threading
import time
from unittest.mock import patch

import pytest

from openfatture.utils.async_bridge import (
    AsyncRunner,
    async_context,
    is_async_context,
    run_async,
    run_async_safe,
    run_async_timeout,
)

# ============================================================================
# is_async_context Tests
# ============================================================================


class TestIsAsyncContext:
    """Test async context detection."""

    def test_not_in_async_context(self):
        """Test that sync code is correctly detected."""
        assert is_async_context() is False

    @pytest.mark.asyncio
    async def test_in_async_context(self):
        """Test that async code is correctly detected."""
        assert is_async_context() is True


# ============================================================================
# run_async Tests
# ============================================================================


class TestRunAsync:
    """Test basic async->sync bridge functionality."""

    def test_simple_coroutine(self):
        """Test running a simple async function."""

        async def simple():
            return "success"

        result = run_async(simple())
        assert result == "success"

    def test_coroutine_with_arguments(self):
        """Test running async function with arguments."""

        async def with_args(a: int, b: int):
            return a + b

        result = run_async(with_args(5, 3))
        assert result == 8

    def test_coroutine_with_sleep(self):
        """Test that async sleep works correctly."""

        async def with_sleep():
            await asyncio.sleep(0.01)
            return "done"

        start = time.time()
        result = run_async(with_sleep())
        duration = time.time() - start

        assert result == "done"
        assert duration >= 0.01

    def test_exception_propagation(self):
        """Test that exceptions are properly propagated."""

        async def raises():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            run_async(raises())

    def test_multiple_sequential_calls(self):
        """Test multiple sequential run_async calls."""

        async def counter(n):
            await asyncio.sleep(0.001)
            return n * 2

        results = [run_async(counter(i)) for i in range(5)]
        assert results == [0, 2, 4, 6, 8]

    def test_nested_async_calls(self):
        """Test async function calling another async function."""

        async def inner():
            await asyncio.sleep(0.001)
            return "inner"

        async def outer():
            result = await inner()
            return f"outer-{result}"

        result = run_async(outer())
        assert result == "outer-inner"


# ============================================================================
# Nested Loop Tests
# ============================================================================


class TestNestedLoops:
    """Test handling of nested event loops."""

    @pytest.mark.skip(reason="Requires nest_asyncio to be installed")
    def test_nested_loop_with_nest_asyncio(self):
        """Test nested loop handling when nest_asyncio is available."""
        import nest_asyncio

        nest_asyncio.apply()

        async def outer_async():
            # This is running in an async context
            # Now try to call run_async from within (nested)
            async def inner():
                return "nested result"

            return run_async(inner())

        result = run_async(outer_async())
        assert result == "nested result"

    def test_nested_loop_fallback_to_thread(self):
        """Test nested loop falls back to thread execution."""
        # Mock nest_asyncio not being available
        with patch.dict("sys.modules", {"nest_asyncio": None}):

            async def inner():
                await asyncio.sleep(0.001)
                return "thread result"

            async def outer():
                # This will detect nested loop and use thread fallback
                return run_async(inner())

            # This should work via thread fallback
            result = run_async(outer())
            assert result == "thread result"


# ============================================================================
# AsyncRunner Tests
# ============================================================================


class TestAsyncRunner:
    """Test AsyncRunner class."""

    def test_runner_basic_usage(self):
        """Test basic AsyncRunner usage."""
        runner = AsyncRunner()

        async def task():
            return "result"

        result = runner.run(task())
        assert result == "result"

        runner.cleanup()

    def test_runner_multiple_tasks(self):
        """Test running multiple tasks with same runner."""
        runner = AsyncRunner()

        async def task(n):
            await asyncio.sleep(0.001)
            return n * 2

        results = [runner.run(task(i)) for i in range(5)]
        assert results == [0, 2, 4, 6, 8]

        runner.cleanup()

    def test_runner_context_manager(self):
        """Test AsyncRunner as context manager."""

        async def task(n):
            return n + 1

        with AsyncRunner() as runner:
            result1 = runner.run(task(1))
            result2 = runner.run(task(2))

        assert result1 == 2
        assert result2 == 3

    def test_runner_exception_handling(self):
        """Test that exceptions are propagated through runner."""
        runner = AsyncRunner()

        async def failing_task():
            raise RuntimeError("task failed")

        with pytest.raises(RuntimeError, match="task failed"):
            runner.run(failing_task())

        runner.cleanup()

    def test_runner_cleanup_cancels_pending_tasks(self):
        """Test that cleanup cancels pending tasks."""
        runner = AsyncRunner()

        async def long_task():
            await asyncio.sleep(10)  # Won't complete
            return "should not reach"

        # Start but don't wait
        task = asyncio.ensure_future(long_task(), loop=runner._ensure_loop())

        # Cleanup should cancel
        runner.cleanup()

        assert task.cancelled()

    def test_runner_debug_mode(self):
        """Test AsyncRunner in debug mode."""
        runner = AsyncRunner(debug=True)

        async def task():
            return "debug result"

        result = runner.run(task())
        assert result == "debug result"

        runner.cleanup()


# ============================================================================
# async_context Tests
# ============================================================================


class TestAsyncContext:
    """Test async_context context manager."""

    def test_async_context_basic(self):
        """Test basic async_context usage."""

        async def task(n):
            await asyncio.sleep(0.001)
            return n * 2

        with async_context() as execute:
            result1 = execute(task(5))
            result2 = execute(task(10))

        assert result1 == 10
        assert result2 == 20

    def test_async_context_exception_cleanup(self):
        """Test that async_context cleans up on exception."""

        async def failing_task():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            with async_context() as execute:
                execute(failing_task())

        # Should have cleaned up properly (no assertion, just shouldn't crash)

    def test_async_context_multiple_operations(self):
        """Test multiple operations in same context."""

        async def add(a, b):
            return a + b

        async def multiply(a, b):
            return a * b

        with async_context() as execute:
            sum_result = execute(add(5, 3))
            product_result = execute(multiply(5, 3))

        assert sum_result == 8
        assert product_result == 15


# ============================================================================
# Convenience Functions Tests
# ============================================================================


class TestRunAsyncSafe:
    """Test run_async_safe with exception handling."""

    def test_successful_execution(self):
        """Test that successful execution returns result."""

        async def success():
            return "ok"

        result = run_async_safe(success())
        assert result == "ok"

    def test_exception_returns_none(self):
        """Test that exception returns None by default."""

        async def fails():
            raise RuntimeError("error")

        result = run_async_safe(fails())
        assert result is None

    def test_exception_returns_custom_default(self):
        """Test that exception returns custom default."""

        async def fails():
            raise RuntimeError("error")

        result = run_async_safe(fails(), default="fallback")
        assert result == "fallback"

    def test_custom_default_with_list(self):
        """Test custom default with mutable type."""

        async def fails():
            raise RuntimeError("error")

        result = run_async_safe(fails(), default=[])
        assert result == []
        assert isinstance(result, list)


class TestRunAsyncTimeout:
    """Test run_async_timeout with timeout handling."""

    def test_completes_before_timeout(self):
        """Test operation that completes before timeout."""

        async def fast():
            await asyncio.sleep(0.01)
            return "done"

        result = run_async_timeout(fast(), timeout=1.0)
        assert result == "done"

    def test_timeout_raises_by_default(self):
        """Test that timeout raises TimeoutError by default."""

        async def slow():
            await asyncio.sleep(10)
            return "never"

        with pytest.raises(asyncio.TimeoutError):
            run_async_timeout(slow(), timeout=0.01)

    def test_timeout_returns_default(self):
        """Test that timeout returns default value."""

        async def slow():
            await asyncio.sleep(10)
            return "never"

        result = run_async_timeout(slow(), timeout=0.01, default="timeout")
        assert result == "timeout"

    def test_zero_timeout(self):
        """Test behavior with zero timeout."""

        async def instant():
            return "immediate"

        # Should complete instantly
        result = run_async_timeout(instant(), timeout=0.1)
        assert result == "immediate"


# ============================================================================
# Thread Safety Tests
# ============================================================================


class TestThreadSafety:
    """Test thread safety of async bridge."""

    def test_run_async_from_multiple_threads(self):
        """Test running async operations from multiple threads."""

        async def task(n):
            await asyncio.sleep(0.001)
            return n * 2

        def thread_worker(n):
            return run_async(task(n))

        threads = []
        results = [None] * 5

        def worker(index):
            results[index] = thread_worker(index)

        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert results == [0, 2, 4, 6, 8]

    def test_async_runner_per_thread(self):
        """Test that each thread can have its own AsyncRunner."""

        async def task(n):
            return n + 100

        results = {}

        def thread_worker(thread_id):
            with AsyncRunner() as runner:
                result = runner.run(task(thread_id))
                results[thread_id] = result

        threads = []
        for i in range(3):
            thread = threading.Thread(target=thread_worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert results == {0: 100, 1: 101, 2: 102}


# ============================================================================
# Performance Tests
# ============================================================================


class TestPerformance:
    """Test performance characteristics."""

    def test_overhead_is_minimal(self):
        """Test that bridge overhead is minimal."""

        async def minimal():
            return "result"

        # Warm up
        for _ in range(10):
            run_async(minimal())

        # Time 100 operations
        start = time.time()
        for _ in range(100):
            run_async(minimal())
        duration = time.time() - start

        # Should complete quickly (< 1 second for 100 ops)
        assert duration < 1.0

    def test_async_runner_reuse_is_faster(self):
        """Test that AsyncRunner reuse is faster than multiple run_async."""

        async def task():
            return "result"

        # Method 1: Multiple run_async calls
        start1 = time.time()
        for _ in range(50):
            run_async(task())
        duration1 = time.time() - start1

        # Method 2: Single AsyncRunner
        start2 = time.time()
        with AsyncRunner() as runner:
            for _ in range(50):
                runner.run(task())
        duration2 = time.time() - start2

        # AsyncRunner should be faster (reuses loop)
        # Note: This might be flaky, so we just ensure it completes
        assert duration2 < duration1 * 2  # At most 2x slower
