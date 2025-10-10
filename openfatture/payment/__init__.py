"""Payment tracking and reconciliation system.

This module implements payment tracking with:
- Bank transaction import (CSV/OFX/QIF)
- Fuzzy matching algorithms (5 strategies)
- Auto-reconciliation engine
- Automated reminder system
- Payment analytics
- Prometheus metrics monitoring

Architecture: Domain-Driven Design (DDD) + Hexagonal Architecture
"""

__all__ = [
    "BankTransaction",
    "BankAccount",
    "PaymentReminder",
    "MatchResult",
    "ReconciliationResult",
    "ImportResult",
    "TransactionStatus",
    "MatchType",
    "ReminderStatus",
    # Metrics
    "start_metrics_server",
    "record_transaction_import",
    "record_reconciliation",
    "record_reminder_sent",
]

from .domain.enums import MatchType, ReminderStatus, TransactionStatus
from .domain.models import BankAccount, BankTransaction, PaymentReminder
from .domain.value_objects import ImportResult, MatchResult, ReconciliationResult

# Import metrics (auto-starts server if PROMETHEUS_ENABLED=true)
from .metrics import (
    record_reconciliation,
    record_reminder_sent,
    record_transaction_import,
    start_metrics_server,
)
