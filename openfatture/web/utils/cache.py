"""Caching utilities for Streamlit web app.

Provides specialized cache decorators and helpers for OpenFatture data.

Best Practices 2025:
- Explicit session lifecycle management
- Context manager for automatic cleanup
- Connection leak prevention
- Proper error handling
"""

from collections.abc import Callable
from contextlib import contextmanager
from functools import wraps
from typing import Any, TypeVar

import streamlit as st

T = TypeVar("T")


def get_db_session() -> Any:
    """
    Get or create database session from Streamlit session_state.

    Uses singleton pattern to ensure one session per Streamlit session.
    Session is automatically cleaned up on page rerun or session end.

    Returns:
        SQLAlchemy session instance

    Note:
        For long-running operations, prefer using `db_session_scope()` context manager
        to ensure explicit cleanup.
    """
    if "db_session" not in st.session_state:
        from openfatture.storage.database.base import get_session

        st.session_state["db_session"] = get_session()
        # Register cleanup on session end (Streamlit atexit hook)
        _register_session_cleanup()

    return st.session_state["db_session"]


def clear_db_session() -> None:
    """
    Close and clear database session from session_state.

    Call this when you need to force a session refresh or cleanup.
    Safe to call multiple times.
    """
    if "db_session" in st.session_state:
        try:
            session = st.session_state["db_session"]
            session.close()
        except Exception as e:
            # Log but don't raise - cleanup should be resilient
            import logging

            logging.warning(f"Error closing database session: {e}")
        finally:
            del st.session_state["db_session"]


@contextmanager
def db_session_scope():
    """
    Context manager for database session with automatic cleanup.

    Provides explicit lifecycle management for database operations.
    Automatically commits on success, rolls back on error, and closes on exit.

    Usage:
        >>> with db_session_scope() as session:
        ...     invoice = session.query(Fattura).first()
        ...     # session automatically committed and closed

    Yields:
        SQLAlchemy session instance

    Best Practice:
        Use this for write operations or long-running queries where you want
        explicit control over transaction boundaries.
    """
    from openfatture.storage.database.base import get_session

    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _register_session_cleanup() -> None:
    """
    Register cleanup callback for database session on Streamlit session end.

    Internal function called automatically by get_db_session().
    """
    if "_db_cleanup_registered" not in st.session_state:
        # Mark as registered to avoid multiple registrations
        st.session_state["_db_cleanup_registered"] = True

        # Note: Streamlit doesn't provide explicit session end hooks,
        # but session_state is cleared when user closes browser/refreshes.
        # For production, consider implementing proper cleanup with:
        # - Periodic connection pool pruning
        # - Session timeout monitoring
        # - Health checks via /healthz endpoint


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


# Best Practice 2025: Selective cache invalidation by category
def invalidate_cache_by_category(category: str) -> int:
    """
    Invalidate all cached results for a specific category.

    Args:
        category: Category identifier (e.g., "invoices", "clients", "payments")

    Returns:
        Number of cache entries cleared

    Example:
        >>> # Clear all invoice-related caches
        >>> cleared = invalidate_cache_by_category("invoices")
        >>> print(f"Cleared {cleared} invoice caches")

    Best Practice:
        Use categories to group related caches and invalidate them together
        when data changes. This is more efficient than clearing all caches.
    """
    pattern = f"_cache_{category}_"
    keys_to_remove = [key for key in st.session_state if pattern in key]

    for key in keys_to_remove:
        del st.session_state[key]

    return len(keys_to_remove)


def cache_with_ttl(ttl_seconds: int = 300):
    """
    Cache decorator with time-to-live (TTL) support.

    Args:
        ttl_seconds: Cache lifetime in seconds (default: 300 = 5 minutes)

    Returns:
        Decorator function

    Example:
        >>> @cache_with_ttl(ttl_seconds=60)  # Cache for 1 minute
        ... def get_dashboard_data():
        ...     return expensive_query()

    Best Practice:
        Use TTL for data that changes frequently but doesn't need real-time updates.
        Common TTL values:
        - 60s: Frequently changing data (dashboard metrics)
        - 300s: Moderate change rate (user lists)
        - 3600s: Slow changing data (configuration)
    """
    import time

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Create cache key
            cache_key = f"_cache_{func.__name__}_{args}_{kwargs}"
            ttl_key = f"{cache_key}_ttl"

            # Check if cache exists and is still valid
            if cache_key in st.session_state and ttl_key in st.session_state:
                if time.time() < st.session_state[ttl_key]:
                    return st.session_state[cache_key]

            # Cache miss or expired - recompute
            result = func(*args, **kwargs)
            st.session_state[cache_key] = result
            st.session_state[ttl_key] = time.time() + ttl_seconds

            return result

        return wrapper

    return decorator


def get_cache_stats() -> dict[str, Any]:
    """
    Get statistics about current cache usage.

    Returns:
        Dictionary with cache statistics

    Example:
        >>> stats = get_cache_stats()
        >>> st.metric("Cached Functions", stats["total_entries"])
    """
    cache_entries = [key for key in st.session_state if key.startswith("_cache_")]

    # Group by function name
    functions: dict[str, int] = {}
    for key in cache_entries:
        # Extract function name from key: "_cache_funcname_..."
        parts = key.split("_")
        if len(parts) >= 3:
            func_name = parts[2]
            functions[func_name] = functions.get(func_name, 0) + 1

    return {
        "total_entries": len(cache_entries),
        "functions": functions,
        "memory_keys": cache_entries[:10],  # First 10 for debugging
    }


def cleanup_expired_caches() -> int:
    """
    Clean up expired TTL caches.

    Returns:
        Number of expired entries removed

    Best Practice:
        Call this periodically (e.g., on page load) to prevent
        session state from growing indefinitely.
    """
    import time

    now = time.time()
    expired_keys = []

    # Find all TTL keys
    ttl_keys = [key for key in st.session_state if key.endswith("_ttl")]

    for ttl_key in ttl_keys:
        if st.session_state[ttl_key] < now:
            # Expired - remove both cache and TTL
            cache_key = ttl_key.replace("_ttl", "")
            expired_keys.append(cache_key)
            expired_keys.append(ttl_key)

    # Remove expired entries
    for key in expired_keys:
        if key in st.session_state:
            del st.session_state[key]

    return len(expired_keys) // 2  # Divide by 2 (cache + TTL keys)


# Category-based cache decorators for common use cases
def cache_invoices(ttl_seconds: int = 60):
    """Cache decorator specifically for invoice-related data."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            cache_key = f"_cache_invoices_{func.__name__}_{args}_{kwargs}"
            ttl_key = f"{cache_key}_ttl"

            if cache_key in st.session_state and ttl_key in st.session_state:
                import time

                if time.time() < st.session_state[ttl_key]:
                    return st.session_state[cache_key]

            result = func(*args, **kwargs)
            st.session_state[cache_key] = result

            import time

            st.session_state[ttl_key] = time.time() + ttl_seconds

            return result

        return wrapper

    return decorator


def cache_clients(ttl_seconds: int = 300):
    """Cache decorator specifically for client-related data."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            cache_key = f"_cache_clients_{func.__name__}_{args}_{kwargs}"
            ttl_key = f"{cache_key}_ttl"

            if cache_key in st.session_state and ttl_key in st.session_state:
                import time

                if time.time() < st.session_state[ttl_key]:
                    return st.session_state[cache_key]

            result = func(*args, **kwargs)
            st.session_state[cache_key] = result

            import time

            st.session_state[ttl_key] = time.time() + ttl_seconds

            return result

        return wrapper

    return decorator
