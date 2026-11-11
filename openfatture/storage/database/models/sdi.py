"""SDI notification log, receipt records, submission claims and identities."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from openfatture.platform.datetime import utc_now

from ..base import Base, IntPKMixin

if TYPE_CHECKING:
    from .billing import Fattura


class LogSDI(IntPKMixin, Base):
    """SDI notification log."""

    __tablename__ = "log_sdi"

    fattura_id: Mapped[int] = mapped_column(ForeignKey("fatture.id"), nullable=False)
    fattura: Mapped[Fattura] = relationship(back_populates="log_sdi")

    # Tipo notifica (RC, NS, MC, NE, DT, AT, EC)
    tipo_notifica: Mapped[str] = mapped_column(String(10), nullable=False)

    # Descrizione
    descrizione: Mapped[str] = mapped_column(Text, nullable=False)

    # File XML ricevuto
    xml_path: Mapped[str | None] = mapped_column(String(500))

    # Data ricezione
    data_ricezione: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    def __repr__(self) -> str:
        return f"<LogSDI(id={self.id}, fattura_id={self.fattura_id}, tipo='{self.tipo_notifica}')>"


class SDINotificationRecord(IntPKMixin, Base):
    """Persisted receipt identity, provenance, and processing outcome."""

    __tablename__ = "sdi_notification_records"
    fingerprint: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    raw_xml: Mapped[str | None] = mapped_column(Text)
    raw_sha256: Mapped[str | None] = mapped_column(String(64), unique=True)
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey("fatture.id"))
    outcome: Mapped[str] = mapped_column(String(40), nullable=False)
    source: Mapped[str] = mapped_column(String(40), default="manual_import", nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)


class SDISubmissionAttempt(IntPKMixin, Base):
    """Durable submission claim; unresolved claims block duplicate sends."""

    __tablename__ = "sdi_submission_attempts"
    invoice_id: Mapped[int] = mapped_column(ForeignKey("fatture.id"), nullable=False, index=True)
    active_invoice_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    xml_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    outcome: Mapped[str] = mapped_column(String(40), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SDIInvoiceIdentity(IntPKMixin, Base):
    """Unique SDI identity claimed atomically by one invoice."""

    __tablename__ = "sdi_invoice_identities"
    identifier: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("fatture.id"), nullable=False, index=True)
