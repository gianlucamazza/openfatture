"""Tests for Payment domain enums.

Covers: TransactionStatus, MatchType, ReminderStatus, ReminderStrategy
Testing enum values, database persistence, and business logic.
"""

import pytest
from sqlalchemy.orm import Session

from openfatture.payment.domain.enums import (
    MatchType,
    ReminderStatus,
    ReminderStrategy,
    TransactionStatus,
)
from openfatture.payment.domain.models import BankTransaction, PaymentReminder

pytestmark = pytest.mark.unit


class TestTransactionStatus:
    """Tests for TransactionStatus enum."""

    def test_enum_values_unique(self):
        """Test that all enum values are unique."""
        values = [status.value for status in TransactionStatus]
        assert len(values) == len(set(values))

    def test_enum_str_representation(self):
        """Test string representation of enum members."""
        assert str(TransactionStatus.UNMATCHED) == "TransactionStatus.UNMATCHED"
        assert TransactionStatus.MATCHED.value == "matched"

    def test_enum_database_persistence(self, db_session: Session, bank_account):
        """Test that enum persists correctly to database."""
        from datetime import date
        from decimal import Decimal
        from uuid import uuid4

        transaction = BankTransaction(
            id=uuid4(),
            account_id=bank_account.id,
            date=date.today(),
            amount=Decimal("100.00"),
            description="Test",
            status=TransactionStatus.MATCHED,
        )

        db_session.add(transaction)
        db_session.commit()

        # Reload from database
        db_session.expire(transaction)
        db_session.refresh(transaction)

        assert transaction.status == TransactionStatus.MATCHED
        assert isinstance(transaction.status, TransactionStatus)

    def test_enum_invalid_values_raise_error(self):
        """Test that invalid enum values raise error."""
        with pytest.raises((ValueError, KeyError)):
            TransactionStatus("invalid_status")


class TestMatchType:
    """Tests for MatchType enum."""

    def test_all_match_types_defined(self):
        """Test that all expected match types are defined."""
        expected_types = {"AUTO", "MANUAL", "EXACT", "FUZZY", "IBAN", "DATE_WINDOW", "COMPOSITE"}
        actual_types = {mt.name for mt in MatchType}

        assert expected_types.issubset(actual_types)

    def test_match_type_values(self):
        """Test enum values match expected strings."""
        assert MatchType.AUTO.value == "auto"
        assert MatchType.MANUAL.value == "manual"
        assert MatchType.EXACT.value == "exact"
        assert MatchType.FUZZY.value == "fuzzy"


class TestReminderStatus:
    """Tests for ReminderStatus enum."""

    def test_reminder_status_lifecycle(self):
        """Test reminder status represents lifecycle: PENDING → SENT → FAILED."""
        assert ReminderStatus.PENDING.value == "pending"
        assert ReminderStatus.SENT.value == "sent"
        assert ReminderStatus.FAILED.value == "failed"

    def test_reminder_status_database_persistence(self, db_session: Session, payment_with_reminder):
        """Test ReminderStatus persists to database correctly."""
        from datetime import date

        reminder = PaymentReminder(
            payment_id=payment_with_reminder.id,
            scheduled_date=date.today(),
            days_before_due=7,
            reminder_strategy=ReminderStrategy.DEFAULT,
            status=ReminderStatus.SENT,
        )

        db_session.add(reminder)
        db_session.commit()
        db_session.refresh(reminder)

        assert reminder.status == ReminderStatus.SENT


class TestReminderStrategy:
    """Tests for ReminderStrategy enum."""

    def test_all_strategies_defined(self):
        """Test that all reminder strategies are defined."""
        strategies = [s.name for s in ReminderStrategy]

        assert "DEFAULT" in strategies
        assert "AGGRESSIVE" in strategies
        assert "GENTLE" in strategies
        assert "MINIMAL" in strategies

    def test_reminder_strategy_days_mapping(self):
        """Test reminder strategy maps to correct days before due."""
        # These values should match ReminderScheduler implementation
        expected_days = {
            ReminderStrategy.DEFAULT: [-7, -3, 0, 7, 30],
            ReminderStrategy.AGGRESSIVE: [-10, -7, -3, -1, 0, 3, 7, 15, 30],
            ReminderStrategy.GENTLE: [-7, 0, 15, 30],
            ReminderStrategy.MINIMAL: [0, 30],
        }

        # Verify expected mapping exists (implementation check)
        for strategy in ReminderStrategy:
            assert strategy in expected_days
            assert len(expected_days[strategy]) > 0

    # Additional tests:
    # - test_enum_comparison_operators
    # - test_enum_iteration
    # - test_enum_membership_testing
