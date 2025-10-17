"""Web service adapter for chat session management.

Provides async/sync bridge for chat sessions in Streamlit web interface.
"""

from typing import Any

import streamlit as st

from openfatture.ai.session import ChatSession, SessionManager


class StreamlitSessionService:
    """Adapter service for chat session management in Streamlit."""

    def __init__(self) -> None:
        """Initialize service with session manager."""
        self._session_manager: SessionManager | None = None

    @property
    def session_manager(self) -> SessionManager:
        """Get or create session manager (cached)."""
        if self._session_manager is None:
            self._session_manager = SessionManager()
        return self._session_manager

    def list_sessions(self) -> list[dict[str, Any]]:
        """
        Get list of available chat sessions.

        Returns:
            List of session dictionaries with metadata
        """
        sessions = self.session_manager.list_sessions()
        return [
            {
                "id": session.id,
                "title": session.metadata.title or f"Session {session.id[:8]}",
                "created_at": session.metadata.created_at,
                "updated_at": session.metadata.updated_at,
                "message_count": session.metadata.message_count,
                "total_tokens": session.metadata.total_tokens,
                "total_cost": session.metadata.total_cost_usd,
            }
            for session in sessions
        ]

    def load_session(self, session_id: str) -> dict[str, Any] | None:
        """
        Load a chat session by ID.

        Args:
            session_id: Session ID to load

        Returns:
            Session data dictionary or None if not found
        """
        session = self.session_manager.load_session(session_id)
        if session:
            return {
                "id": session.id,
                "title": session.metadata.title or f"Session {session.id[:8]}",
                "messages": [
                    {
                        "role": msg.role.value,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                    }
                    for msg in session.messages
                ],
                "metadata": session.metadata.model_dump(),
                "created_at": session.metadata.created_at.isoformat(),
                "updated_at": session.metadata.updated_at.isoformat(),
            }
        return None

    def save_session(self, session_data: dict[str, Any]) -> str | None:
        """
        Save a chat session.

        Args:
            session_data: Session data dictionary with messages and metadata

        Returns:
            Session ID if saved successfully, None otherwise
        """
        try:
            # Create ChatSession from data
            session = ChatSession()

            # Set metadata
            if "title" in session_data:
                session.metadata.title = session_data["title"]

            # Add messages
            if "messages" in session_data:
                from openfatture.ai.domain.message import Role

                for msg_data in session_data["messages"]:
                    try:
                        role = Role(msg_data["role"])
                        session.add_message(role, msg_data["content"])
                    except Exception:
                        continue  # Skip invalid messages

            # Save session
            success = self.session_manager.save_session(session)
            return session.id if success else None

        except Exception:
            return None

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a chat session.

        Args:
            session_id: Session ID to delete

        Returns:
            True if deleted successfully
        """
        return self.session_manager.delete_session(session_id)

    def create_new_session(self, title: str | None = None) -> str:
        """
        Create a new empty chat session.

        Args:
            title: Optional session title

        Returns:
            New session ID
        """
        session = ChatSession()
        if title:
            session.metadata.title = title

        self.session_manager.save_session(session)
        return session.id


@st.cache_resource
def get_session_service() -> StreamlitSessionService:
    """
    Get cached session service instance.

    Returns:
        Singleton session service
    """
    return StreamlitSessionService()
