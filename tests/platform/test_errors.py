"""Errors returned to the assistant and CLI never include SQL."""

import sqlite3

from sqlalchemy.exc import IntegrityError, OperationalError

from openfatture.platform.errors import describe_error


def test_integrity_error_keeps_only_the_reason():
    exc = IntegrityError(
        "INSERT INTO fatture (numero) VALUES (?)",
        ("1",),
        sqlite3.IntegrityError("UNIQUE constraint failed: fatture.numero, fatture.anno"),
    )

    message = describe_error(exc)

    assert (
        message
        == "Rejected by the database: UNIQUE constraint failed: fatture.numero, fatture.anno"
    )
    assert "INSERT" not in message


def test_operational_error_is_generic():
    exc = OperationalError("SELECT 1", (), sqlite3.OperationalError("database is locked"))

    assert describe_error(exc) == "The database is unavailable or locked; try again"


def test_other_errors_keep_their_message():
    assert describe_error(ValueError("Invalid date")) == "Invalid date"
    assert describe_error(RuntimeError()) == "RuntimeError"
