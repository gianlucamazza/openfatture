"""Database session scopes.

- ``db_session()``: open a session, roll back on error, always close.
- ``session_scope(session)``: reuse a caller-provided session (not closed here)
  or fall back to ``db_session()``.

Application services use one of these instead of managing ``get_session()``
and ``close()`` by hand. Commit explicitly to persist changes.
"""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from openfatture.platform.logging import get_logger

logger = get_logger(__name__)


@contextmanager
def session_scope(session: Session | None = None) -> Generator[Session, None, None]:
    """Use ``session`` as-is (the caller owns it) or open a managed one.

    A provided session is neither committed, rolled back nor closed here; an
    owned session behaves like :func:`db_session`.
    """
    if session is not None:
        yield session
        return
    with db_session() as owned:
        yield owned


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


# Backward compatibility aliases (will be deprecated in Phase 5)
