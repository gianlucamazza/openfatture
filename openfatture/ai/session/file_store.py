"""File-based session storage implementation.

Adapter that wraps the existing SessionManager to conform to the
SessionStore interface. Provides persistent storage using JSON files
in the user's data directory (~/.openfatture/sessions/).

Design Rationale (2025 Best Practices):
- Adapter pattern wraps existing SessionManager
- Delegation to proven implementation
- Maintains backward compatibility
- Zero breaking changes to existing code
- Type-safe with explicit return types

Example:
    store = FileSessionStore()
    store.save(session)
    session = store.load("session-id")
    sessions = store.list_sessions(limit=10)
"""

from __future__ import annotations

from pathlib import Path

from openfatture.ai.session.manager import SessionManager
from openfatture.ai.session.models import ChatSession, SessionStatus
from openfatture.ai.session.store import SessionStore
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class FileSessionStore(SessionStore):
    """File-based session storage using JSON persistence.

    Wraps SessionManager to provide the SessionStore interface.
    Sessions are stored as JSON files in ~/.openfatture/sessions/
    with atomic writes and safe file operations.

    Attributes:
        manager: Underlying SessionManager instance
        sessions_dir: Directory containing session files

    Thread Safety:
        File operations use atomic writes (temp file + rename).
        Multiple processes can safely read, but concurrent writes
        to the same session should be avoided.
    """

    def __init__(self, sessions_dir: Path | None = None) -> None:
        """Initialize file-based storage.

        Args:
            sessions_dir: Custom sessions directory (uses default if None)
        """
        self.manager = SessionManager(sessions_dir=sessions_dir)
        self.sessions_dir = self.manager.sessions_dir

        logger.debug("file_session_store_initialized", sessions_dir=str(self.sessions_dir))

    def save(self, session: ChatSession) -> bool:
        """Save session to JSON file.

        Args:
            session: Session to persist

        Returns:
            True if successful, False otherwise
        """
        return self.manager.save_session(session)

    def load(self, session_id: str) -> ChatSession | None:
        """Load session from JSON file.

        Args:
            session_id: Session ID to load

        Returns:
            ChatSession if found, None otherwise
        """
        return self.manager.load_session(session_id)

    def delete(self, session_id: str, permanent: bool = False) -> bool:
        """Delete a session.

        Args:
            session_id: Session to delete
            permanent: If True, delete file. If False, mark as deleted.

        Returns:
            True if successful, False otherwise
        """
        return self.manager.delete_session(session_id, permanent=permanent)

    def list_sessions(
        self,
        status: SessionStatus | None = None,
        limit: int | None = None,
    ) -> list[ChatSession]:
        """List sessions from file system.

        Args:
            status: Filter by status (None = all except deleted)
            limit: Maximum number of sessions

        Returns:
            List of sessions sorted by last update (newest first)
        """
        return self.manager.list_sessions(status=status, limit=limit)

    def exists(self, session_id: str) -> bool:
        """Check if session file exists.

        Args:
            session_id: Session ID to check

        Returns:
            True if file exists, False otherwise
        """
        try:
            # Validate session ID first
            if not self.manager._is_valid_session_id(session_id):
                return False

            file_path = self.manager._get_session_path(session_id)
            return file_path.exists()

        except Exception as e:
            logger.debug("exists_check_failed", session_id=session_id, error=str(e))
            return False

    def get_stats(self) -> dict[str, int]:
        """Get storage statistics.

        Returns:
            Dictionary with total, active, archived, deleted counts
        """
        return self.manager.get_stats()

    # Delegate additional methods to manager

    def get_recent_sessions(self, limit: int = 10) -> list[ChatSession]:
        """Get most recent active sessions.

        Args:
            limit: Maximum number of sessions

        Returns:
            List of recent sessions
        """
        return self.manager.get_recent_sessions(limit=limit)

    def search_sessions(self, query: str, limit: int = 20) -> list[ChatSession]:
        """Search sessions by title or content.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching sessions
        """
        return self.manager.search_sessions(query=query, limit=limit)

    def archive_old_sessions(self, days_old: int = 30) -> int:
        """Archive sessions older than specified days.

        Args:
            days_old: Number of days of inactivity

        Returns:
            Number of sessions archived
        """
        return self.manager.archive_old_sessions(days_old=days_old)

    def cleanup_deleted(self) -> int:
        """Permanently delete sessions marked as deleted.

        Returns:
            Number of sessions deleted
        """
        return self.manager.cleanup_deleted()

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
        return self.manager.export_session(
            session_id=session_id,
            format=format,
            output_path=output_path,
        )


__all__ = ["FileSessionStore"]
