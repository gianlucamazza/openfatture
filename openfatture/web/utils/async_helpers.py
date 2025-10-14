"""Async/await bridge utilities for Streamlit.

Streamlit runs in a synchronous context, but many OpenFatture services
(especially AI agents) use async/await. These utilities bridge the gap.
"""

import asyncio
from collections.abc import AsyncGenerator, Coroutine
from typing import Any, TypeVar

T = TypeVar("T")


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """
    Execute an async coroutine in a synchronous context.

    Creates a new event loop, runs the coroutine, and cleans up.
    Use this for one-off async operations in Streamlit.

    Args:
        coro: The coroutine to execute

    Returns:
        The coroutine's return value

    Example:
        >>> result = run_async(some_async_function())
    """
    try:
        # Try to get the existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running (nested calls), create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        # No event loop, create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(coro)
    finally:
        # Only close if we created it
        if not loop.is_running():
            try:
                loop.close()
            except Exception:
                pass


async def async_generator_to_list(agen: AsyncGenerator[T, None]) -> list[T]:
    """
    Consume an async generator and return all items as a list.

    Args:
        agen: The async generator to consume

    Returns:
        List of all yielded items

    Example:
        >>> items = await async_generator_to_list(stream_results())
    """
    result: list[T] = []
    async for item in agen:
        result.append(item)
    return result


def run_async_generator(agen: AsyncGenerator[T, None]) -> list[T]:
    """
    Execute an async generator in a synchronous context and return all items.

    Args:
        agen: The async generator to execute

    Returns:
        List of all yielded items

    Example:
        >>> chunks = run_async_generator(agent.execute_stream(context))
    """
    return run_async(async_generator_to_list(agen))
