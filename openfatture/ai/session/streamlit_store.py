"""Streamlit session_state-based storage implementation.

In-memory session storage using Streamlit's session_state for fast access
and automatic per-user isolation. Sessions are cleared when the browser
tab closes, making this ideal for ephemeral web UI interactions.

Design Rationale (2025 Best Practices):
- Zero disk I/O for fast read/write
- Automatic per-user isolation via st.session_state
- Browser-tab lifetime (no cleanup needed)
- Graceful degradation when Streamlit not available
- Type-safe implementation with proper error handling

Example:
    # Only works in Streamlit context
    store = StreamlitSessionStore()
    store.save(session)
    session = store.load("session-id")

    # Hybrid storage: memory + optional persistence
    store = StreamlitSessionStore(persistent_fallback=FileSessionStore())
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from openfatture.ai.session.models import ChatSession, SessionStatus
from openfatture.ai.session.store import SessionStore
from openfatture.utils.logging import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)

# Session state key for storing sessions
SESSIONS_KEY = "_openfatture_sessions"


class StreamlitSessionStore(SessionStore):
    """In-memory session storage using Streamlit session_state.

    Stores sessions in st.session_state[SESSIONS_KEY] as a dict
    mapping session_id -> ChatSession. Fast access with zero disk I/O,
    automatically cleared when browser tab closes.

    Attributes:
        persistent_fallback: Optional fallback store for persistence

    Limitations:
        - Only works in Streamlit context (raises error otherwise)
        - Sessions cleared when tab closes (use fallback for persistence)
        - No cross-tab session sharing

    Thread Safety:
        Safe within single Streamlit app instance (one thread per session).
    """

    def __init__(self, persistent_fallback: SessionStore | None = None) -> None:
        """Initialize Streamlit-based storage.

        Args:
            persistent_fallback: Optional fallback store for persistence
                                (e.g., FileSessionStore for hybrid storage)

        Raises:
            RuntimeError: If not running in Streamlit context
        """
        self._persistent_fallback = persistent_fallback
        self._ensure_streamlit_context()
        self._init_sessions_dict()

        logger.debug("streamlit_session_store_initialized", has_fallback=persistent_fallback is not None)

    def _ensure_streamlit_context(self) -> None:
        """Verify we're running in Streamlit context."""
        try:
            import streamlit as st

            # Access session_state to verify context
            _ = st.session_state
        except (ImportError, RuntimeError) as e:
            msg = "StreamlitSessionStore requires Streamlit context"
            logger.error("streamlit_context_missing", error=str(e))
            raise RuntimeError(msg) from e

    def _init_sessions_dict(self) -> None:
        """Initialize sessions dictionary in session_state if needed."""
        import streamlit as st

        if SESSIONS_KEY not in st.session_state:
            st.session_state[SESSIONS_KEY] = {}
            logger.debug("sessions_dict_initialized")

    def _get_sessions_dict(self) -> dict[str, ChatSession]:
        """Get sessions dictionary from session_state."""
        import streamlit as st

        return st.session_state[SESSIONS_KEY]

    def save(self, session: ChatSession) -> bool:
        """Save session to session_state.

        Args:
            session: Session to persist

        Returns:
            True if successful, False otherwise
        """
        try:
            sessions = self._get_sessions_dict()
            sessions[session.id] = session

            # Also save to fallback if configured
            if self._persistent_fallback:
                self._persistent_fallback.save(session)

            logger.debug("session_saved_to_streamlit", session_id=session.id)
            return True

        except Exception as e:
            logger.error(
                "streamlit_session_save_failed",
                session_id=session.id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

    def load(self, session_id: str) -> ChatSession | None:
        """Load session from session_state.

        Args:
            session_id: Session ID to load

        Returns:
            ChatSession if found, None otherwise
        """
        try:
            sessions = self._get_sessions_dict()
            session = sessions.get(session_id)

            # Try fallback if not found in memory
            if session is None and self._persistent_fallback:
                session = self._persistent_fallback.load(session_id)
                if session:
                    # Cache in memory for future access
                    sessions[session_id] = session
                    logger.debug("session_loaded_from_fallback", session_id=session_id)

            if session:
                logger.debug("session_loaded_from_streamlit", session_id=session_id)
            else:
                logger.debug("session_not_found_in_streamlit", session_id=session_id)

            return session

        except Exception as e:
            logger.error(
                "streamlit_session_load_failed",
                session_id=session_id,
                error=str(e),
            )
            return None

    def delete(self, session_id: str, permanent: bool = False) -> bool:
        """Delete a session.

        Args:
            session_id: Session to delete
            permanent: If True, delete from fallback too. If False, soft delete.

        Returns:
            True if successful, False otherwise
        """
        try:
            sessions = self._get_sessions_dict()

            if permanent:
                # Remove from memory
                if session_id in sessions:
                    del sessions[session_id]

                # Remove from fallback
                if self._persistent_fallback:
                    self._persistent_fallback.delete(session_id, permanent=True)

                logger.info("session_deleted_permanent_streamlit", session_id=session_id)
            else:
                # Soft delete - mark as deleted
                if session_id in sessions:
                    sessions[session_id].delete()

                if self._persistent_fallback:
                    self._persistent_fallback.delete(session_id, permanent=False)

                logger.info("session_deleted_soft_streamlit", session_id=session_id)

            return True

        except Exception as e:
            logger.error("streamlit_session_delete_failed", session_id=session_id, error=str(e))
            return False

    def list_sessions(
        self,
        status: SessionStatus | None = None,
        limit: int | None = None,
    ) -> list[ChatSession]:
        """List sessions from session_state.

        Args:
            status: Filter by status (None = all except deleted)
            limit: Maximum number of sessions

        Returns:
            List of sessions sorted by last update (newest first)
        """
        try:
            sessions = self._get_sessions_dict()
            result = []

            for session in sessions.values():
                # Filter by status
                if status is None and session.status == SessionStatus.DELETED:
                    continue  # Skip deleted by default
                elif status is not None and session.status != status:
                    continue

                result.append(session)

            # Sort by last update (newest first)
            result.sort(key=lambda s: s.metadata.updated_at, reverse=True)

            # Apply limit
            if limit:
                result = result[:limit]

            logger.debug("sessions_listed_from_streamlit", count=len(result), status=status)
            return result

        except Exception as e:
            logger.error("streamlit_list_sessions_failed", error=str(e))
            return []

    def exists(self, session_id: str) -> bool:
        """Check if session exists.

        Args:
            session_id: Session ID to check

        Returns:
            True if exists, False otherwise
        """
        try:
            sessions = self._get_sessions_dict()
            return session_id in sessions

        except Exception as e:
            logger.debug("streamlit_exists_check_failed", session_id=session_id, error=str(e))
            return False

    def get_stats(self) -> dict[str, int]:
        """Get storage statistics.

        Returns:
            Dictionary with total, active, archived, deleted counts
        """
        try:
            sessions = list(self._get_sessions_dict().values())

            stats = {
                "total": len(sessions),
                "active": sum(1 for s in sessions if s.status == SessionStatus.ACTIVE),
                "archived": sum(1 for s in sessions if s.status == SessionStatus.ARCHIVED),
                "deleted": sum(1 for s in sessions if s.status == SessionStatus.DELETED),
            }

            return stats

        except Exception:
            return {"total": 0, "active": 0, "archived": 0, "deleted": 0}

    def clear_all(self) -> int:
        """Clear all sessions from memory (Streamlit-specific).

        Returns:
            Number of sessions cleared
        """
        try:
            sessions = self._get_sessions_dict()
            count = len(sessions)
            sessions.clear()

            logger.info("all_sessions_cleared_from_streamlit", count=count)
            return count

        except Exception as e:
            logger.error("clear_all_failed", error=str(e))
            return 0

    def sync_from_fallback(self) -> int:
        """Load all sessions from fallback into memory (Streamlit-specific).

        Useful for initializing memory from persistent storage.

        Returns:
            Number of sessions synced
        """
        if not self._persistent_fallback:
            return 0

        try:
            persistent_sessions = self._persistent_fallback.list_sessions()
            sessions = self._get_sessions_dict()

            for session in persistent_sessions:
                sessions[session.id] = session

            logger.info("sessions_synced_from_fallback", count=len(persistent_sessions))
            return len(persistent_sessions)

        except Exception as e:
            logger.error("sync_from_fallback_failed", error=str(e))
            return 0


__all__ = ["StreamlitSessionStore", "SESSIONS_KEY"]
