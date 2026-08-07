"""Database base configuration, session management, and ORM mixins."""

import uuid
from collections.abc import Generator
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, MetaData, create_engine
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from ...utils.datetime import utc_now

# Naming convention for constraints (helps with Alembic migrations)
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    """Base class for all database models (without primary key)."""

    __abstract__ = True
    metadata = metadata

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class IntPKMixin:
    """Mixin providing an auto-incrementing integer primary key."""

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class UUIDPKMixin:
    """Mixin providing a UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )


# Database engine and session (will be configured at runtime)
engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None


def init_db(database_url: str = "sqlite:///./openfatture.db") -> None:
    """Initialize database engine and session factory."""
    global engine, SessionLocal

    engine = create_engine(
        database_url,
        echo=False,  # Set to True for SQL debug logging
        pool_pre_ping=True,  # Verify connections before using
    )

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create all tables
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database sessions."""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    assert SessionLocal is not None
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session() -> Session:
    """
    Get a database session directly (not a generator).

    This is a helper function for CLI commands and other synchronous code
    that needs a session. The caller is responsible for closing the session.

    Returns:
        Session: Database session

    Raises:
        RuntimeError: If database not initialized

    Usage:
        db = get_session()
        try:
            # Use db
            pass
        finally:
            db.close()
    """
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    return SessionLocal()
