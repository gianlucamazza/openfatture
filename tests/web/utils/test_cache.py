"""Tests for cache utilities - Best Practices 2025.

Tests cover:
- Database session management
- Session lifecycle
- Context manager behavior
- Cleanup functionality
"""

from unittest.mock import MagicMock, patch

import pytest


@patch("openfatture.web.utils.cache.st")
@patch("openfatture.storage.database.base.get_session")
def test_get_db_session_creates_singleton(mock_get_session, mock_st):
    """Test that get_db_session creates a singleton session."""
    from openfatture.web.utils.cache import get_db_session

    # Setup mock
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session
    mock_st.session_state = {}

    # First call - should create session
    result1 = get_db_session()

    assert result1 == mock_session
    assert "db_session" in mock_st.session_state
    mock_get_session.assert_called_once()

    # Second call - should return cached session
    result2 = get_db_session()

    assert result2 == mock_session
    mock_get_session.assert_called_once()  # Still only one call


@patch("openfatture.web.utils.cache.st")
def test_clear_db_session_closes_and_removes(mock_st):
    """Test that clear_db_session properly closes and removes session."""
    from openfatture.web.utils.cache import clear_db_session

    # Setup mock session with dict-like session_state
    mock_session = MagicMock()
    session_state = {"db_session": mock_session}
    mock_st.session_state = session_state

    # Clear session
    clear_db_session()

    # Verify closed and removed
    mock_session.close.assert_called_once()
    assert "db_session" not in session_state


@patch("openfatture.web.utils.cache.st")
def test_clear_db_session_handles_error_gracefully(mock_st):
    """Test that clear_db_session handles errors without raising."""
    from openfatture.web.utils.cache import clear_db_session

    # Setup mock session that raises on close
    mock_session = MagicMock()
    mock_session.close.side_effect = Exception("Close failed")
    session_state = {"db_session": mock_session}
    mock_st.session_state = session_state

    # Should not raise
    clear_db_session()

    # Session should still be removed even if close failed
    assert "db_session" not in session_state


@patch("openfatture.web.utils.cache.st")
def test_clear_db_session_safe_when_no_session(mock_st):
    """Test that clear_db_session is safe to call when no session exists."""
    from openfatture.web.utils.cache import clear_db_session

    mock_st.session_state = {}

    # Should not raise
    clear_db_session()


@patch("openfatture.storage.database.base.get_session")
def test_db_session_scope_commits_on_success(mock_get_session):
    """Test that db_session_scope commits transaction on success."""
    from openfatture.web.utils.cache import db_session_scope

    # Setup mock
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session

    # Use context manager successfully
    with db_session_scope() as session:
        assert session == mock_session
        # Simulate some work
        pass

    # Verify commit and close
    mock_session.commit.assert_called_once()
    mock_session.rollback.assert_not_called()
    mock_session.close.assert_called_once()


@patch("openfatture.storage.database.base.get_session")
def test_db_session_scope_rollback_on_error(mock_get_session):
    """Test that db_session_scope rolls back transaction on error."""
    from openfatture.web.utils.cache import db_session_scope

    # Setup mock
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session

    # Use context manager with error
    with pytest.raises(ValueError):
        with db_session_scope() as session:
            raise ValueError("Test error")

    # Verify rollback and close
    mock_session.commit.assert_not_called()
    mock_session.rollback.assert_called_once()
    mock_session.close.assert_called_once()


@patch("openfatture.storage.database.base.get_session")
def test_db_session_scope_closes_even_on_commit_error(mock_get_session):
    """Test that db_session_scope closes session even if commit fails."""
    from openfatture.web.utils.cache import db_session_scope

    # Setup mock with failing commit
    mock_session = MagicMock()
    mock_session.commit.side_effect = Exception("Commit failed")
    mock_get_session.return_value = mock_session

    # Use context manager
    with pytest.raises(Exception, match="Commit failed"):
        with db_session_scope() as session:
            pass

    # Verify close was still called
    mock_session.close.assert_called_once()


def test_cache_for_session_decorator():
    """Test that cache_for_session decorator caches function results."""
    from openfatture.web.utils.cache import cache_for_session

    # Mock st.session_state
    session_state = {}

    with patch("openfatture.web.utils.cache.st") as mock_st:
        mock_st.session_state = session_state

        # Decorate function
        call_count = 0

        @cache_for_session
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1

        # Second call with same args - should use cache
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Not called again

        # Different args - should call function
        result3 = expensive_function(10)
        assert result3 == 20
        assert call_count == 2


def test_invalidate_cache_removes_function_cache():
    """Test that invalidate_cache removes cached results for specific function."""
    from openfatture.web.utils.cache import cache_for_session, invalidate_cache

    session_state = {}

    with patch("openfatture.web.utils.cache.st") as mock_st:
        mock_st.session_state = session_state

        @cache_for_session
        def test_func(x):
            return x * 2

        # Call function to populate cache
        test_func(5)
        test_func(10)

        # Verify cache exists
        cache_keys = [k for k in session_state if k.startswith("_cache_test_func_")]
        assert len(cache_keys) == 2

        # Invalidate cache
        invalidate_cache("test_func")

        # Verify cache cleared
        cache_keys = [k for k in session_state if k.startswith("_cache_test_func_")]
        assert len(cache_keys) == 0
