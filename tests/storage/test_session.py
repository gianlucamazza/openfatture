"""Comprehensive test suite for database session management.

Tests cover:
- Context manager functionality (db_session)
- Async context manager (async_db_session)
- Direct session creation (get_db_session)
- Exception handling and rollback
- Session lifecycle and cleanup
- Database initialization errors
- Integration with actual database operations
"""

import asyncio
import pytest
from unittest.mock import patch, MagicMock

from openfatture.storage.session import (
    db_session,
    async_db_session,
    get_db_session,
)
from openfatture.storage.database.models import Cliente


# ============================================================================
# db_session Context Manager Tests
# ============================================================================


class TestDbSession:
    """Test synchronous db_session context manager."""

    def test_basic_usage(self, test_db):
        """Test basic context manager usage."""
        with db_session() as db:
            assert db is not None
            assert hasattr(db, "query")
            assert hasattr(db, "commit")
            assert hasattr(db, "rollback")

    def test_auto_cleanup(self, test_db):
        """Test that session is automatically closed on exit."""
        session_id = None

        with db_session() as db:
            session_id = id(db)
            # Session is open

        # Session should be closed after exiting context
        # Note: We can't directly test if closed, but we verify no errors

    def test_commit_persists_changes(self, test_db):
        """Test that commit persists changes to database."""
        # Create a client
        with db_session() as db:
            cliente = Cliente(
                denominazione="Test Client",
                partita_iva="12345678901",
                codice_fiscale="TSTCLT90A01H501Z",
            )
            db.add(cliente)
            db.commit()
            cliente_id = cliente.id

        # Verify client exists in new session
        with db_session() as db:
            found = db.query(Cliente).filter_by(id=cliente_id).first()
            assert found is not None
            assert found.denominazione == "Test Client"

    def test_no_commit_doesnt_persist(self, test_db):
        """Test that changes without commit are not persisted."""
        cliente_id = None

        with db_session() as db:
            cliente = Cliente(
                denominazione="Uncommitted Client",
                partita_iva="98765432109",
                codice_fiscale="UNCMTD90A01H501Z",
            )
            db.add(cliente)
            db.flush()  # Get ID without commit
            cliente_id = cliente.id

        # Verify client does NOT exist in new session
        with db_session() as db:
            found = db.query(Cliente).filter_by(id=cliente_id).first()
            assert found is None

    def test_exception_triggers_rollback(self, test_db):
        """Test that exception triggers automatic rollback."""
        cliente_id = None

        try:
            with db_session() as db:
                cliente = Cliente(
                    denominazione="Exception Client",
                    partita_iva="11111111111",
                    codice_fiscale="EXCPTN90A01H501Z",
                )
                db.add(cliente)
                db.flush()
                cliente_id = cliente.id

                # Trigger exception
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Verify rollback occurred
        with db_session() as db:
            found = db.query(Cliente).filter_by(id=cliente_id).first()
            assert found is None

    def test_multiple_sessions_independent(self, test_db):
        """Test that multiple sessions are independent."""
        with db_session() as db1:
            with db_session() as db2:
                assert db1 is not db2
                assert id(db1) != id(db2)

    def test_read_only_operations(self, test_db):
        """Test read-only operations (no commit needed)."""
        # Setup: Create a client
        with db_session() as db:
            cliente = Cliente(
                denominazione="Read Only Client",
                partita_iva="22222222222",
                codice_fiscale="RDONLY90A01H501Z",
            )
            db.add(cliente)
            db.commit()

        # Test: Read without commit
        with db_session() as db:
            clienti = db.query(Cliente).all()
            assert len(clienti) >= 1


class TestDbSessionErrors:
    """Test error handling in db_session."""

    def test_uninitialized_database_raises(self):
        """Test that using session before init_db raises RuntimeError."""
        # Patch the import inside db_session() function
        with patch("openfatture.storage.database.base.SessionLocal", None):
            with pytest.raises(RuntimeError, match="Database not initialized"):
                with db_session() as db:
                    pass

    def test_exception_propagates_after_rollback(self, test_db):
        """Test that exceptions are propagated after rollback."""
        with pytest.raises(ValueError, match="Test error"):
            with db_session() as db:
                raise ValueError("Test error")


# ============================================================================
# async_db_session Context Manager Tests
# ============================================================================


class TestAsyncDbSession:
    """Test asynchronous async_db_session context manager."""

    @pytest.mark.asyncio
    async def test_basic_async_usage(self, test_db):
        """Test basic async context manager usage."""
        async with async_db_session() as db:
            assert db is not None
            assert hasattr(db, "query")
            assert hasattr(db, "commit")

    @pytest.mark.asyncio
    async def test_async_commit_persists(self, test_db):
        """Test that async commit persists changes."""
        cliente_id = None

        async with async_db_session() as db:
            cliente = Cliente(
                denominazione="Async Client",
                partita_iva="33333333333",
                codice_fiscale="ASYNC90A01H501Z",
            )
            db.add(cliente)
            db.commit()
            cliente_id = cliente.id

        # Verify in sync session
        with db_session() as db:
            found = db.query(Cliente).filter_by(id=cliente_id).first()
            assert found is not None
            assert found.denominazione == "Async Client"

    @pytest.mark.asyncio
    async def test_async_exception_rollback(self, test_db):
        """Test that async exception triggers rollback."""
        cliente_id = None

        try:
            async with async_db_session() as db:
                cliente = Cliente(
                    denominazione="Async Exception",
                    partita_iva="44444444444",
                    codice_fiscale="ASYNCE90A01H501Z",
                )
                db.add(cliente)
                db.flush()
                cliente_id = cliente.id

                raise RuntimeError("Async error")
        except RuntimeError:
            pass

        # Verify rollback
        with db_session() as db:
            found = db.query(Cliente).filter_by(id=cliente_id).first()
            assert found is None

    @pytest.mark.asyncio
    async def test_async_multiple_operations(self, test_db):
        """Test multiple async operations in sequence."""
        async with async_db_session() as db:
            # Operation 1: Create
            cliente = Cliente(
                denominazione="Multi Op Client",
                partita_iva="55555555555",
                codice_fiscale="MULTOP90A01H501Z",
            )
            db.add(cliente)
            db.commit()
            cliente_id = cliente.id

        async with async_db_session() as db:
            # Operation 2: Read and update
            cliente = db.query(Cliente).filter_by(id=cliente_id).first()
            assert cliente is not None
            cliente.denominazione = "Updated Name"
            db.commit()

        async with async_db_session() as db:
            # Operation 3: Verify update
            cliente = db.query(Cliente).filter_by(id=cliente_id).first()
            assert cliente.denominazione == "Updated Name"


