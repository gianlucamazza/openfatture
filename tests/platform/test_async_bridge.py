"""The async->sync bridge: one strategy for callers with and without a running loop."""

import asyncio
import contextvars
import threading
import time

import pytest

from openfatture.platform.async_bridge import is_async_context, run_async

request_id: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="unset")


async def _loop_identity() -> tuple[int, str]:
    await asyncio.sleep(0)
    return id(asyncio.get_running_loop()), threading.current_thread().name


async def _fail() -> None:
    await asyncio.sleep(0)
    raise ValueError("test error")


async def _read_and_set_context() -> str:
    seen = request_id.get()
    request_id.set("changed-inside")
    return seen


class TestIsAsyncContext:
    def test_not_in_async_context(self) -> None:
        assert is_async_context() is False

    def test_in_async_context(self) -> None:
        async def probe() -> bool:
            return is_async_context()

        assert asyncio.run(probe()) is True


class TestWithoutRunningLoop:
    def test_returns_result_on_the_calling_thread(self) -> None:
        _, thread = run_async(_loop_identity())
        assert thread == threading.current_thread().name

    def test_coroutine_with_arguments(self) -> None:
        async def add(a: int, b: int) -> int:
            await asyncio.sleep(0.001)
            return a + b

        assert run_async(add(5, 3)) == 8

    def test_exception_propagates(self) -> None:
        with pytest.raises(ValueError, match="test error"):
            run_async(_fail())

    def test_context_is_copied_in_and_not_leaked_out(self) -> None:
        token = request_id.set("caller")
        try:
            assert run_async(_read_and_set_context()) == "caller"
            assert request_id.get() == "caller"
        finally:
            request_id.reset(token)

    def test_sequential_calls_leave_no_loop_behind(self) -> None:
        assert [run_async(asyncio.sleep(0, result=n)) for n in range(3)] == [0, 1, 2]
        with pytest.raises(RuntimeError):
            asyncio.get_running_loop()

    def test_debug_mode(self) -> None:
        async def debug_flag() -> bool:
            return asyncio.get_running_loop().get_debug()

        assert run_async(debug_flag(), debug=True) is True
        assert run_async(debug_flag()) is False


class TestInsideRunningLoop:
    def test_runs_on_a_separate_loop_and_thread(self) -> None:
        async def caller() -> tuple[tuple[int, str], int, str]:
            inner = run_async(_loop_identity())
            return inner, id(asyncio.get_running_loop()), threading.current_thread().name

        (inner_loop, inner_thread), outer_loop, outer_thread = asyncio.run(caller())
        assert inner_loop != outer_loop
        assert inner_thread != outer_thread
        assert inner_thread.startswith("async-bridge")

    def test_exception_propagates(self) -> None:
        async def caller() -> None:
            run_async(_fail())

        with pytest.raises(ValueError, match="test error"):
            asyncio.run(caller())

    def test_context_is_copied_in_and_not_leaked_out(self) -> None:
        async def caller() -> tuple[str, str]:
            request_id.set("outer-task")
            seen = run_async(_read_and_set_context())
            return seen, request_id.get()

        assert asyncio.run(caller()) == ("outer-task", "outer-task")

    def test_nested_bridges(self) -> None:
        async def inner() -> str:
            return "inner"

        async def middle() -> str:
            return "middle-" + run_async(inner())

        async def caller() -> str:
            return run_async(middle())

        assert asyncio.run(caller()) == "middle-inner"

    def test_timeout_cancels_the_coroutine(self) -> None:
        cancelled = threading.Event()

        async def slow() -> None:
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                cancelled.set()
                raise

        async def caller() -> None:
            run_async(slow(), timeout=0.01)

        with pytest.raises(TimeoutError):
            asyncio.run(caller())
        assert cancelled.is_set()


class TestTimeout:
    def test_completes_before_timeout(self) -> None:
        async def fast() -> str:
            await asyncio.sleep(0.001)
            return "done"

        assert run_async(fast(), timeout=1.0) == "done"

    def test_timeout_raises_and_cancels(self) -> None:
        cancelled = False

        async def slow() -> None:
            nonlocal cancelled
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                cancelled = True
                raise

        start = time.monotonic()
        with pytest.raises(TimeoutError):
            run_async(slow(), timeout=0.01)
        assert cancelled
        assert time.monotonic() - start < 5

    def test_exception_inside_timeout_propagates(self) -> None:
        with pytest.raises(ValueError, match="test error"):
            run_async(_fail(), timeout=1.0)


class TestThreads:
    def test_run_async_from_multiple_threads(self) -> None:
        async def task(n: int) -> int:
            await asyncio.sleep(0.001)
            return n * 2

        results: list[int | None] = [None] * 5

        def worker(index: int) -> None:
            results[index] = run_async(task(index))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert results == [0, 2, 4, 6, 8]
