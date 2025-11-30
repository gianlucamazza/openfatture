"""Session store abstraction for unified persistence across CLI and Web UI.

This module provides a storage-agnostic interface for chat session persistence,
enabling seamless switching between file-based storage (CLI) and in-memory
storage (Streamlit web UI) following the Strategy pattern.

Design Rationale (2025 Best Practices):
- Abstract base class defines contract (no implementation details)
- Adapter pattern for different storage backends
- Type-safe interfaces with proper return types
- Context detection for automatic backend selection
- Fail-safe operations (return None/False vs raising exceptions)

Example:
    # Auto-detect context (CLI vs Streamlit)
    store = get_session_store()

    # Or explicit backend
    store = FileSessionStore()
    store = StreamlitSessionStore()

    # Unified interface
    session = store.load("session-id")
    store.save(session)
    sessions = store.list_sessions(status=SessionStatus.ACTIVE)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from openfatture.ai.session.models import ChatSession, SessionStatus


class SessionStore(ABC):
    """Abstract base class for session storage backends.

    Defines the contract that all storage implementations must follow.
    Implementations should handle errors gracefully and return None/False
    rather than raising exceptions for user-facing operations.

    Methods:
        save: Persist a session
        load: Retrieve a session by ID
        delete: Remove a session (soft or permanent)
        list_sessions: Get all sessions with filtering
        exists: Check if session exists
        get_stats: Get storage statistics
    """

    @abstractmethod
    def save(self, session: ChatSession) -> bool:
        """Save a session to storage.

        Args:
            session: Session to persist

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def load(self, session_id: str) -> ChatSession | None:
        """Load a session from storage.

        Args:
            session_id: Session ID to load

        Returns:
            ChatSession if found, None otherwise
        """
        pass

    @abstractmethod
    def delete(self, session_id: str, permanent: bool = False) -> bool:
        """Delete a session.

        Args:
            session_id: Session to delete
            permanent: If True, permanently delete. If False, soft delete.

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def list_sessions(
        self,
        status: SessionStatus | None = None,
        limit: int | None = None,
    ) -> list[ChatSession]:
        """List sessions with optional filtering.

        Args:
            status: Filter by status (None = all except deleted)
            limit: Maximum number of sessions to return

        Returns:
            List of sessions sorted by last update (newest first)
        """
        pass

    @abstractmethod
    def exists(self, session_id: str) -> bool:
        """Check if a session exists.

        Args:
            session_id: Session ID to check

        Returns:
            True if exists, False otherwise
        """
        pass

    @abstractmethod
    def get_stats(self) -> dict[str, int]:
        """Get storage statistics.

        Returns:
            Dictionary with stats (total, active, archived, deleted)
        """
        pass

    # Optional convenience methods with default implementations

    def get_recent_sessions(self, limit: int = 10) -> list[ChatSession]:
        """Get most recent active sessions.

        Args:
            limit: Maximum number of sessions

        Returns:
            List of recent sessions
        """
        return self.list_sessions(status=SessionStatus.ACTIVE, limit=limit)

    def search_sessions(self, query: str, limit: int = 20) -> list[ChatSession]:
        """Search sessions by title or content.

        Default implementation does simple filtering. Subclasses can
        override for more sophisticated search (full-text, fuzzy, etc.).

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching sessions
        """
        query_lower = query.lower()
        matching = []

        for session in self.list_sessions():
            # Search in title
            if query_lower in session.metadata.title.lower():
                matching.append(session)
                continue

            # Search in messages
            for msg in session.messages:
                if query_lower in msg.content.lower():
                    matching.append(session)
                    break

        return matching[:limit]

    def export_session(
        self,
        session_id: str,
        format: str = "markdown",
        output_path: Path | None = None,
    ) -> str | None:
        """Export session to file.

        Args:
            session_id: Session to export
            format: Export format ("markdown" or "json")
            output_path: Custom output path

        Returns:
            Path to exported file, or None if failed
        """
        session = self.load(session_id)
        if not session:
            return None

        try:
            import json

            if format == "markdown":
                content = session.export_markdown()
                extension = ".md"
            elif format == "json":
                content = json.dumps(session.export_json(), indent=2, ensure_ascii=False)
                extension = ".json"
            else:
                return None

            # Determine output path
            if output_path is None:
                filename = f"{session.metadata.title.replace(' ', '_')}_{session_id[:8]}{extension}"
                output_path = Path.cwd() / filename

            # Write file
            output_path.write_text(content, encoding="utf-8")
            return str(output_path)

        except Exception:
            return None


__all__ = ["SessionStore"]
