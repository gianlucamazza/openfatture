"""Run a coroutine to completion from synchronous code.

One strategy, chosen by whether the calling thread already runs an event loop:

- no running loop: ``asyncio.run`` on a fresh loop;
- running loop (an async caller, a notebook, an async test runner): the
  coroutine runs on its own fresh loop in a dedicated worker thread while the
  caller's thread blocks until it finishes. The caller's loop is never
  re-entered.

In both cases the coroutine sees a copy of the caller's context variables,
its exceptions propagate unchanged, and an optional timeout cancels it.
Async callers should prefer ``await``; blocking a running loop stalls every
other task on it.
"""

import asyncio
import contextvars
from collections.abc import Coroutine
from concurrent.futures import ThreadPoolExecutor
from typing import Any

__all__ = ["is_async_context", "run_async"]


def is_async_context() -> bool:
    """Return True when the current thread is running an event loop."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return False
    return True


def run_async[T](
    coro: Coroutine[Any, Any, T],
    *,
    timeout: float | None = None,
    debug: bool = False,
) -> T:
    """Run ``coro`` to completion and return its result.

    Args:
        coro: Coroutine to execute.
        timeout: Seconds after which the coroutine is cancelled and
            ``TimeoutError`` is raised; ``None`` waits indefinitely.
        debug: Run the event loop in asyncio debug mode.

    Raises:
        Whatever the coroutine raises, or ``TimeoutError`` on timeout.
    """
    main = coro if timeout is None else _with_timeout(coro, timeout)
    if not is_async_context():
        return asyncio.run(main, debug=debug)
    return _run_in_worker_thread(main, debug=debug)


async def _with_timeout[T](coro: Coroutine[Any, Any, T], timeout: float) -> T:
    async with asyncio.timeout(timeout):
        return await coro


def _run_in_worker_thread[T](coro: Coroutine[Any, Any, T], *, debug: bool) -> T:
    """Run ``coro`` on a fresh loop in a dedicated thread, in a copy of this context."""
    context = contextvars.copy_context()
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="async-bridge") as executor:
        future = executor.submit(context.run, asyncio.run, coro, debug=debug)
        return future.result()
