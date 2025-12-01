"""Unified database session management with context manager pattern.

This module provides modern session management utilities to replace the 26+
instances of direct SessionLocal() instantiation scattered across the codebase.

Modern best practices (2025):
- Context managers for automatic cleanup
- Proper exception handling and rollback
- Async/sync bridge integration
- Transaction isolation
- Connection pooling awareness

Usage:
    # Sync context manager (recommended)
    with db_session() as db:
        fattura = db.query(Fattura).filter_by(numero="001").first()
        db.commit()

    # Async context manager
    async with async_db_session() as db:
        fattura = db.query(Fattura).filter_by(numero="001").first()
        db.commit()

    # Direct session (legacy, manual cleanup required)
    db = get_db_session()
    try:
        # Use db
        db.commit()
    finally:
        db.close()

Migration from old patterns:
    # OLD (manual cleanup, error-prone)
    from openfatture.storage.database.base import SessionLocal
    db = SessionLocal()
    try:
        # Use db
        db.commit()
    finally:
        db.close()

    # NEW (automatic cleanup, safe)
    from openfatture.storage.session import db_session
    with db_session() as db:
        # Use db
        db.commit()
"""

import asyncio
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from sqlalchemy.orm import Session

from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions with automatic cleanup.

    Provides:
    - Automatic session creation and cleanup
    - Proper exception handling with rollback
    - Logging for debugging
    - Connection pool management

    Yields:
        Session: SQLAlchemy session

    Raises:
        RuntimeError: If database not initialized
        Exception: Any exception from within the context (after rollback)

    Examples:
        # Basic usage
        with db_session() as db:
            fattura = db.query(Fattura).filter_by(numero="001").first()
            db.commit()

        # With exception handling
        try:
            with db_session() as db:
                fattura = create_fattura(db, ...)
                db.commit()
        except ValueError as e:
            logger.error("validation_error", error=str(e))

        # Read-only (no commit needed)
        with db_session() as db:
            clienti = db.query(Cliente).all()
            # Automatic cleanup, no commit

    Note:
        - Session is automatically rolled back on exception
        - Session is automatically closed on exit
        - You must call db.commit() to persist changes
    """
    from openfatture.storage.database.base import SessionLocal, get_session

    if SessionLocal is None:
        raise RuntimeError(
            "Database not initialized. Call init_db() first or configure DATABASE_URL."
        )

    db = get_session()
    try:
        logger.debug("db_session_created", session_id=id(db))
        yield db
    except Exception as e:
        logger.error(
            "db_session_error_rollback",
            error=str(e),
            error_type=type(e).__name__,
            session_id=id(db),
        )
        db.rollback()
        raise
    finally:
        logger.debug("db_session_closed", session_id=id(db))
        db.close()


@asynccontextmanager
async def async_db_session() -> AsyncGenerator[Session, None]:
    """Async context manager for database sessions.

    This is a thin wrapper around db_session() for use in async contexts.
    The actual database operations are still synchronous (SQLAlchemy 1.4 style),
    but the context manager can be used with async/await.

    Yields:
        Session: SQLAlchemy session

    Raises:
        RuntimeError: If database not initialized
        Exception: Any exception from within the context (after rollback)

    Examples:
        # Async usage
        async def create_invoice():
            async with async_db_session() as db:
                fattura = Fattura(numero="001", ...)
                db.add(fattura)
                db.commit()
                return fattura

        # In async CLI command
        @app.command()
        def my_command():
            async def _impl():
                async with async_db_session() as db:
                    return db.query(Fattura).all()

            return run_async(_impl())

    Note:
        - Uses db_session() internally (sync operations)
        - Yields control to event loop between operations
        - Useful for async CLI commands and agents
    """
    from openfatture.storage.database.base import SessionLocal, get_session

    # SQLAlchemy operations are sync, but we yield to event loop
    if SessionLocal is None:
        raise RuntimeError(
            "Database not initialized. Call init_db() first or configure DATABASE_URL."
        )

    db = get_session()
    try:
        logger.debug("async_db_session_created", session_id=id(db))
        await asyncio.sleep(0)  # Yield to event loop
        yield db
    except Exception as e:
        logger.error(
            "async_db_session_error_rollback",
            error=str(e),
            error_type=type(e).__name__,
            session_id=id(db),
        )
        db.rollback()
        raise
    finally:
        logger.debug("async_db_session_closed", session_id=id(db))
        db.close()


def get_db_session() -> Session:
    """Get a database session directly (manual cleanup required).

    This is a convenience function for cases where a context manager
    cannot be used. The caller is responsible for closing the session.

    Returns:
        Session: Database session

    Raises:
        RuntimeError: If database not initialized

    Examples:
        # Manual cleanup (use only when necessary)
        db = get_db_session()
        try:
            fattura = db.query(Fattura).first()
            db.commit()
        finally:
            db.close()

    Note:
        - Prefer using db_session() context manager instead
        - You MUST call db.close() when done
        - You MUST handle exceptions and rollback manually
    """
    from openfatture.storage.database.base import SessionLocal, get_session

    if SessionLocal is None:
        raise RuntimeError(
            "Database not initialized. Call init_db() first or configure DATABASE_URL."
        )

    logger.debug("direct_session_created")
    return get_session()


# Backward compatibility aliases (will be deprecated in Phase 5)
get_db = db_session  # For FastAPI dependency injection compatibility
