"""Comprehensive tests for FileSessionStore.

Testing file-based session persistence following 2025 best practices.
"""

import json
from pathlib import Path

import pytest

from openfatture.ai.domain.message import Role
from openfatture.ai.session import ChatSession, SessionStatus
from openfatture.ai.session.file_store import FileSessionStore


class TestFileSessionStoreBasics:
    """Test basic FileSessionStore operations."""

    @pytest.fixture
    def temp_sessions_dir(self, tmp_path: Path) -> Path:
        """Create temporary sessions directory."""
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        return sessions_dir

    @pytest.fixture
    def store(self, temp_sessions_dir: Path) -> FileSessionStore:
        """Create FileSessionStore with temp directory."""
        return FileSessionStore(sessions_dir=temp_sessions_dir)

    @pytest.fixture
    def sample_session(self) -> ChatSession:
        """Create sample session for testing."""
        session = ChatSession()
        session.metadata.title = "Test Session"
        session.add_user_message("Hello AI")
        session.add_assistant_message("Hello! How can I help?", provider="test", model="gpt-4")
        return session

    def test_initialization(self, temp_sessions_dir: Path):
        """Test store initialization."""
        store = FileSessionStore(sessions_dir=temp_sessions_dir)
        assert store.sessions_dir == temp_sessions_dir
        assert temp_sessions_dir.exists()

    def test_save_session(self, store: FileSessionStore, sample_session: ChatSession):
        """Test saving a session."""
        result = store.save(sample_session)
        assert result is True

        # Verify file exists
        session_file = store.sessions_dir / f"{sample_session.id}.json"
        assert session_file.exists()

        # Verify content
        with open(session_file) as f:
            data = json.load(f)
        assert data["id"] == sample_session.id
        assert data["metadata"]["title"] == "Test Session"

    def test_load_session(self, store: FileSessionStore, sample_session: ChatSession):
        """Test loading a session."""
        # Save first
        store.save(sample_session)

        # Load
        loaded = store.load(sample_session.id)
        assert loaded is not None
        assert loaded.id == sample_session.id
        assert loaded.metadata.title == sample_session.metadata.title
        assert len(loaded.messages) == 2

    def test_load_nonexistent_session(self, store: FileSessionStore):
        """Test loading nonexistent session returns None."""
        result = store.load("nonexistent-session-id")
        assert result is None

    def test_exists(self, store: FileSessionStore, sample_session: ChatSession):
        """Test exists() method."""
        assert not store.exists(sample_session.id)

        store.save(sample_session)
        assert store.exists(sample_session.id)

    def test_delete_soft(self, store: FileSessionStore, sample_session: ChatSession):
        """Test soft delete marks session as deleted."""
        store.save(sample_session)

        result = store.delete(sample_session.id, permanent=False)
        assert result is True

        # Session file still exists
        assert store.exists(sample_session.id)

        # But status is DELETED
        loaded = store.load(sample_session.id)
        assert loaded is not None
        assert loaded.status == SessionStatus.DELETED

    def test_delete_permanent(self, store: FileSessionStore, sample_session: ChatSession):
        """Test permanent delete removes file."""
        store.save(sample_session)

        result = store.delete(sample_session.id, permanent=True)
        assert result is True

        # File should be gone
        assert not store.exists(sample_session.id)


