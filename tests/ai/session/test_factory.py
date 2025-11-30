"""Comprehensive tests for session store factory.

Testing context detection and factory pattern following 2025 best practices.
"""

import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from openfatture.ai.session import ChatSession
from openfatture.ai.session.factory import get_default_store, get_session_store
from openfatture.ai.session.file_store import FileSessionStore
from openfatture.ai.session.store import SessionStore


class TestFactoryContextDetection:
    """Test automatic context detection."""

    def test_cli_context_returns_file_store(self):
        """Test CLI context (no Streamlit) returns FileSessionStore."""
        store = get_session_store()
        assert isinstance(store, FileSessionStore)

    def test_explicit_file_type(self, tmp_path: Path):
        """Test explicit file type parameter."""
        store = get_session_store(store_type="file", sessions_dir=tmp_path)
        assert isinstance(store, FileSessionStore)
        assert store.sessions_dir == tmp_path

    @patch("openfatture.ai.session.factory._is_streamlit_context")
    def test_streamlit_context_detection(self, mock_is_streamlit: Mock):
        """Test Streamlit context detection returns StreamlitSessionStore."""
        mock_is_streamlit.return_value = True

        # Mock Streamlit imports
        with patch.dict("sys.modules", {"streamlit": Mock()}):
            from openfatture.ai.session.streamlit_store import StreamlitSessionStore

            # Create mock st.session_state
            mock_st = Mock()
            mock_st.session_state = {"_openfatture_sessions": {}}

            with patch("streamlit.session_state", mock_st.session_state):
                store = get_session_store()
                assert isinstance(store, StreamlitSessionStore)

    def test_auto_detection_default(self):
        """Test auto detection is default behavior."""
        store1 = get_session_store()
        store2 = get_session_store(store_type="auto")

        assert type(store1) == type(store2)

    def test_get_default_store(self):
        """Test get_default_store() convenience function."""
        store = get_default_store()
        assert isinstance(store, SessionStore)


class TestFactoryEnvironmentOverride:
    """Test environment variable override."""

    def test_env_override_file(self, tmp_path: Path):
        """Test OPENFATTURE_SESSION_STORE=file override."""
        with patch.dict(os.environ, {"OPENFATTURE_SESSION_STORE": "file"}):
            store = get_session_store(sessions_dir=tmp_path)
            assert isinstance(store, FileSessionStore)

    def test_env_override_case_insensitive(self, tmp_path: Path):
        """Test environment variable is case-insensitive."""
        with patch.dict(os.environ, {"OPENFATTURE_SESSION_STORE": "FILE"}):
            store = get_session_store(sessions_dir=tmp_path)
            assert isinstance(store, FileSessionStore)

    def test_env_override_invalid_value_ignored(self):
        """Test invalid environment value is ignored."""
        with patch.dict(os.environ, {"OPENFATTURE_SESSION_STORE": "invalid"}):
            store = get_session_store()
            # Should fall back to auto-detection (FileStore in CLI)
            assert isinstance(store, FileSessionStore)


class TestFactoryHybridMode:
    """Test hybrid persistence mode."""

    @patch("openfatture.ai.session.factory._is_streamlit_context")
    def test_hybrid_mode_streamlit_with_persistence(self, mock_is_streamlit: Mock, tmp_path: Path):
        """Test hybrid mode: Streamlit + file fallback."""
        mock_is_streamlit.return_value = True

        # Mock Streamlit
        with patch.dict("sys.modules", {"streamlit": Mock()}):
            from openfatture.ai.session.streamlit_store import StreamlitSessionStore

            mock_st = Mock()
            mock_st.session_state = {"_openfatture_sessions": {}}

            with patch("streamlit.session_state", mock_st.session_state):
                store = get_session_store(
                    store_type="streamlit",
                    enable_persistence=True,
                    sessions_dir=tmp_path,
                )

                assert isinstance(store, StreamlitSessionStore)
                assert store._persistent_fallback is not None
                assert isinstance(store._persistent_fallback, FileSessionStore)

    @patch("openfatture.ai.session.factory._is_streamlit_context")
    def test_hybrid_mode_memory_only(self, mock_is_streamlit: Mock):
        """Test pure memory mode without persistence."""
        mock_is_streamlit.return_value = True

        with patch.dict("sys.modules", {"streamlit": Mock()}):
            from openfatture.ai.session.streamlit_store import StreamlitSessionStore

            mock_st = Mock()
            mock_st.session_state = {"_openfatture_sessions": {}}

            with patch("streamlit.session_state", mock_st.session_state):
                store = get_session_store(
                    store_type="streamlit",
                    enable_persistence=False,
                )

                assert isinstance(store, StreamlitSessionStore)
                assert store._persistent_fallback is None


class TestFactoryIntegration:
    """Test factory integration with actual stores."""

    def test_file_store_works_end_to_end(self, tmp_path: Path):
        """Test FileStore created by factory works correctly."""
        store = get_session_store(store_type="file", sessions_dir=tmp_path)

        # Create and save session
        session = ChatSession()
        session.metadata.title = "Factory Test"
        session.add_user_message("Hello")

        assert store.save(session)

        # Load session
        loaded = store.load(session.id)
        assert loaded is not None
        assert loaded.metadata.title == "Factory Test"

    def test_custom_sessions_dir(self, tmp_path: Path):
        """Test custom sessions directory is respected."""
        custom_dir = tmp_path / "custom_sessions"
        store = get_session_store(store_type="file", sessions_dir=custom_dir)

        assert isinstance(store, FileSessionStore)
        assert store.sessions_dir == custom_dir
        assert custom_dir.exists()

    def test_store_interface_compliance(self, tmp_path: Path):
        """Test factory returns SessionStore-compliant instance."""
        store = get_session_store(store_type="file", sessions_dir=tmp_path)

        # Verify SessionStore interface
        assert hasattr(store, "save")
        assert hasattr(store, "load")
        assert hasattr(store, "delete")
        assert hasattr(store, "list_sessions")
        assert hasattr(store, "exists")
        assert hasattr(store, "get_stats")

        # All methods should be callable
        assert callable(store.save)
        assert callable(store.load)
        assert callable(store.delete)
        assert callable(store.list_sessions)
        assert callable(store.exists)
        assert callable(store.get_stats)


class TestFactoryEdgeCases:
    """Test factory edge cases and error handling."""

    def test_none_sessions_dir_uses_default(self):
        """Test None sessions_dir uses default location."""
        store = get_session_store(store_type="file", sessions_dir=None)
        assert isinstance(store, FileSessionStore)
        assert store.sessions_dir.exists()

    def test_multiple_calls_return_new_instances(self, tmp_path: Path):
        """Test factory returns new instances (not singletons)."""
        store1 = get_session_store(store_type="file", sessions_dir=tmp_path)
        store2 = get_session_store(store_type="file", sessions_dir=tmp_path)

        # Different instances
        assert store1 is not store2

        # But same type and directory
        assert type(store1) == type(store2)
        assert store1.sessions_dir == store2.sessions_dir

    def test_factory_with_all_parameters(self, tmp_path: Path):
        """Test factory with all parameters specified."""
        store = get_session_store(
            store_type="file",
            sessions_dir=tmp_path / "sessions",
            enable_persistence=False,  # Ignored for file store
        )

        assert isinstance(store, FileSessionStore)
        assert store.sessions_dir == tmp_path / "sessions"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
