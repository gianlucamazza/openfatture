"""Caching utilities for Streamlit web app.

Provides specialized cache decorators and helpers for OpenFatture data.
"""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

import streamlit as st

T = TypeVar("T")


def get_db_session() -> Any:
    """
    Get or create database session from Streamlit session_state.

    Uses singleton pattern to ensure one session per Streamlit session.

    Returns:
        SQLAlchemy session instance
    """
    if "db_session" not in st.session_state:
        from openfatture.storage.database.base import get_session

        st.session_state.db_session = get_session()

    return st.session_state.db_session


def clear_db_session() -> None:
    """
    Close and clear database session from session_state.

    Call this when you need to force a session refresh.
    """
    if "db_session" in st.session_state:
        try:
            st.session_state.db_session.close()
        except Exception:
            pass
        del st.session_state.db_session


def cache_for_session[T](func: Callable[..., T]) -> Callable[..., T]:
    """
    Cache function result for the duration of the Streamlit session.

    Unlike @st.cache_data, this cache persists across reruns but is
    cleared when the session ends (browser refresh/close).

    Args:
        func: Function to cache

    Returns:
        Wrapped function with session-level caching

    Example:
        >>> @cache_for_session
        ... def expensive_computation(x):
        ...     return x ** 2
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        # Create cache key from function name and args
        cache_key = f"_cache_{func.__name__}_{args}_{kwargs}"

        if cache_key not in st.session_state:
            st.session_state[cache_key] = func(*args, **kwargs)

        return st.session_state[cache_key]

    return wrapper


def invalidate_cache(func_name: str) -> None:
    """
    Invalidate all cached results for a specific function.

    Args:
        func_name: Name of the function whose cache to clear

    Example:
        >>> invalidate_cache("get_invoices")
    """
    keys_to_remove = [key for key in st.session_state if key.startswith(f"_cache_{func_name}_")]
    for key in keys_to_remove:
        del st.session_state[key]


def invalidate_all_caches() -> None:
    """Clear all function caches from session state."""
    keys_to_remove = [key for key in st.session_state if key.startswith("_cache_")]
    for key in keys_to_remove:
        del st.session_state[key]
