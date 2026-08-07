"""Chat session management for OpenFatture AI.

Provides file-backed session storage for CLI and interactive terminal flows.

Key Components:
- ChatSession, ChatMessage: Core session models
- SessionStore: Abstract storage interface
- FileSessionStore: JSON file persistence
- get_session_store(): Factory for the file-backed store

Example:
    from openfatture.ai.session import get_session_store

    store = get_session_store()
    store.save(session)
    session = store.load("session-id")
"""

from openfatture.ai.session.factory import get_session_store
from openfatture.ai.session.file_store import FileSessionStore
from openfatture.ai.session.manager import SessionManager
from openfatture.ai.session.models import ChatMessage, ChatSession, SessionMetadata, SessionStatus
from openfatture.ai.session.store import SessionStore

__all__ = [
    # Core models
    "ChatSession",
    "ChatMessage",
    "SessionMetadata",
    "SessionStatus",
    "SessionManager",
    # New unified storage
    "SessionStore",
    "FileSessionStore",
    # Factory
    "get_session_store",
]
