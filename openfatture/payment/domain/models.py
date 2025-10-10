"""Domain models for payment tracking system.

DDD Entities:
- Have identity (unique ID)
- Mutable lifecycle
- Encapsulate business logic
- Mapped to database tables via SQLAlchemy
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Date, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...storage.database.base import Base
from .enums import ImportSource, MatchType, ReminderStatus, ReminderStrategy, TransactionStatus

if TYPE_CHECKING:
    from ...storage.database.models import Pagamento
    from .payment_allocation import PaymentAllocation


class BankAccount(Base):
    """Bank account entity for tracking payment sources.

    Represents a bank account from which transactions are imported.
    Supports multiple Italian and European banks.

    Attributes:
        name: Friendly name for the account (e.g., "Intesa Business Account")
        iban: International Bank Account Number (27 chars for Italy)
        bic_swift: Bank Identifier Code (8-11 chars)
        bank_name: Name of the bank (e.g., "Intesa Sanpaolo")
        currency: Currency code (ISO 4217, default EUR)
        opening_balance: Account balance at opening date
        current_balance: Current account balance (updated on transaction import)
        last_sync_date: Last time transactions were imported
        is_active: Whether this account is currently active
        notes: Additional notes
    """

    __tablename__ = "bank_accounts"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    iban: Mapped[str | None] = mapped_column(String(27), unique=True, index=True)
    bic_swift: Mapped[str | None] = mapped_column(String(11))
    bank_name: Mapped[str | None] = mapped_column(String(100))
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)

    # Balances
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    current_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))

    # Sync tracking
    last_sync_date: Mapped[datetime | None] = mapped_column()

    # Status
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    transactions: Mapped[list["BankTransaction"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )

    def update_balance(self, amount: Decimal) -> None:
        """Update current balance by adding transaction amount.

        Positive amount = incoming payment
        Negative amount = outgoing payment
        """
        self.current_balance += amount

    def __repr__(self) -> str:
        return f"<BankAccount(id={self.id}, name='{self.name}', iban='{self.iban}')>"


class BankTransaction(Base):
    """Bank transaction entity for reconciliation.

    Represents a single transaction imported from a bank statement.
    Can be matched to a payment via reconciliation algorithms.

    Attributes:
        id: Unique transaction ID (UUID)
        account_id: Foreign key to BankAccount
        date: Transaction date
        amount: Transaction amount (positive=incoming, negative=outgoing)
        description: Transaction description from bank
        reference: Bank reference/memo field
        counterparty: Name of the other party (if available)
        counterparty_iban: IBAN of the other party (if available)
        status: Matching status (UNMATCHED/MATCHED/IGNORED)
        matched_payment_id: FK to Pagamento if matched
        match_confidence: Confidence score of the match (0.0-1.0)
        match_type: Type of matching algorithm used
        import_source: Source of import (CSV/OFX/QIF/MANUAL)
        raw_data: Original transaction data as JSON
    """

    __tablename__ = "bank_transactions"

    # Override Base's id to use UUID instead of Integer
    # Use UUID for better security and distributed systems
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )

    # Bank account relationship
    account_id: Mapped[int] = mapped_column(ForeignKey("bank_accounts.id"), nullable=False)
    account: Mapped["BankAccount"] = relationship(back_populates="transactions")

    # Transaction details
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    reference: Mapped[str | None] = mapped_column(String(200))

    # Counterparty info (if available from bank)
    counterparty: Mapped[str | None] = mapped_column(String(200))
    counterparty_iban: Mapped[str | None] = mapped_column(String(27), index=True)

    # Matching status
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus), nullable=False, default=TransactionStatus.UNMATCHED, index=True
    )

    # Matched payment (nullable until matched)
    matched_payment_id: Mapped[int | None] = mapped_column(ForeignKey("pagamenti.id"))
    matched_payment: Mapped["Pagamento | None"] = relationship(foreign_keys=[matched_payment_id])

    match_confidence: Mapped[float | None] = mapped_column()
    match_type: Mapped[MatchType | None] = mapped_column(Enum(MatchType))

    # Import metadata
    import_source: Mapped[ImportSource] = mapped_column(
        Enum(ImportSource), nullable=False, default=ImportSource.MANUAL
    )
    import_date: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    # Store original data for debugging/audit trail
    raw_data: Mapped[dict | None] = mapped_column(JSON)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text)

    # Allocations
    allocations: Mapped[list["PaymentAllocation"]] = relationship(
        "PaymentAllocation",
        back_populates="transaction",
        cascade="all, delete-orphan",
    )

    def match_to_payment(
        self, payment: "Pagamento", confidence: float, match_type: MatchType
    ) -> None:
        """Match this transaction to a payment.

        Args:
            payment: The payment to match to
            confidence: Match confidence score (0.0-1.0)
            match_type: Type of matching algorithm used
        """
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {confidence}")

        self.matched_payment_id = payment.id
        self.match_confidence = confidence
        self.match_type = match_type
        self.status = TransactionStatus.MATCHED

    def unmatch(self) -> None:
        """Unmatch this transaction from its payment."""
        self.matched_payment_id = None
        self.match_confidence = None
        self.match_type = None
        self.status = TransactionStatus.UNMATCHED

    def ignore(self) -> None:
        """Mark this transaction as ignored (not relevant for reconciliation)."""
        self.status = TransactionStatus.IGNORED

    @property
    def is_incoming(self) -> bool:
        """Whether this is an incoming payment (positive amount)."""
        return self.amount > 0

    @property
    def is_outgoing(self) -> bool:
        """Whether this is an outgoing payment (negative amount)."""
        return self.amount < 0

    def __repr__(self) -> str:
        return (
            f"<BankTransaction(id={self.id}, "
            f"date={self.date}, "
            f"amount={self.amount}, "
            f"status='{self.status.value}')>"
        )


class PaymentReminder(Base):
    """Payment reminder entity for automated notifications.

    Represents a scheduled reminder for an upcoming or overdue payment.
    Supports multiple reminder strategies (DEFAULT/AGGRESSIVE/GENTLE/MINIMAL).

    Attributes:
        payment_id: Foreign key to Pagamento
        reminder_date: When the reminder should be sent
        status: Reminder status (PENDING/SENT/FAILED/CANCELLED)
        strategy: Reminder strategy used
        email_template: Name of the email template to use
        email_subject: Email subject line
        email_body: Email body content
        sent_date: When the reminder was actually sent
        error_message: Error message if sending failed
    """

    __tablename__ = "payment_reminders"

    # Payment relationship
    payment_id: Mapped[int] = mapped_column(ForeignKey("pagamenti.id"), nullable=False, index=True)
    payment: Mapped["Pagamento"] = relationship()

    # Scheduling
    reminder_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[ReminderStatus] = mapped_column(
        Enum(ReminderStatus), nullable=False, default=ReminderStatus.PENDING, index=True
    )
    strategy: Mapped[ReminderStrategy] = mapped_column(
        Enum(ReminderStrategy), nullable=False, default=ReminderStrategy.DEFAULT
    )

    # Email content
    email_template: Mapped[str] = mapped_column(String(100), default="default")
    email_subject: Mapped[str | None] = mapped_column(String(200))
    email_body: Mapped[str | None] = mapped_column(Text)

    # Tracking
    sent_date: Mapped[datetime | None] = mapped_column()
    error_message: Mapped[str | None] = mapped_column(Text)

    def mark_sent(self) -> None:
        """Mark this reminder as sent."""
        self.status = ReminderStatus.SENT
        self.sent_date = datetime.utcnow()

    def mark_failed(self, error: str) -> None:
        """Mark this reminder as failed with an error message."""
        self.status = ReminderStatus.FAILED
        self.error_message = error

    def cancel(self) -> None:
        """Cancel this reminder (e.g., payment received before reminder sent)."""
        self.status = ReminderStatus.CANCELLED

    @property
    def is_overdue_reminder(self) -> bool:
        """Whether this is a reminder for an overdue payment (sent after due date)."""
        if not self.payment:
            return False
        return self.reminder_date > self.payment.data_scadenza

    def __repr__(self) -> str:
        return (
            f"<PaymentReminder(id={self.id}, "
            f"payment_id={self.payment_id}, "
            f"reminder_date={self.reminder_date}, "
            f"status='{self.status.value}')>"
        )
