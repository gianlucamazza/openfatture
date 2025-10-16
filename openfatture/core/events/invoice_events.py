"""Invoice lifecycle events.

Events emitted during invoice operations (creation, validation, sending, deletion).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .base import BaseEvent


@dataclass(frozen=True)
class InvoiceCreatedEvent(BaseEvent):
    """Event emitted when a new invoice is created.

    Triggered after invoice is saved to database but before any validation or sending.

    Hook point: post-invoice-create
    """

    invoice_id: int
    invoice_number: str
    client_id: int
    client_name: str
    total_amount: Decimal
    currency: str = "EUR"


@dataclass(frozen=True)
class InvoiceValidatedEvent(BaseEvent):
    """Event emitted after invoice XML validation.

    Triggered after FatturaPA XML generation and XSD validation.

    Hook point: post-invoice-validate
    """

    invoice_id: int
    invoice_number: str
    validation_status: str  # "passed" | "failed"
    issues: list[str]
    xml_path: str | None = None


@dataclass(frozen=True)
class InvoiceSentEvent(BaseEvent):
    """Event emitted when invoice is sent via PEC to SDI.

    Triggered after successful PEC email transmission.

    Hook point: post-invoice-send
    """

    invoice_id: int
    invoice_number: str
    recipient: str  # PEC address or SDI codice destinatario
    pec_address: str
    xml_path: str
    signed: bool = False


@dataclass(frozen=True)
class InvoiceDeletedEvent(BaseEvent):
    """Event emitted when an invoice is deleted.

    Triggered after invoice deletion from database.

    Hook point: post-invoice-delete
    """

    invoice_id: int
    invoice_number: str
    reason: str | None = None
