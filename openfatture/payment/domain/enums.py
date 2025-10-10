"""Domain enums for payment tracking system."""

from enum import Enum


class TransactionStatus(str, Enum):
    """Bank transaction matching status.

    Lifecycle:
        UNMATCHED → MATCHED (after auto-reconciliation)
        UNMATCHED → IGNORED (manual action)
        MATCHED → UNMATCHED (undo reconciliation)
    """

    UNMATCHED = "unmatched"  # Transaction not yet matched to any payment
    MATCHED = "matched"  # Transaction successfully matched
    IGNORED = "ignored"  # Transaction manually marked as irrelevant

    def __str__(self) -> str:
        return self.value


class MatchType(str, Enum):
    """Type of payment matching algorithm used.

    Confidence levels:
        EXACT: 1.0 (perfect match)
        FUZZY: 0.7-0.95 (high confidence)
        MANUAL: 1.0 (user-confirmed)
        AUTO: varies (composite score)
    """

    EXACT = "exact"  # Exact amount + date match
    FUZZY = "fuzzy"  # Fuzzy string matching (Levenshtein)
    IBAN = "iban"  # IBAN match in reference
    DATE_WINDOW = "date_window"  # Amount match + date within window
    COMPOSITE = "composite"  # Weighted combination of multiple factors
    MANUAL = "manual"  # User manually reconciled

    def __str__(self) -> str:
        return self.value


class ReminderStatus(str, Enum):
    """Payment reminder status.

    Lifecycle:
        PENDING → SENT (after email dispatch)
        PENDING → CANCELLED (payment received before sending)
        SENT → FAILED (email delivery error)
    """

    PENDING = "pending"  # Reminder scheduled but not sent
    SENT = "sent"  # Reminder successfully sent
    FAILED = "failed"  # Email delivery failed
    CANCELLED = "cancelled"  # Reminder cancelled (payment received)

    def __str__(self) -> str:
        return self.value


class ReminderStrategy(str, Enum):
    """Reminder sending strategy for overdue payments.

    Schedules:
        DEFAULT: -7, -3, 0, +7, +30 days
        AGGRESSIVE: -10, -7, -3, -1, 0, +3, +7, +15, +30 days
        GENTLE: -7, 0, +15, +30 days
        MINIMAL: 0, +30 days only
    """

    DEFAULT = "default"  # Standard reminder schedule
    AGGRESSIVE = "aggressive"  # More frequent reminders
    GENTLE = "gentle"  # Less frequent reminders
    MINIMAL = "minimal"  # Only critical reminders

    def __str__(self) -> str:
        return self.value

    def get_schedule_days(self) -> list[int]:
        """Get reminder schedule in days relative to due date.

        Negative values = before due date
        Positive values = after due date (overdue)
        0 = on due date
        """
        schedules = {
            ReminderStrategy.DEFAULT: [-7, -3, 0, 7, 30],
            ReminderStrategy.AGGRESSIVE: [-10, -7, -3, -1, 0, 3, 7, 15, 30],
            ReminderStrategy.GENTLE: [-7, 0, 15, 30],
            ReminderStrategy.MINIMAL: [0, 30],
        }
        return schedules[self]


class ImportSource(str, Enum):
    """Source of bank transaction import.

    Supported formats:
        CSV: Comma-separated values (custom field mapping)
        OFX: Open Financial Exchange (standard banking format)
        QIF: Quicken Interchange Format (legacy)
        MANUAL: User manually entered transaction
    """

    CSV = "csv"
    OFX = "ofx"
    QIF = "qif"
    MANUAL = "manual"

    def __str__(self) -> str:
        return self.value
