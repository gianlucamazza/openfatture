"""Alembic owns the schema: create+stamp, refuse outdated, adopt pre-2.8 databases."""

import pytest
from alembic import command
from sqlalchemy import create_engine, text

from openfatture.storage import schema
from openfatture.storage.schema import (
    SchemaError,
    database_schema_state,
    head_revision,
    prepare_schema,
    schema_state,
    upgrade_schema,
)


def _engine(tmp_path, name="db.sqlite"):
    return create_engine(f"sqlite:///{tmp_path / name}")


def test_migrations_ship_with_the_package():
    assert (schema.MIGRATIONS_DIR / "env.py").is_file()
    assert list((schema.MIGRATIONS_DIR / "versions").glob("*.py"))
    assert head_revision()


def test_new_database_is_created_at_head(tmp_path):
    engine = _engine(tmp_path)

    assert schema_state(engine) == "empty"
    assert prepare_schema(engine) == "current"
    with engine.connect() as connection:
        assert schema.current_revision(connection) == head_revision()
        indexes = connection.execute(
            text("select name from sqlite_master where name = 'uq_fatture_numero_anno'")
        ).all()
    assert indexes


def test_outdated_database_is_refused_until_upgraded(tmp_path):
    engine = _engine(tmp_path)
    prepare_schema(engine)
    with engine.begin() as connection:
        command.stamp(schema._config(connection), "20261110_merge")

    assert schema_state(engine) == "outdated"
    with pytest.raises(SchemaError, match="openfatture init"):
        prepare_schema(engine)

    previous, backup = upgrade_schema(engine)
    assert previous == "outdated"
    assert backup is not None and backup.exists()
    assert schema_state(engine) == "current"


def _legacy(engine):
    """A pre-2.8 database: create_all tables, no alembic_version."""
    from sqlalchemy.orm import Session

    from openfatture.storage.database.models import Cliente

    schema._metadata().create_all(bind=engine)
    with Session(engine) as session:
        session.add(Cliente(denominazione="Legacy", partita_iva="12345678903"))
        session.commit()


def test_pre_28_database_keeps_working_and_is_adopted_by_init(tmp_path):
    engine = _engine(tmp_path)
    _legacy(engine)

    assert schema_state(engine) == "unversioned"
    assert prepare_schema(engine) == "unversioned"  # startup does not migrate

    previous, backup = upgrade_schema(engine)
    assert previous == "unversioned" and backup is not None
    assert schema_state(engine) == "current"
    with engine.connect() as connection:
        assert connection.execute(text("select count(*) from clienti")).scalar_one() == 1


def test_adoption_refuses_databases_with_missing_columns(tmp_path):
    engine = _engine(tmp_path)
    _legacy(engine)
    with engine.begin() as connection:
        connection.execute(text("alter table fatture drop column issued_elsewhere"))

    with pytest.raises(SchemaError, match="fatture.issued_elsewhere"):
        upgrade_schema(engine)
    assert schema_state(engine) == "unversioned"


def test_state_check_never_creates_a_database(tmp_path):
    path = tmp_path / "missing.sqlite"
    assert database_schema_state(f"sqlite:///{path}") == "empty"
    assert not path.exists()
