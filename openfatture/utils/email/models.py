"""
Pydantic models for email template contexts.

Type-safe context models for rendering email templates.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

from openfatture.core.batch.processor import BatchResult
from openfatture.sdi.notifiche.parser import NotificaSDI, TipoNotifica
from openfatture.storage.database.models import Cliente, Fattura


class EmailAttachment(BaseModel):
    """Email attachment."""

    filename: str = Field(..., description="Attachment filename")
    content: bytes = Field(..., description="File content (bytes)")
    mime_type: str = Field(default="application/octet-stream", description="MIME type")

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Validate filename is not empty."""
        if not v or not v.strip():
            raise ValueError("Filename cannot be empty")
        return v.strip()

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class EmailMessage(BaseModel):
    """
    Complete email message with HTML and text parts.

    Represents a multipart email with HTML and plain text alternatives.
    """

    subject: str = Field(..., description="Email subject")
    html_body: str = Field(..., description="HTML body")
    text_body: str = Field(..., description="Plain text body (fallback)")
    recipients: list[str] = Field(..., description="Recipient email addresses")
    attachments: list[EmailAttachment] = Field(default_factory=list, description="File attachments")
    reply_to: str | None = Field(None, description="Reply-to address")

    @field_validator("recipients")
    @classmethod
    def validate_recipients(cls, v: list[str]) -> list[str]:
        """Validate recipients list is not empty."""
        if not v:
            raise ValueError("Recipients list cannot be empty")
        return v

    @field_validator("subject", "html_body", "text_body")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Validate string fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


class FatturaInvioContext(BaseModel):
    """
    Context for invoice submission email to SDI.

    Used when sending invoice via PEC to Sistema di Interscambio.
    """

    fattura: Fattura = Field(..., description="Invoice model")
    cedente: dict[str, str] = Field(..., description="Sender company info")
    destinatario: str = Field(..., description="SDI PEC address")
    is_signed: bool = Field(default=False, description="Whether the XML is digitally signed")
    xml_filename: str = Field(..., description="Attached XML filename")

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class NotificaSDIContext(BaseModel):
    """
    Context for SDI notification emails.

    Used when notifying users about SDI events (delivery, rejection, etc.).
    """

    notification: NotificaSDI = Field(..., description="Parsed SDI notification")
    fattura: Fattura = Field(..., description="Related invoice")
    cliente: Cliente = Field(..., description="Invoice client/customer")
    tipo_notifica: TipoNotifica = Field(..., description="Notification type")
    timestamp: datetime = Field(default_factory=datetime.now, description="Notification timestamp")

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class BatchSummaryContext(BaseModel):
    """
    Context for batch operation summary email.

    Used when sending batch operation results to administrators.
    """

    result: BatchResult = Field(..., description="Batch operation result")
    operation_type: str = Field(
        ..., description="Type of operation (import, export, validate, send)"
    )
    timestamp: datetime = Field(default_factory=datetime.now, description="Operation timestamp")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional details")
    csv_report_path: Path | None = Field(None, description="Path to CSV report (if generated)")

    @field_validator("operation_type")
    @classmethod
    def validate_operation_type(cls, v: str) -> str:
        """Validate operation type."""
        allowed = ["import", "export", "validate", "send", "update", "other"]
        if v not in allowed:
            raise ValueError(f"Operation type must be one of: {', '.join(allowed)}")
        return v

    @property
    def duration_formatted(self) -> str:
        """Get formatted duration string."""
        if self.result.duration is None:
            return "N/A"

        duration = self.result.duration
        if duration < 60:
            return f"{duration:.1f}s"
        elif duration < 3600:
            minutes = duration / 60
            return f"{minutes:.1f}m"
        else:
            hours = duration / 3600
            return f"{hours:.1f}h"

    @property
    def success_rate_formatted(self) -> str:
        """Get formatted success rate."""
        return f"{self.result.success_rate:.1f}%"

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class EmailTestContext(BaseModel):
    """
    Context for test email.

    Used when testing PEC configuration.
    """

    smtp_server: str = Field(..., description="SMTP server address")
    smtp_port: int = Field(..., description="SMTP port")
    pec_address: str = Field(..., description="PEC email address")
    test_time: datetime = Field(default_factory=datetime.now, description="Test timestamp")

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class InvoiceSummary(BaseModel):
    """
    Invoice summary for email display.

    Simplified invoice data for email templates.
    """

    numero: str = Field(..., description="Invoice number")
    anno: int = Field(..., description="Invoice year")
    data_emissione: str = Field(..., description="Issue date (formatted)")
    cliente_denominazione: str = Field(..., description="Client name")
    imponibile: str = Field(..., description="Subtotal (formatted)")
    iva: str = Field(..., description="VAT amount (formatted)")
    totale: str = Field(..., description="Total amount (formatted)")
    stato: str = Field(..., description="Invoice status")
    numero_sdi: str | None = Field(None, description="SDI identifier")

    @classmethod
    def from_fattura(cls, fattura: Fattura) -> "InvoiceSummary":
        """
        Create InvoiceSummary from Fattura model.

        Args:
            fattura: Fattura model instance

        Returns:
            InvoiceSummary instance
        """
        return cls(
            numero=fattura.numero,
            anno=fattura.anno,
            data_emissione=fattura.data_emissione.strftime("%d/%m/%Y"),
            cliente_denominazione=fattura.cliente.denominazione,
            imponibile=f"€{fattura.imponibile:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", "."),
            iva=f"€{fattura.iva:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            totale=f"€{fattura.totale:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            stato=fattura.stato.value.upper(),
            numero_sdi=fattura.numero_sdi,
        )


class ErrorDetail(BaseModel):
    """
    Error detail for email display.

    Represents a single error in batch operations or SDI rejections.
    """

    code: str | None = Field(None, description="Error code")
    message: str = Field(..., description="Error message")
    context: str | None = Field(None, description="Additional context")

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True