class TestFileSessionStoreListingSorting:
    """Test session listing and filtering."""

    @pytest.fixture
    def store_with_sessions(self, tmp_path: Path) -> tuple[FileSessionStore, list[ChatSession]]:
        """Create store with multiple sessions."""
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        store = FileSessionStore(sessions_dir=sessions_dir)

        sessions = []
        for i in range(5):
            session = ChatSession()
            session.metadata.title = f"Session {i}"
            session.add_user_message(f"Message {i}")
            store.save(session)
            sessions.append(session)

        return store, sessions

    def test_list_sessions(self, store_with_sessions: tuple[FileSessionStore, list[ChatSession]]):
        """Test listing all sessions."""
        store, _ = store_with_sessions

        sessions = store.list_sessions()
        assert len(sessions) == 5

    def test_list_sessions_with_limit(self, store_with_sessions: tuple[FileSessionStore, list[ChatSession]]):
        """Test listing with limit."""
        store, _ = store_with_sessions

        sessions = store.list_sessions(limit=3)
        assert len(sessions) == 3

    def test_list_sessions_sorted_by_updated(self, store_with_sessions: tuple[FileSessionStore, list[ChatSession]]):
        """Test sessions are sorted by last update (newest first)."""
        store, original_sessions = store_with_sessions

        # Update first session (making it newest)
        first = store.load(original_sessions[0].id)
        assert first is not None
        first.add_user_message("New message")
        store.save(first)

        # List sessions
        sessions = store.list_sessions()

        # First session should be at the top now
        assert sessions[0].id == original_sessions[0].id

    def test_list_active_only(self, store_with_sessions: tuple[FileSessionStore, list[ChatSession]]):
        """Test filtering by status."""
        store, original_sessions = store_with_sessions

        # Archive one session
        session = store.load(original_sessions[0].id)
        assert session is not None
        session.archive()
        store.save(session)

        # List active only
        active = store.list_sessions(status=SessionStatus.ACTIVE)
        assert len(active) == 4

        # List archived
        archived = store.list_sessions(status=SessionStatus.ARCHIVED)
        assert len(archived) == 1

    def test_list_excludes_deleted_by_default(self, store_with_sessions: tuple[FileSessionStore, list[ChatSession]]):
        """Test deleted sessions excluded by default."""
        store, original_sessions = store_with_sessions

        # Soft delete one session
        store.delete(original_sessions[0].id, permanent=False)

        # List all (should exclude deleted)
        sessions = store.list_sessions()
        assert len(sessions) == 4

        # Explicitly list deleted
        deleted = store.list_sessions(status=SessionStatus.DELETED)
        assert len(deleted) == 1


