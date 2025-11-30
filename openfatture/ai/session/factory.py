"""Factory for creating context-appropriate session stores.

Automatically detects execution context (CLI vs Streamlit) and returns
the appropriate SessionStore implementation. Enables write-once code
that works seamlessly in both environments.

Design Rationale (2025 Best Practices):
- Factory pattern for dependency injection
- Context detection via runtime introspection
- Fallback to file storage for robustness
- Environment variable override for testing
- Type-safe with proper annotations

Example:
    # Auto-detect context
    store = get_session_store()  # FileSessionStore in CLI, StreamlitSessionStore in web

    # Force specific backend
    store = get_session_store(force="file")
    store = get_session_store(force="streamlit")

    # Hybrid storage (memory + persistence)
    store = get_session_store(enable_persistence=True)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from openfatture.ai.session.file_store import FileSessionStore
from openfatture.ai.session.store import SessionStore
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)

StoreType = Literal["file", "streamlit", "auto"]


def _is_streamlit_context() -> bool:
    """Detect if running in Streamlit context.

    Returns:
        True if Streamlit is available and initialized, False otherwise
    """
    try:
        import streamlit as st
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        # Try to access session_state (will fail if not in app context)
        _ = st.session_state

        # Also check for script run context (ensures we're in actual Streamlit runtime)
        ctx = get_script_run_ctx()
        return ctx is not None

    except (ImportError, RuntimeError, AttributeError):
        return False


def get_session_store(
    store_type: StoreType = "auto",
    sessions_dir: Path | None = None,
    enable_persistence: bool = False,
) -> SessionStore:
    """Get session store based on context detection or explicit type.

    Factory function that returns the appropriate SessionStore implementation:
    - **CLI context**: FileSessionStore (JSON persistence)
    - **Streamlit context**: StreamlitSessionStore (in-memory)
    - **Hybrid mode**: StreamlitSessionStore with FileSessionStore fallback

    Context Detection Logic:
    1. Check environment variable OPENFATTURE_SESSION_STORE (override)
    2. Check store_type parameter
    3. Auto-detect Streamlit context
    4. Fallback to FileSessionStore

    Args:
        store_type: Store type ("file", "streamlit", "auto")
        sessions_dir: Custom sessions directory for file storage
        enable_persistence: Enable hybrid mode (memory + disk)

    Returns:
        SessionStore instance appropriate for context

    Example:
        >>> # Auto-detect (recommended)
        >>> store = get_session_store()
        >>>
        >>> # Explicit type
        >>> store = get_session_store(store_type="file")
        >>>
        >>> # Hybrid mode (best of both worlds)
        >>> store = get_session_store(enable_persistence=True)
    """
    # Check environment variable override
    env_store_type = os.getenv("OPENFATTURE_SESSION_STORE", "").lower()
    if env_store_type in ("file", "streamlit"):
        store_type = env_store_type  # type: ignore

    # Auto-detect if requested
    if store_type == "auto":
        if _is_streamlit_context():
            store_type = "streamlit"
            logger.debug("context_detected", type="streamlit")
        else:
            store_type = "file"
            logger.debug("context_detected", type="file")

    # Create appropriate store
    if store_type == "streamlit":
        from openfatture.ai.session.streamlit_store import StreamlitSessionStore

        if enable_persistence:
            # Hybrid mode: memory + file fallback
            file_store = FileSessionStore(sessions_dir=sessions_dir)
            streamlit_store = StreamlitSessionStore(persistent_fallback=file_store)
            logger.info("session_store_created", type="streamlit", mode="hybrid")
            return streamlit_store
        else:
            # Pure in-memory
            streamlit_store = StreamlitSessionStore()
            logger.info("session_store_created", type="streamlit", mode="memory")
            return streamlit_store

    else:  # file
        file_store = FileSessionStore(sessions_dir=sessions_dir)
        logger.info("session_store_created", type="file", sessions_dir=str(file_store.sessions_dir))
        return file_store


def get_default_store() -> SessionStore:
    """Get default session store with auto-detection.

    Convenience function equivalent to get_session_store(store_type="auto").

    Returns:
        Auto-detected SessionStore instance
    """
    return get_session_store(store_type="auto")


__all__ = [
    "get_session_store",
    "get_default_store",
    "StoreType",
]