# ============================================================================
# get_db_session Direct Session Tests
# ============================================================================


class TestGetDbSession:
    """Test direct session creation with get_db_session."""

    def test_direct_session_creation(self, test_db):
        """Test creating session directly."""
        db = get_db_session()
        try:
            assert db is not None
            assert hasattr(db, "query")
            assert hasattr(db, "commit")
        finally:
            db.close()

    def test_direct_session_requires_manual_cleanup(self, test_db):
        """Test that direct session requires manual close."""
        db = get_db_session()

        cliente = Cliente(
            denominazione="Direct Session Client",
            partita_iva="66666666666",
            codice_fiscale="DIRECT90A01H501Z",
        )
        db.add(cliente)
        db.commit()
        cliente_id = cliente.id

        # Must manually close
        db.close()

        # Verify persistence
        with db_session() as db2:
            found = db2.query(Cliente).filter_by(id=cliente_id).first()
            assert found is not None

    def test_direct_session_manual_rollback(self, test_db):
        """Test manual rollback with direct session."""
        db = get_db_session()

        try:
            cliente = Cliente(
                denominazione="Rollback Client",
                partita_iva="77777777777",
                codice_fiscale="ROLLBK90A01H501Z",
            )
            db.add(cliente)
            db.flush()
            cliente_id = cliente.id

            # Manual rollback
            db.rollback()
        finally:
            db.close()

        # Verify rollback
        with db_session() as db2:
            found = db2.query(Cliente).filter_by(id=cliente_id).first()
            assert found is None

    def test_uninitialized_database_raises_direct(self):
        """Test that direct session before init_db raises RuntimeError."""
        with patch("openfatture.storage.database.base.SessionLocal", None):
            with pytest.raises(RuntimeError, match="Database not initialized"):
                get_db_session()


# ============================================================================
# Integration Tests
# ============================================================================


class TestSessionIntegration:
    """Integration tests with real database operations."""

    def test_nested_sessions_work(self, test_db):
        """Test that nested sessions work correctly."""
        with db_session() as db1:
            cliente1 = Cliente(
                denominazione="Outer Client",
                partita_iva="88888888888",
                codice_fiscale="OUTER90A01H501Z",
            )
            db1.add(cliente1)
            db1.commit()
            cliente1_id = cliente1.id

            with db_session() as db2:
                cliente2 = Cliente(
                    denominazione="Inner Client",
                    partita_iva="99999999999",
                    codice_fiscale="INNER90A01H501Z",
                )
                db2.add(cliente2)
                db2.commit()
                cliente2_id = cliente2.id

        # Verify both persisted
        with db_session() as db:
            assert db.query(Cliente).filter_by(id=cliente1_id).first() is not None
            assert db.query(Cliente).filter_by(id=cliente2_id).first() is not None

    @pytest.mark.asyncio
    async def test_sync_and_async_interop(self, test_db):
        """Test that sync and async sessions interoperate."""
        # Create in sync
        with db_session() as db:
            cliente = Cliente(
                denominazione="Interop Client",
                partita_iva="10101010101",
                codice_fiscale="INTEROP0A01H501Z",
            )
            db.add(cliente)
            db.commit()
            cliente_id = cliente.id

        # Read in async
        async with async_db_session() as db:
            found = db.query(Cliente).filter_by(id=cliente_id).first()
            assert found is not None
            assert found.denominazione == "Interop Client"

            # Update in async
            found.denominazione = "Async Updated"
            db.commit()

        # Verify update in sync
        with db_session() as db:
            found = db.query(Cliente).filter_by(id=cliente_id).first()
            assert found.denominazione == "Async Updated"

    @pytest.mark.skip(reason="SQLite in-memory doesn't support concurrent writes across threads")
    def test_concurrent_sessions(self, test_db):
        """Test that concurrent sessions don't interfere.

        Note: This test is skipped because SQLite in-memory database doesn't support
        concurrent writes from multiple threads. In production with PostgreSQL or file-based
        SQLite, this would work correctly.
        """
        import threading

        results = []

        def worker(index):
            with db_session() as db:
                cliente = Cliente(
                    denominazione=f"Concurrent {index}",
                    partita_iva=f"{index:011d}",
                    codice_fiscale=f"CONCUR{index:02d}A01H501Z",
                )
                db.add(cliente)
                db.commit()
                results.append(cliente.id)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify all were created
        assert len(results) == 5
        with db_session() as db:
            for cliente_id in results:
                assert db.query(Cliente).filter_by(id=cliente_id).first() is not None
