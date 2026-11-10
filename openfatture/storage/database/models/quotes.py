"""Quote (preventivo) models and their lines."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, IntPKMixin

if TYPE_CHECKING:
    from .billing import Cliente, Fattura


class StatoPreventivo(PyEnum):
    """Quote/Estimate status."""

    BOZZA = "bozza"  # Draft
    INVIATO = "inviato"  # Sent to client
    ACCETTATO = "accettato"  # Accepted by client
    RIFIUTATO = "rifiutato"  # Rejected by client
    SCADUTO = "scaduto"  # Expired
    CONVERTITO = "convertito"  # Converted to invoice


class Preventivo(IntPKMixin, Base):
    """Quote/Estimate model."""

    __tablename__ = "preventivi"

    # Numero preventivo (progressivo annuale)
    numero: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    anno: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Date
    data_emissione: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    data_scadenza: Mapped[date] = mapped_column(Date, nullable=False)

    # Cliente
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clienti.id"), nullable=False)
    cliente: Mapped[Cliente] = relationship(back_populates="preventivi")

    # Importi (calcolati dalle righe)
    imponibile: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    iva: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    totale: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    # Stato
    stato: Mapped[StatoPreventivo] = mapped_column(
        Enum(StatoPreventivo), nullable=False, default=StatoPreventivo.BOZZA
    )

    # Note e condizioni
    note: Mapped[str | None] = mapped_column(Text)
    condizioni: Mapped[str | None] = mapped_column(Text)  # Terms and conditions

    # Validità (giorni)
    validita_giorni: Mapped[int] = mapped_column(Integer, default=30)

    # File path (PDF)
    pdf_path: Mapped[str | None] = mapped_column(String(500))

    # Relationships
    righe: Mapped[list[RigaPreventivo]] = relationship(
        back_populates="preventivo", cascade="all, delete-orphan"
    )
    fattura: Mapped[Fattura | None] = relationship(back_populates="preventivo")

    def __repr__(self) -> str:
        return f"<Preventivo(id={self.id}, numero='{self.numero}/{self.anno}', stato='{self.stato.value}')>"


class RigaPreventivo(IntPKMixin, Base):
    """Quote/Estimate line item."""

    __tablename__ = "righe_preventivo"

    preventivo_id: Mapped[int] = mapped_column(ForeignKey("preventivi.id"), nullable=False)
    preventivo: Mapped[Preventivo] = relationship(back_populates="righe")

    # Riga
    numero_riga: Mapped[int] = mapped_column(Integer, nullable=False)

    # Descrizione
    descrizione: Mapped[str] = mapped_column(Text, nullable=False)

    # Quantità e prezzo
    quantita: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=1)
    prezzo_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    unita_misura: Mapped[str] = mapped_column(String(10), default="ore")

    # IVA
    aliquota_iva: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=22.00)
    natura: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Totali
    imponibile: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    iva: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    totale: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    def __repr__(self) -> str:
        return f"<RigaPreventivo(id={self.id}, preventivo_id={self.preventivo_id}, descrizione='{self.descrizione[:30]}...')>"
