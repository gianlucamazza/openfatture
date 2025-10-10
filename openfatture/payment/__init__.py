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
# Optional dependency - only available if prometheus_client is installed
try:
    from .metrics import (
        record_reconciliation,
        record_reminder_sent,
        record_transaction_import,
        start_metrics_server,
    )
except ImportError:
    # Stub functions when prometheus_client is not installed
    def start_metrics_server(port: int = 8000) -> None:  # type: ignore[misc]
        """Stub for start_metrics_server when prometheus_client is not installed."""
        pass

    def record_transaction_import(bank_preset: str, status: str, count: int = 1) -> None:  # type: ignore[misc]
        """Stub for record_transaction_import when prometheus_client is not installed."""
        pass

    def record_reconciliation(match_type: str, status: str = "success") -> None:  # type: ignore[misc]
        """Stub for record_reconciliation when prometheus_client is not installed."""
        pass

    def record_reminder_sent(  # type: ignore[misc]
        strategy: str, notifier_type: str, count: int = 1
    ) -> None:
        """Stub for record_reminder_sent when prometheus_client is not installed."""
        pass
