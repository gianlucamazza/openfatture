"""SDI (Sistema di Interscambio) notification events.

Events emitted when SDI notifications are received and processed.
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import BaseEvent


@dataclass(frozen=True)
class SDINotificationReceivedEvent(BaseEvent):
    """Event emitted when an SDI notification is received and processed.

    Triggered after parsing SDI notification XML (RC, NS, MC, DT, AT, etc.).

    Hook point: on-sdi-notification
    """

    notification_type: str  # RC, NS, MC, DT, AT, NE
    invoice_id: int
    invoice_number: str
    message: str
    notification_id: int | None = None
    file_path: str | None = None