class TestFileSessionStoreAdvanced:
    """Test advanced FileSessionStore features."""

    @pytest.fixture
    def store(self, tmp_path: Path) -> FileSessionStore:
        """Create FileSessionStore with temp directory."""
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        return FileSessionStore(sessions_dir=sessions_dir)

    def test_get_stats(self, store: FileSessionStore):
        """Test get_stats() returns accurate counts."""
        # Create sessions with different statuses
        active = ChatSession()
        active.metadata.title = "Active"
        store.save(active)

        archived = ChatSession()
        archived.metadata.title = "Archived"
        archived.archive()
        store.save(archived)

        deleted = ChatSession()
        deleted.metadata.title = "Deleted"
        store.save(deleted)
        store.delete(deleted.id, permanent=False)

        # Get stats
        stats = store.get_stats()
        assert stats["total"] == 3
        assert stats["active"] == 1
        assert stats["archived"] == 1
        assert stats["deleted"] == 1

    def test_get_recent_sessions(self, store: FileSessionStore):
        """Test get_recent_sessions() returns active sessions."""
        # Create 15 sessions
        for i in range(15):
            session = ChatSession()
            session.metadata.title = f"Session {i}"
            store.save(session)

        # Get recent (default limit 10)
        recent = store.get_recent_sessions()
        assert len(recent) == 10

        # Get recent with custom limit
        recent = store.get_recent_sessions(limit=5)
        assert len(recent) == 5

    def test_search_sessions_by_title(self, store: FileSessionStore):
        """Test search by title."""
        # Create sessions
        session1 = ChatSession()
        session1.metadata.title = "Invoice Discussion"
        store.save(session1)

        session2 = ChatSession()
        session2.metadata.title = "Tax Guidance"
        store.save(session2)

        # Search
        results = store.search_sessions("invoice")
        assert len(results) == 1
        assert results[0].metadata.title == "Invoice Discussion"

    def test_search_sessions_by_content(self, store: FileSessionStore):
        """Test search by message content."""
        session = ChatSession()
        session.metadata.title = "Chat"
        session.add_user_message("How do I create a FatturaPA invoice?")
        store.save(session)

        # Search
        results = store.search_sessions("FatturaPA")
        assert len(results) == 1

    def test_archive_old_sessions(self, store: FileSessionStore):
        """Test archiving old sessions."""
        from datetime import datetime, timedelta

        # Create old session
        old_session = ChatSession()
        old_session.metadata.title = "Old Session"
        old_session.metadata.updated_at = datetime.now() - timedelta(days=40)
        store.save(old_session)

        # Create recent session
        recent_session = ChatSession()
        recent_session.metadata.title = "Recent Session"
        store.save(recent_session)

        # Archive sessions older than 30 days
        count = store.archive_old_sessions(days_old=30)
        assert count == 1

        # Verify
        old = store.load(old_session.id)
        assert old is not None
        assert old.status == SessionStatus.ARCHIVED

        recent = store.load(recent_session.id)
        assert recent is not None
        assert recent.status == SessionStatus.ACTIVE

    def test_cleanup_deleted(self, store: FileSessionStore):
        """Test cleanup_deleted() permanently removes deleted sessions."""
        # Create and soft-delete sessions
        session1 = ChatSession()
        store.save(session1)
        store.delete(session1.id, permanent=False)

        session2 = ChatSession()
        store.save(session2)
        store.delete(session2.id, permanent=False)

        # Cleanup
        count = store.cleanup_deleted()
        assert count == 2

        # Verify files are gone
        assert not store.exists(session1.id)
        assert not store.exists(session2.id)

    def test_export_session_markdown(self, store: FileSessionStore, tmp_path: Path):
        """Test exporting session as Markdown."""
        session = ChatSession()
        session.metadata.title = "Export Test"
        session.add_user_message("Hello")
        session.add_assistant_message("Hi there!")
        store.save(session)

        # Export
        output_path = tmp_path / "export.md"
        result = store.export_session(session.id, format="markdown", output_path=output_path)

        assert result is not None
        assert output_path.exists()

        content = output_path.read_text()
        assert "Export Test" in content
        assert "Hello" in content
        assert "Hi there!" in content

    def test_export_session_json(self, store: FileSessionStore, tmp_path: Path):
        """Test exporting session as JSON."""
        session = ChatSession()
        session.metadata.title = "Export Test"
        session.add_user_message("Hello")
        store.save(session)

        # Export
        output_path = tmp_path / "export.json"
        result = store.export_session(session.id, format="json", output_path=output_path)

        assert result is not None
        assert output_path.exists()

        data = json.loads(output_path.read_text())
        assert data["metadata"]["title"] == "Export Test"


class TestFileSessionStoreErrorHandling:
    """Test error handling and edge cases."""

    @pytest.fixture
    def store(self, tmp_path: Path) -> FileSessionStore:
        """Create FileSessionStore with temp directory."""
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        return FileSessionStore(sessions_dir=sessions_dir)

    def test_load_corrupted_session(self, store: FileSessionStore):
        """Test loading corrupted JSON file."""
        # Create corrupted file
        session_file = store.sessions_dir / "corrupted-session.json"
        session_file.write_text("{invalid json")

        result = store.load("corrupted-session")
        assert result is None

    def test_invalid_session_id(self, store: FileSessionStore):
        """Test handling of invalid session IDs."""
        # Path traversal attempt
        result = store.load("../../../etc/passwd")
        assert result is None

        # Special characters
        result = store.load("session|with|pipes")
        assert result is None

    def test_delete_nonexistent_session(self, store: FileSessionStore):
        """Test deleting nonexistent session."""
        result = store.delete("nonexistent", permanent=True)
        assert result is True  # Should not fail

    def test_export_nonexistent_session(self, store: FileSessionStore, tmp_path: Path):
        """Test exporting nonexistent session."""
        result = store.export_session("nonexistent", output_path=tmp_path / "out.md")
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
