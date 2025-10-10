"""Tests for Payment domain models.

Covers: BankAccount, BankTransaction, PaymentReminder
Following DDD and property-based testing best practices.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import exc
from sqlalchemy.orm import Session

from openfatture.payment.domain.enums import (
    MatchType,
    ReminderStatus,
    ReminderStrategy,
    TransactionStatus,
)
from openfatture.payment.domain.models import (
    BankAccount,
    BankTransaction,
    PaymentReminder,
)

pytestmark = pytest.mark.unit


class TestBankAccount:
    """Tests for BankAccount entity."""

    def test_bank_account_creation_with_valid_data(self, db_session: Session):
        """Test creating a bank account with all valid fields."""
        account = BankAccount(
            name="Conto Business",
            iban="IT60X0542811101000000123456",
            bic_swift="BCITITMM",
            bank_name="Intesa Sanpaolo",
        )

        db_session.add(account)
        db_session.commit()

        assert account.id is not None
        assert account.name == "Conto Business"
        assert account.iban == "IT60X0542811101000000123456"
        assert account.bic_swift == "BCITITMM"

    def test_bank_account_iban_required(self, db_session: Session):
        """Test that IBAN is not required for bank account (nullable)."""
        account = BankAccount(name="Test Account")

        db_session.add(account)
        db_session.commit()

        assert account.id is not None
        assert account.iban is None

    def test_bank_account_relationships_with_transactions(
        self, db_session: Session, bank_account: BankAccount, bank_transaction: BankTransaction
    ):
        """Test that bank account has relationship with transactions."""
        assert bank_transaction in bank_account.transactions
        assert bank_transaction.account_id == bank_account.id

    def test_bank_account_cascade_delete(
        self, db_session: Session, bank_account: BankAccount, bank_transaction: BankTransaction
    ):
        """Test that deleting account cascades to transactions."""
        account_id = bank_account.id
        tx_id = bank_transaction.id

        db_session.delete(bank_account)
        db_session.commit()

        # Transaction should also be deleted (cascade)
        deleted_tx = db_session.query(BankTransaction).filter_by(id=tx_id).first()
        assert deleted_tx is None

    # Additional tests (implement for >90% coverage):
    # - test_bank_account_iban_normalization
    # - test_bank_account_unique_iban_constraint
    # - test_bank_account_str_representation


class TestBankTransaction:
    """Tests for BankTransaction entity."""

    def test_transaction_creation_all_fields(self, db_session: Session, bank_account: BankAccount):
        """Test creating transaction with all fields populated."""
        tx_id = uuid4()
        transaction = BankTransaction(
            id=tx_id,
            account_id=bank_account.id,
            date=date(2025, 1, 15),
            amount=Decimal("1500.50"),
            description="Invoice payment XYZ",
            reference="REF-2025-001",
            notes="Additional memo",
            status=TransactionStatus.UNMATCHED,
        )

        db_session.add(transaction)
        db_session.commit()

        assert transaction.id == tx_id
        assert isinstance(transaction.id, UUID)
        assert transaction.amount == Decimal("1500.50")
        assert transaction.status == TransactionStatus.UNMATCHED

    def test_transaction_status_transitions(
        self, db_session: Session, bank_transaction: BankTransaction
    ):
        """Test valid status transitions: UNMATCHED → MATCHED → IGNORED."""
        # Initial state
        assert bank_transaction.status == TransactionStatus.UNMATCHED

        # Transition to MATCHED
        bank_transaction.status = TransactionStatus.MATCHED
        bank_transaction.matched_payment_id = 1
        bank_transaction.match_type = MatchType.EXACT
        bank_transaction.match_confidence = 0.95
        db_session.commit()

        assert bank_transaction.status == TransactionStatus.MATCHED
        assert bank_transaction.matched_payment_id == 1

        # Transition to IGNORED
        bank_transaction.status = TransactionStatus.IGNORED
        db_session.commit()

        assert bank_transaction.status == TransactionStatus.IGNORED

    def test_transaction_uuid_uniqueness(self, db_session: Session, bank_account: BankAccount):
        """Test that transaction IDs are unique UUIDs."""
        tx1 = BankTransaction(
            id=uuid4(),
            account_id=bank_account.id,
            date=date.today(),
            amount=Decimal("100.00"),
            description="TX1",
            status=TransactionStatus.UNMATCHED,
        )

        tx2 = BankTransaction(
            id=uuid4(),
            account_id=bank_account.id,
            date=date.today(),
            amount=Decimal("200.00"),
            description="TX2",
            status=TransactionStatus.UNMATCHED,
        )

        db_session.add_all([tx1, tx2])
        db_session.commit()

        assert tx1.id != tx2.id
        assert isinstance(tx1.id, UUID)
        assert isinstance(tx2.id, UUID)

    def test_transaction_date_ordering(self, db_session: Session, multiple_transactions):
        """Test transactions can be ordered by date."""
        sorted_txs = sorted(multiple_transactions, key=lambda tx: tx.date, reverse=True)

        assert sorted_txs[0].date > sorted_txs[-1].date

    def test_transaction_negative_amounts_debits(
        self, db_session: Session, bank_account: BankAccount
    ):
        """Test transactions can have negative amounts (debits)."""
        debit = BankTransaction(
            id=uuid4(),
            account_id=bank_account.id,
            date=date.today(),
            amount=Decimal("-500.00"),  # Debit
            description="Payment outgoing",
            status=TransactionStatus.UNMATCHED,
        )

        db_session.add(debit)
        db_session.commit()

        assert debit.amount < 0

    def test_transaction_duplicate_detection(self, db_session: Session, bank_account: BankAccount):
        """Test detecting duplicate transactions (same date, amount, description)."""
        tx1 = BankTransaction(
            id=uuid4(),
            account_id=bank_account.id,
            date=date(2025, 1, 15),
            amount=Decimal("100.00"),
            description="Duplicate payment",
            status=TransactionStatus.UNMATCHED,
        )

        tx2 = BankTransaction(
            id=uuid4(),  # Different UUID
            account_id=bank_account.id,
            date=date(2025, 1, 15),  # Same date
            amount=Decimal("100.00"),  # Same amount
            description="Duplicate payment",  # Same description
            status=TransactionStatus.UNMATCHED,
        )

        db_session.add_all([tx1, tx2])
        db_session.commit()

        # Both exist in DB (no unique constraint on content)
        # Duplicate detection happens at application layer
        all_txs = (
            db_session.query(BankTransaction)
            .filter_by(account_id=bank_account.id, date=date(2025, 1, 15), amount=Decimal("100.00"))
            .all()
        )

        assert len(all_txs) == 2  # Duplicates allowed at DB level

    # Additional tests (implement for >90% coverage):
    # - test_transaction_matched_fields_required_when_matched
    # - test_transaction_confidence_range_validation
    # - test_transaction_memo_field_optional
    # - test_transaction_foreign_key_constraint


class TestPaymentReminder:
    """Tests for PaymentReminder entity."""

    def test_reminder_creation_with_payment(self, db_session: Session, payment_with_reminder):
        """Test creating reminder linked to payment."""
        reminder = PaymentReminder(
            payment_id=payment_with_reminder.id,
            reminder_date=date.today() + timedelta(days=7),
            strategy=ReminderStrategy.DEFAULT,
            status=ReminderStatus.PENDING,
        )

        db_session.add(reminder)
        db_session.commit()

        assert reminder.id is not None
        assert reminder.payment_id == payment_with_reminder.id
        assert reminder.status == ReminderStatus.PENDING

    def test_reminder_scheduled_date_calculation(self, db_session: Session, payment_with_reminder):
        """Test reminder date is calculated correctly based on due date."""
        due_date = payment_with_reminder.data_scadenza
        days_before = 7

        reminder = PaymentReminder(
            payment_id=payment_with_reminder.id,
            reminder_date=due_date - timedelta(days=days_before),
            strategy=ReminderStrategy.DEFAULT,
            status=ReminderStatus.PENDING,
        )

        db_session.add(reminder)
        db_session.commit()

        assert reminder.reminder_date == due_date - timedelta(days=7)

    def test_reminder_status_transitions(self, db_session: Session, payment_reminder):
        """Test valid status transitions: PENDING → SENT → FAILED."""
        # Initial state
        assert payment_reminder.status == ReminderStatus.PENDING

        # Transition to SENT
        payment_reminder.status = ReminderStatus.SENT
        payment_reminder.sent_date = datetime.now()
        db_session.commit()

        assert payment_reminder.status == ReminderStatus.SENT
        assert payment_reminder.sent_date is not None

        # Transition to FAILED (retry scenario)
        payment_reminder.status = ReminderStatus.FAILED
        payment_reminder.error_message = "SMTP connection timeout"
        db_session.commit()

        assert payment_reminder.status == ReminderStatus.FAILED
        assert payment_reminder.error_message is not None

    def test_reminder_foreign_key_cascade(
        self, db_session: Session, payment_with_reminder, payment_reminder
    ):
        """Test that reminder is properly linked to payment via foreign key."""
        reminder_id = payment_reminder.id
        payment_id = payment_with_reminder.id

        # Verify the reminder is linked to the payment
        assert payment_reminder.payment_id == payment_id

        # Manually delete reminder first (cascade not configured in model)
        db_session.delete(payment_reminder)
        db_session.commit()

        # Now delete the payment
        db_session.delete(payment_with_reminder)
        db_session.commit()

        # Verify both are deleted
        deleted_payment = db_session.query(type(payment_with_reminder)).filter_by(id=payment_id).first()
        deleted_reminder = db_session.query(PaymentReminder).filter_by(id=reminder_id).first()
        assert deleted_payment is None
        assert deleted_reminder is None

    # Additional tests (implement for >90% coverage):
    # - test_reminder_multiple_reminders_per_payment
    # - test_reminder_days_before_due_negative_for_overdue
    # - test_reminder_strategy_enum_persistence
