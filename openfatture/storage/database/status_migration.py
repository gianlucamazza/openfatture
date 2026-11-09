"""Additive status journal migration usable by installed wheels and Alembic."""

from typing import cast

from sqlalchemy import Table, inspect
from sqlalchemy.engine import Connection, Engine

from openfatture.storage.database.models import (
    SDIInvoiceIdentity,
    SDINotificationRecord,
    SDISubmissionAttempt,
)

TABLES: tuple[Table, ...] = (
    cast(Table, SDINotificationRecord.__table__),
    cast(Table, SDISubmissionAttempt.__table__),
    cast(Table, SDIInvoiceIdentity.__table__),
)


def upgrade_status_schema(bind: Engine | Connection) -> None:
    """Validate the existing baseline then add only status journals; never stamp history."""
    inspector = inspect(bind)
    if not inspector.has_table("fatture"):
        raise ValueError("Initialize the core database before upgrading its status journals")
    required = {"id", "stato", "issued_elsewhere", "numero_sdi", "xml_path", "xml_firmato_path"}
    if not required <= {column["name"] for column in inspector.get_columns("fatture")}:
        raise ValueError("Unsupported invoice schema: upgrade the core database first")
    for table in TABLES:
        table.create(bind, checkfirst=True)


def downgrade_status_schema(bind: Engine | Connection) -> None:
    """Never silently discard receipt/transport evidence during a downgrade."""
    from sqlalchemy import func, select

    for table in TABLES:
        if inspect(bind).has_table(table.name):
            connection = bind.connect() if isinstance(bind, Engine) else bind
            try:
                if connection.execute(select(func.count()).select_from(table)).scalar_one():
                    raise ValueError(
                        "Status journals contain evidence; restore a pre-upgrade backup instead"
                    )
            finally:
                if isinstance(bind, Engine):
                    connection.close()
    for table in reversed(TABLES):
        table.drop(bind, checkfirst=True)
