"""Domain model for tracking payment allocations against bank transactions."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...storage.database.base import Base
from .enums import MatchType

if TYPE_CHECKING:
    from ...storage.database.models import Pagamento
    from .models import BankTransaction


class PaymentAllocation(Base):
    """Allocation of a bank transaction (or portion) to a payment record.

    Tracks the exact amount applied, confidence score, and metadata so we can
    manage partial payments, reversals, and audit history.
    """

    __tablename__ = "payment_allocations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("pagamenti.id"), nullable=False, index=True)
    transaction_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bank_transactions.id"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    allocated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    match_type: Mapped[MatchType | None] = mapped_column(Enum(MatchType))
    match_confidence: Mapped[float | None] = mapped_column()
    notes: Mapped[str | None] = mapped_column(Text)

    payment: Mapped["Pagamento"] = relationship(back_populates="allocations")
    transaction: Mapped["BankTransaction"] = relationship(back_populates="allocations")

    def __repr__(self) -> str:
        return (
            f"<PaymentAllocation(id={self.id}, payment_id={self.payment_id}, "
            f"transaction_id='{self.transaction_id}', amount={self.amount})>"
        )
