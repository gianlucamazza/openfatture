"""Database schema lifecycle, owned by the packaged Alembic migrations.

- A new, empty database gets the current schema and is stamped at head.
- A database behind head is refused at startup until ``openfatture init``
  upgrades it (after a backup for SQLite files).
- A database created by releases before 2.8.0 (tables, no ``alembic_version``)
  keeps working; ``openfatture init`` verifies its columns and adopts it.

Startup never runs migrations; only :func:`upgrade_schema` does.
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from sqlalchemy import MetaData, inspect
from sqlalchemy.engine import Connection, Engine

if TYPE_CHECKING:
    from alembic.config import Config

MIGRATIONS_DIR = Path(__file__).parent / "migrations"

# Last revision whose changes are all plain columns/tables that ``create_all``
# already produces; later revisions are idempotent and safe to replay.
LEGACY_ADOPTION_REVISION = "dda5c6e9a600"

SchemaState = Literal["empty", "current", "outdated", "unversioned", "ahead"]


class SchemaError(RuntimeError):
    """The database schema cannot be used as it is."""


def _config(connection: Connection) -> Config:
    from alembic.config import Config

    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.attributes["connection"] = connection
    return config


def head_revision() -> str:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    head = ScriptDirectory.from_config(config).get_current_head()
    if head is None:
        raise SchemaError("No migration head found")
    return head


def current_revision(connection: Connection) -> str | None:
    from alembic.runtime.migration import MigrationContext

    return MigrationContext.configure(connection).get_current_revision()


def schema_state(engine: Engine) -> SchemaState:
    """Classify the database without changing it."""
    from alembic.script import ScriptDirectory

    with engine.connect() as connection:
        tables = set(inspect(connection).get_table_names())
        if not tables - {"alembic_version"}:
            return "empty"
        if "alembic_version" not in tables:
            return "unversioned"
        current = current_revision(connection)
    head = head_revision()
    if current == head:
        return "current"
    from alembic.config import Config

    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    known = {rev.revision for rev in ScriptDirectory.from_config(config).walk_revisions()}
    return "outdated" if current in known else "ahead"


def _metadata() -> MetaData:
    """``Base.metadata`` with every model module imported, so no table is missed."""
    from openfatture.payment.domain import models as payment_models
    from openfatture.storage.database import models as storage_models
    from openfatture.storage.database.base import Base

    assert payment_models and storage_models
    return Base.metadata


def _create_and_stamp(engine: Engine) -> None:
    from alembic import command

    with engine.begin() as connection:
        _metadata().create_all(bind=connection)
        command.stamp(_config(connection), "head")


def prepare_schema(engine: Engine) -> SchemaState:
    """Make a database usable at startup without migrating existing data."""
    state = schema_state(engine)
    if state == "empty":
        _create_and_stamp(engine)
        return "current"
    if state == "unversioned":
        # Pre-2.8 behaviour: add missing tables, never alter existing ones.
        _metadata().create_all(bind=engine)
        return state
    if state == "outdated":
        raise SchemaError("The database schema is outdated: run `openfatture init` to upgrade it")
    if state == "ahead":
        raise SchemaError(
            "The database was migrated by a newer OpenFatture release: upgrade OpenFatture"
        )
    return state


def missing_columns(engine: Engine) -> list[str]:
    """Model columns absent from the database, as ``table.column``."""
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    missing: list[str] = []
    for table in _metadata().sorted_tables:
        if table.name not in tables:
            continue
        present = {column["name"] for column in inspector.get_columns(table.name)}
        missing += [f"{table.name}.{c.name}" for c in table.columns if c.name not in present]
    return missing


def backup_sqlite(engine: Engine) -> Path | None:
    """Copy a file-backed SQLite database next to itself; return the copy."""
    if engine.url.get_backend_name() != "sqlite" or not engine.url.database:
        return None
    source = Path(engine.url.database)
    if not source.exists():
        return None
    target = source.with_name(f"{source.name}.bak-{datetime.now():%Y%m%d%H%M%S}")
    shutil.copy2(source, target)
    return target


def upgrade_schema(engine: Engine) -> tuple[SchemaState, Path | None]:
    """Bring the database to head; return the previous state and any backup."""
    from alembic import command

    state = schema_state(engine)
    if state == "empty":
        _create_and_stamp(engine)
        return state, None
    if state == "current":
        return state, None
    if state == "ahead":
        raise SchemaError(
            "The database was migrated by a newer OpenFatture release: upgrade OpenFatture"
        )
    if state == "unversioned":
        _metadata().create_all(bind=engine)
        missing = missing_columns(engine)
        if missing:
            raise SchemaError(
                "Cannot adopt this database automatically; missing columns: " + ", ".join(missing)
            )
    backup = backup_sqlite(engine)
    with engine.begin() as connection:
        config = _config(connection)
        if state == "unversioned":
            command.stamp(config, LEGACY_ADOPTION_REVISION)
        command.upgrade(config, "head")
    return state, backup


def upgrade_database(url: str) -> tuple[SchemaState, Path | None]:
    """Open ``url``, upgrade it to head and release the connection."""
    from sqlalchemy import create_engine

    engine = create_engine(url)
    try:
        return upgrade_schema(engine)
    finally:
        engine.dispose()


def database_schema_state(url: str) -> SchemaState | None:
    """Read-only state of ``url``; None when the database cannot be opened."""
    from sqlalchemy import create_engine, make_url

    parsed = make_url(url)
    if parsed.get_backend_name() == "sqlite" and parsed.database:
        if parsed.database != ":memory:" and not Path(parsed.database).exists():
            return "empty"  # connecting would create the file
    engine = create_engine(url)
    try:
        return schema_state(engine)
    except Exception:
        return None
    finally:
        engine.dispose()
