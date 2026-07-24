"""Factory for creating the CLI session store.

OpenFatture uses file-backed session persistence for CLI and interactive
terminal workflows. One backend keeps session behavior predictable.

Design Rationale (2025 Best Practices):
- Factory pattern for dependency injection
- File storage for robustness
- Type-safe with proper annotations

Example:
    store = get_session_store()
    store = get_session_store(sessions_dir=Path(".sessions"))
"""

from __future__ import annotations

from pathlib import Path

from openfatture.ai.session.file_store import FileSessionStore
from openfatture.ai.session.store import SessionStore
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


def get_session_store(sessions_dir: Path | None = None) -> SessionStore:
    """Return a file-backed session store.

    Args:
        sessions_dir: Custom sessions directory for file storage

    Returns:
        FileSessionStore instance

    Example:
        >>> # Default CLI store
        >>> store = get_session_store()
        >>>
        >>> # Custom location
        >>> store = get_session_store(sessions_dir=Path(".sessions"))
    """
    file_store = FileSessionStore(sessions_dir=sessions_dir)
    logger.debug("session_store_created", type="file", sessions_dir=str(file_store.sessions_dir))
    return file_store


__all__ = ["get_session_store"]
