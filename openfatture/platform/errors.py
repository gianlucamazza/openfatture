"""User-facing descriptions of unexpected errors.

Application services return ``{"error": ...}`` to the assistant and the CLI.
Database exceptions carry SQL statements and parameters; this keeps only the
reason, while the full exception still goes to the logs.
"""

from __future__ import annotations


def describe_error(exc: BaseException) -> str:
    """A short, safe message for ``exc``."""
    from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

    if isinstance(exc, IntegrityError):
        reason = str(exc.orig).splitlines()[0] if exc.orig is not None else "constraint violated"
        return f"Rejected by the database: {reason}"
    if isinstance(exc, OperationalError):
        return "The database is unavailable or locked; try again"
    if isinstance(exc, SQLAlchemyError):
        return f"Database error ({type(exc).__name__})"
    return str(exc) or type(exc).__name__
