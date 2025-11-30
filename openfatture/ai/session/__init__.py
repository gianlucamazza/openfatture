"""Chat session management for OpenFatture AI.

Provides unified session storage across CLI and Web UI with automatic
context detection and pluggable storage backends.

Key Components:
- ChatSession, ChatMessage: Core session models
- SessionStore: Abstract storage interface
- FileSessionStore: JSON file persistence
- StreamlitSessionStore: In-memory st.session_state storage
- get_session_store(): Factory with auto-detection

Example:
    # Auto-detect context (CLI vs Streamlit)
    from openfatture.ai.session import get_session_store

    store = get_session_store()
    store.save(session)
    session = store.load("session-id")
"""

from openfatture.ai.session.factory import get_default_store, get_session_store
from openfatture.ai.session.file_store import FileSessionStore
from openfatture.ai.session.manager import SessionManager
from openfatture.ai.session.models import ChatMessage, ChatSession, SessionMetadata, SessionStatus
from openfatture.ai.session.store import SessionStore

# Conditional import for Streamlit store (graceful degradation)
try:
    from openfatture.ai.session.streamlit_store import StreamlitSessionStore

    _STREAMLIT_AVAILABLE = True
except ImportError:
    _STREAMLIT_AVAILABLE = False
    StreamlitSessionStore = None  # type: ignore

__all__ = [
    # Core models
    "ChatSession",
    "ChatMessage",
    "SessionMetadata",
    "SessionStatus",
    # Legacy manager (backward compatibility)
    "SessionManager",
    # New unified storage
    "SessionStore",
    "FileSessionStore",
    "StreamlitSessionStore",
    # Factory
    "get_session_store",
    "get_default_store",
]
