"""Session manager for persistent chat sessions."""

import json
from pathlib import Path
from typing import Optional

from openfatture.ai.session.models import ChatSession, SessionStatus
from openfatture.utils.config import get_settings
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class SessionManager:
    """
    Manages chat session persistence and lifecycle.

    Features:
    - JSON-based persistence in user data directory
    - Auto-save on message add
    - Session listing and search
    - Archive and cleanup
    - Safe file operations with validation

    Sessions are stored in: ~/.openfatture/sessions/
    Format: {session_id}.json
    """

    def __init__(self, sessions_dir: Optional[Path] = None) -> None:
        """
        Initialize session manager.

        Args:
            sessions_dir: Custom sessions directory (uses default if None)
        """
        if sessions_dir:
            self.sessions_dir = sessions_dir
        else:
            # Use data_dir from settings
            settings = get_settings()
            self.sessions_dir = settings.data_dir / "sessions"

        # Ensure directory exists
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        logger.info("session_manager_initialized", sessions_dir=str(self.sessions_dir))

    def save_session(self, session: ChatSession) -> bool:
        """
        Save session to disk.

        Args:
            session: Session to save

        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate session ID (security)
            if not self._is_valid_session_id(session.id):
                logger.error("invalid_session_id", session_id=session.id)
                return False

            # Build file path
            file_path = self._get_session_path(session.id)

            # Export to JSON
            data = session.export_json()

            # Write to file (atomic write with temp file)
            temp_path = file_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Atomic rename
            temp_path.replace(file_path)

            logger.debug(
                "session_saved",
                session_id=session.id,
                messages=len(session.messages),
                file_path=str(file_path),
            )

            return True

        except Exception as e:
            logger.error(
                "session_save_failed",
                session_id=session.id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

    def load_session(self, session_id: str) -> Optional[ChatSession]:
        """
        Load session from disk.

        Args:
            session_id: Session ID to load

        Returns:
            ChatSession if found, None otherwise
        """
        try:
            # Validate session ID
            if not self._is_valid_session_id(session_id):
                logger.error("invalid_session_id", session_id=session_id)
                return None

            # Build file path
            file_path = self._get_session_path(session_id)

            if not file_path.exists():
                logger.warning("session_not_found", session_id=session_id)
                return None

            # Load JSON
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            # Create session from data
            session = ChatSession.from_json(data)

            logger.info(
                "session_loaded",
                session_id=session_id,
                messages=len(session.messages),
                title=session.metadata.title,
            )

            return session

        except Exception as e:
            logger.error(
                "session_load_failed",
                session_id=session_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return None

    def delete_session(self, session_id: str, permanent: bool = False) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session to delete
            permanent: If True, delete file immediately. If False, mark as deleted.

        Returns:
            True if successful
        """
        try:
            if permanent:
                # Delete file
                file_path = self._get_session_path(session_id)
                if file_path.exists():
                    file_path.unlink()
                    logger.info("session_deleted_permanent", session_id=session_id)
                return True
            else:
                # Soft delete - mark as deleted
                session = self.load_session(session_id)
                if session:
                    session.delete()
                    self.save_session(session)
                    logger.info("session_deleted_soft", session_id=session_id)
                    return True
                return False

        except Exception as e:
            logger.error(
                "session_delete_failed",
                session_id=session_id,
                error=str(e),
            )
            return False

    def list_sessions(
        self,
        status: Optional[SessionStatus] = None,
        limit: Optional[int] = None,
    ) -> list[ChatSession]:
        """
        List all sessions.

        Args:
            status: Filter by status (None = all except deleted)
            limit: Maximum number of sessions to return

        Returns:
            List of sessions, sorted by last update (newest first)
        """
        sessions = []

        try:
            # Find all JSON files
            for file_path in self.sessions_dir.glob("*.json"):
                try:
                    # Load session
                    with open(file_path, encoding="utf-8") as f:
                        data = json.load(f)

                    session = ChatSession.from_json(data)

                    # Filter by status
                    if status is None and session.status == SessionStatus.DELETED:
                        continue  # Skip deleted by default
                    elif status is not None and session.status != status:
                        continue

                    sessions.append(session)

                except Exception as e:
                    logger.warning(
                        "session_load_error_during_list",
                        file=file_path.name,
                        error=str(e),
                    )
                    continue

            # Sort by last update (newest first)
            sessions.sort(
                key=lambda s: s.metadata.updated_at,
                reverse=True,
            )

            # Apply limit
            if limit:
                sessions = sessions[:limit]

            logger.debug("sessions_listed", count=len(sessions), status=status)

        except Exception as e:
            logger.error("list_sessions_failed", error=str(e))

        return sessions

    def get_recent_sessions(self, limit: int = 10) -> list[ChatSession]:
        """
        Get most recent active sessions.

        Args:
            limit: Maximum number of sessions

        Returns:
            List of recent sessions
        """
        return self.list_sessions(status=SessionStatus.ACTIVE, limit=limit)

    def search_sessions(self, query: str, limit: int = 20) -> list[ChatSession]:
        """
        Search sessions by title or content.

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

    def archive_old_sessions(self, days_old: int = 30) -> int:
        """
        Archive sessions older than specified days.

        Args:
            days_old: Number of days of inactivity

        Returns:
            Number of sessions archived
        """
        from datetime import datetime, timedelta

        cutoff_date = datetime.now() - timedelta(days=days_old)
        archived_count = 0

        for session in self.list_sessions(status=SessionStatus.ACTIVE):
            if session.metadata.updated_at < cutoff_date:
                session.archive()
                if self.save_session(session):
                    archived_count += 1

        logger.info("sessions_archived", count=archived_count, days_old=days_old)
        return archived_count

    def cleanup_deleted(self) -> int:
        """
        Permanently delete sessions marked as deleted.

        Returns:
            Number of sessions deleted
        """
        deleted_count = 0

        for session in self.list_sessions(status=SessionStatus.DELETED):
            if self.delete_session(session.id, permanent=True):
                deleted_count += 1

        logger.info("deleted_sessions_cleaned_up", count=deleted_count)
        return deleted_count

    def get_stats(self) -> dict[str, int]:
        """
        Get statistics about sessions.

        Returns:
            Dictionary with stats
        """
        all_sessions = self.list_sessions()

        stats = {
            "total": len(all_sessions),
            "active": sum(1 for s in all_sessions if s.status == SessionStatus.ACTIVE),
            "archived": sum(1 for s in all_sessions if s.status == SessionStatus.ARCHIVED),
            "deleted": sum(1 for s in all_sessions if s.status == SessionStatus.DELETED),
        }

        return stats

    def export_session(
        self,
        session_id: str,
        format: str = "markdown",
        output_path: Optional[Path] = None,
    ) -> Optional[str]:
        """
        Export session to file.

        Args:
            session_id: Session to export
            format: Export format ("markdown" or "json")
            output_path: Custom output path (uses default if None)

        Returns:
            Path to exported file, or None if failed
        """
        session = self.load_session(session_id)
        if not session:
            return None

        try:
            if format == "markdown":
                content = session.export_markdown()
                extension = ".md"
            elif format == "json":
                content = json.dumps(session.export_json(), indent=2, ensure_ascii=False)
                extension = ".json"
            else:
                logger.error("invalid_export_format", format=format)
                return None

            # Determine output path
            if output_path is None:
                filename = f"{session.metadata.title.replace(' ', '_')}_{session_id[:8]}{extension}"
                output_path = Path.cwd() / filename

            # Write file
            output_path.write_text(content, encoding="utf-8")

            logger.info(
                "session_exported",
                session_id=session_id,
                format=format,
                path=str(output_path),
            )

            return str(output_path)

        except Exception as e:
            logger.error(
                "session_export_failed",
                session_id=session_id,
                error=str(e),
            )
            return None

    # Private helper methods

    def _get_session_path(self, session_id: str) -> Path:
        """Get file path for a session."""
        return self.sessions_dir / f"{session_id}.json"

    def _is_valid_session_id(self, session_id: str) -> bool:
        """
        Validate session ID for security.

        Prevents path traversal attacks by ensuring ID contains only
        safe characters.

        Args:
            session_id: Session ID to validate

        Returns:
            True if valid
        """
        if not session_id:
            return False

        # Allow only alphanumeric and hyphens (UUID format)
        if not all(c.isalnum() or c == "-" for c in session_id):
            return False

        # Reasonable length check
        if len(session_id) > 100:
            return False

        return True
