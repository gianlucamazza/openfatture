"""Payment schedule and collection ledger models."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, IntPKMixin

if TYPE_CHECKING:
    from ....payment.domain.payment_allocation import PaymentAllocation
    from .billing import Fattura


class StatoPagamento(PyEnum):
    """Payment status."""

    DA_PAGARE = "da_pagare"  # To be paid
    PAGATO_PARZIALE = "pagato_parziale"  # Partially paid
    PAGATO = "pagato"  # Paid
    SCADUTO = "scaduto"  # Overdue


class Pagamento(IntPKMixin, Base):
    """Payment tracking."""

    __tablename__ = "pagamenti"

    fattura_id: Mapped[int] = mapped_column(ForeignKey("fatture.id"), nullable=False)
    fattura: Mapped[Fattura] = relationship(back_populates="pagamenti")

    # Importo
    importo: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    importo_pagato: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )

    # Date
    data_scadenza: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_pagamento: Mapped[date | None] = mapped_column(Date)

    # Payment terms (0 = immediate, N = N days from invoice date)
    giorni_scadenza: Mapped[int] = mapped_column(Integer, default=30)

    # Stato
    stato: Mapped[StatoPagamento] = mapped_column(
        Enum(StatoPagamento), nullable=False, default=StatoPagamento.DA_PAGARE
    )

    # Modalità (Bonifico, Contanti, RiBa, ecc.)
    modalita: Mapped[str] = mapped_column(String(50), default="Bonifico")

    # Riferimenti bancari
    iban: Mapped[str | None] = mapped_column(String(27))
    bic_swift: Mapped[str | None] = mapped_column(String(11))

    # Note
    note: Mapped[str | None] = mapped_column(Text)

    # Relationships
    allocations: Mapped[list[PaymentAllocation]] = relationship(
        "PaymentAllocation", back_populates="payment", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Pagamento(id={self.id}, fattura_id={self.fattura_id}, importo={self.importo}, stato='{self.stato.value}')>"

    @property
    def importo_da_pagare(self) -> Decimal:
        """Total amount due for the payment (alias of importo column)."""
        return self.importo

    @importo_da_pagare.setter
    def importo_da_pagare(self, value: Decimal | float | str) -> None:
        """Allow assignments using semantic name expected by services/tests."""
        self.importo = Decimal(str(value))

    @property
    def saldo_residuo(self) -> Decimal:
        """Outstanding balance still to be paid."""
        outstanding = Decimal(self.importo_da_pagare) - Decimal(self.importo_pagato or 0)
        if outstanding < Decimal("0.00"):
            return Decimal("0.00")
        return outstanding

    def apply_payment(self, amount: Decimal, pagamento_effective_date: date | None = None) -> None:
        """Record a payment allocation against this Pagamento."""
        amount_decimal = Decimal(str(amount))
        if amount_decimal <= Decimal("0.00"):
            raise ValueError("Payment amount must be positive")

        nuovo_pagato = Decimal(self.importo_pagato or 0) + amount_decimal
        if nuovo_pagato > Decimal(self.importo_da_pagare):
            nuovo_pagato = Decimal(self.importo_da_pagare)

        self.importo_pagato = nuovo_pagato

        if self.importo_pagato >= self.importo_da_pagare:
            self.stato = StatoPagamento.PAGATO
            if pagamento_effective_date:
                self.data_pagamento = pagamento_effective_date
        elif self.importo_pagato > Decimal("0.00"):
            self.stato = StatoPagamento.PAGATO_PARZIALE
            if pagamento_effective_date and self.data_pagamento is None:
                self.data_pagamento = pagamento_effective_date

    def revert_payment(self, amount: Decimal) -> None:
        """Roll back a previously applied payment amount."""
        amount_decimal = Decimal(str(amount))
        if amount_decimal <= Decimal("0.00"):
            raise ValueError("Revert amount must be positive")

        current_paid = Decimal(self.importo_pagato or 0)
        if amount_decimal > current_paid:
            raise ValueError(
                f"Cannot revert {amount_decimal} because only {current_paid} has been paid"
            )

        nuovo_pagato = current_paid - amount_decimal
        self.importo_pagato = nuovo_pagato

        if nuovo_pagato <= Decimal("0.00"):
            self.stato = StatoPagamento.DA_PAGARE
            self.data_pagamento = None
        elif nuovo_pagato < Decimal(self.importo_da_pagare):
            self.stato = StatoPagamento.PAGATO_PARZIALE
        else:
            self.stato = StatoPagamento.PAGATO


class CollectionReceipt(IntPKMixin, Base):
    """One incoming amount, independent of invoices and due dates."""

    __tablename__ = "collection_receipts"
    __table_args__ = (
        CheckConstraint(
            "amount > 0 AND allocated >= 0 AND allocated <= amount", name="receipt_budget"
        ),
    )
    request_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    bank_transaction_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("bank_transactions.id", ondelete="RESTRICT"), unique=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    effective_date: Mapped[date | None] = mapped_column(Date)
    origin: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    allocated: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)


class CollectionEntry(IntPKMixin, Base):
    """Append-only allocation or reversal against an invoice."""

    __tablename__ = "collection_entries"
    __table_args__ = (CheckConstraint("amount != 0", name="nonzero_collection_entry"),)
    request_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    receipt_id: Mapped[int] = mapped_column(ForeignKey("collection_receipts.id"), nullable=False)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("fatture.id"), nullable=False)
    payment_id: Mapped[int | None] = mapped_column(ForeignKey("pagamenti.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    reverses_id: Mapped[int | None] = mapped_column(ForeignKey("collection_entries.id"))
    notes: Mapped[str | None] = mapped_column(Text)


class CollectionStatement(IntPKMixin, Base):
    """Owner declaration, kept separate from actual money movements."""

    __tablename__ = "collection_statements"
    request_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("fatture.id"), nullable=False)
    value: Mapped[str] = mapped_column(String(20), nullable=False)
    declared_on: Mapped[date | None] = mapped_column(Date)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class CollectionOperation(IntPKMixin, Base):
    """Durable idempotency key and result for multi-step cash operations."""

    __tablename__ = "collection_operations"
    request_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    result: Mapped[str] = mapped_column(Text, nullable=False)


def _register_payment_allocation_model() -> None:
    """Register PaymentAllocation on the shared Base for relationship resolution.

    Imported at module end to avoid circular imports between billing storage
    models and the payment domain package.
    """
    from openfatture.payment.domain.payment_allocation import PaymentAllocation

    assert PaymentAllocation.__tablename__ == "payment_allocations"


_register_payment_allocation_model()
