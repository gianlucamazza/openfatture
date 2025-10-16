"""Client lifecycle events.

Events emitted during client operations (creation, deletion).
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import BaseEvent


@dataclass(frozen=True)
class ClientCreatedEvent(BaseEvent):
    """Event emitted when a new client is created.

    Triggered after client is saved to database.

    Hook point: post-client-create
    """

    client_id: int
    client_name: str
    partita_iva: str | None = None
    codice_fiscale: str | None = None
    codice_destinatario: str | None = None
    pec: str | None = None


@dataclass(frozen=True)
class ClientUpdatedEvent(BaseEvent):
    """Event emitted when a client is updated.

    Triggered after client fields are modified.

    Hook point: post-client-update
    """

    client_id: int
    client_name: str
    updated_fields: list[str]


@dataclass(frozen=True)
class ClientDeletedEvent(BaseEvent):
    """Event emitted when a client is deleted.

    Triggered after client deletion from database.

    Hook point: post-client-delete
    """

    client_id: int
    client_name: str
    invoice_count: int = 0
    reason: str | None = None
