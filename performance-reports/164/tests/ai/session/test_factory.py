"""Comprehensive tests for session store factory.

Testing the single file-backed session factory.
"""

from pathlib import Path

import pytest

from openfatture.ai.session import ChatSession
from openfatture.ai.session.factory import get_session_store
from openfatture.ai.session.file_store import FileSessionStore


class TestFactory:
    """Test the file-backed session factory."""

    def test_default_returns_file_store(self):
        """The CLI-first default returns FileSessionStore."""
        store = get_session_store()
        assert isinstance(store, FileSessionStore)

    def test_explicit_file_type(self, tmp_path: Path):
        """Test explicit file type parameter."""
        store = get_session_store(sessions_dir=tmp_path)
        assert isinstance(store, FileSessionStore)
        assert store.sessions_dir == tmp_path


class TestFactoryIntegration:
    """Test factory integration with actual stores."""

    def test_file_store_works_end_to_end(self, tmp_path: Path):
        """Test FileStore created by factory works correctly."""
        store = get_session_store(sessions_dir=tmp_path)

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
        store = get_session_store(sessions_dir=custom_dir)

        assert isinstance(store, FileSessionStore)
        assert store.sessions_dir == custom_dir
        assert custom_dir.exists()

    def test_store_interface_compliance(self, tmp_path: Path):
        """Test factory returns SessionStore-compliant instance."""
        store = get_session_store(sessions_dir=tmp_path)

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
        store = get_session_store(sessions_dir=None)
        assert isinstance(store, FileSessionStore)
        assert store.sessions_dir.exists()

    def test_multiple_calls_return_new_instances(self, tmp_path: Path):
        """Test factory returns new instances (not singletons)."""
        store1 = get_session_store(sessions_dir=tmp_path)
        store2 = get_session_store(sessions_dir=tmp_path)

        # Different instances
        assert store1 is not store2

        # But same type and directory
        assert type(store1) is type(store2)
        assert store1.sessions_dir == store2.sessions_dir


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
