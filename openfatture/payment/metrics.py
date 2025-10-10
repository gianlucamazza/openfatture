"""Prometheus metrics instrumentation for Payment Tracking module.

Provides metrics collection for monitoring payment reconciliation performance,
transaction volumes, and system health.
"""

import os
from typing import Any

from prometheus_client import Counter, Gauge, Histogram, start_http_server

# ============================================================================
# Metric Definitions
# ============================================================================

# Counter: Bank transactions imported
bank_transactions_imported_total = Counter(
    "openfatture_payment_transactions_imported_total",
    "Total number of bank transactions imported",
    ["bank_preset", "status"],  # labels: intesa/unicredit/etc, success/error/duplicate
)

# Counter: Reconciliations performed
reconciliations_performed_total = Counter(
    "openfatture_payment_reconciliations_performed_total",
    "Total number of transaction reconciliations performed",
    ["match_type", "status"],  # labels: auto/manual/fuzzy/iban, success/failure
)

# Gauge: Unmatched transactions count
unmatched_transactions_count = Gauge(
    "openfatture_payment_unmatched_transactions_count",
    "Current number of unmatched bank transactions",
    ["account_id"],  # label: bank account ID
)

# Histogram: Matching confidence scores
matching_confidence_scores = Histogram(
    "openfatture_payment_matching_confidence_scores",
    "Distribution of matching confidence scores",
    ["matcher_strategy"],  # label: exact/fuzzy/iban/composite
    buckets=(0.0, 0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0),
)

# Counter: Payment reminders sent
payment_reminders_sent_total = Counter(
    "openfatture_payment_reminders_sent_total",
    "Total number of payment reminders sent",
    ["reminder_strategy", "notifier_type"],  # labels: default/aggressive/gentle/minimal, email/console
)

# Histogram: Import processing duration
import_processing_duration_seconds = Histogram(
    "openfatture_payment_import_processing_duration_seconds",
    "Time taken to process bank statement imports",
    ["bank_preset"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

# Histogram: Matching processing duration
matching_processing_duration_seconds = Histogram(
    "openfatture_payment_matching_processing_duration_seconds",
    "Time taken to match transactions",
    ["matcher_strategy"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0),
)

# Gauge: Review queue size
review_queue_size = Gauge(
    "openfatture_payment_review_queue_size",
    "Number of transactions pending manual review",
    ["confidence_range"],  # label: low/medium/high
)

# Counter: CLI command executions
cli_command_executions_total = Counter(
    "openfatture_payment_cli_command_executions_total",
    "Total number of payment CLI command executions",
    ["command", "status"],  # labels: import/match/queue/reminders, success/failure
)


# ============================================================================
# Metrics Server
# ============================================================================


def start_metrics_server(port: int = 8000) -> None:
    """Start Prometheus metrics HTTP server.

    Args:
        port: Port to expose metrics on (default: 8000)
    """
    if os.getenv("PROMETHEUS_ENABLED", "false").lower() == "true":
        try:
            start_http_server(port)
            print(f"✓ Prometheus metrics server started on port {port}")
        except OSError as e:
            # Port already in use, skip
            print(f"✗ Metrics server already running or port {port} in use: {e}")


# ============================================================================
# Convenience Functions
# ============================================================================


def record_transaction_import(bank_preset: str, status: str, count: int = 1) -> None:
    """Record bank transaction import.

    Args:
        bank_preset: Bank identifier (intesa, unicredit, revolut, etc.)
        status: Import status (success, error, duplicate)
        count: Number of transactions
    """
    bank_transactions_imported_total.labels(
        bank_preset=bank_preset or "unknown", status=status
    ).inc(count)


def record_reconciliation(match_type: str, status: str = "success") -> None:
    """Record transaction reconciliation.

    Args:
        match_type: Type of match (auto, manual, fuzzy, iban, exact)
        status: Reconciliation status (success, failure)
    """
    reconciliations_performed_total.labels(match_type=match_type, status=status).inc()


def update_unmatched_count(account_id: int, count: int) -> None:
    """Update unmatched transactions gauge.

    Args:
        account_id: Bank account ID
        count: Current count of unmatched transactions
    """
    unmatched_transactions_count.labels(account_id=str(account_id)).set(count)


def record_matching_confidence(strategy: str, confidence: float) -> None:
    """Record matching confidence score.

    Args:
        strategy: Matcher strategy (exact, fuzzy, iban, composite)
        confidence: Confidence score (0.0-1.0)
    """
    matching_confidence_scores.labels(matcher_strategy=strategy).observe(confidence)


def record_reminder_sent(strategy: str, notifier_type: str, count: int = 1) -> None:
    """Record payment reminder sent.

    Args:
        strategy: Reminder strategy (default, aggressive, gentle, minimal)
        notifier_type: Notifier type (email, console)
        count: Number of reminders sent
    """
    payment_reminders_sent_total.labels(
        reminder_strategy=strategy, notifier_type=notifier_type
    ).inc(count)


def update_review_queue_size(confidence_range: str, count: int) -> None:
    """Update review queue size gauge.

    Args:
        confidence_range: Confidence range (low: 0-0.6, medium: 0.6-0.85, high: 0.85-1.0)
        count: Current queue size
    """
    review_queue_size.labels(confidence_range=confidence_range).set(count)


def record_cli_command(command: str, status: str = "success") -> None:
    """Record CLI command execution.

    Args:
        command: Command name (import, match, queue, reminders)
        status: Execution status (success, failure)
    """
    cli_command_executions_total.labels(command=command, status=status).inc()


# ============================================================================
# Context Managers for Duration Tracking
# ============================================================================


class track_import_duration:
    """Context manager to track import processing duration."""

    def __init__(self, bank_preset: str):
        self.bank_preset = bank_preset
        self.timer: Any = None

    def __enter__(self) -> "track_import_duration":
        self.timer = import_processing_duration_seconds.labels(
            bank_preset=self.bank_preset or "unknown"
        ).time()
        self.timer.__enter__()
        return self

    def __exit__(self, *args: Any) -> None:
        if self.timer:
            self.timer.__exit__(*args)


class track_matching_duration:
    """Context manager to track matching processing duration."""

    def __init__(self, strategy: str):
        self.strategy = strategy
        self.timer: Any = None

    def __enter__(self) -> "track_matching_duration":
        self.timer = matching_processing_duration_seconds.labels(
            matcher_strategy=self.strategy
        ).time()
        self.timer.__enter__()
        return self

    def __exit__(self, *args: Any) -> None:
        if self.timer:
            self.timer.__exit__(*args)


# ============================================================================
# Auto-start metrics server on import (if enabled)
# ============================================================================

if __name__ != "__main__":
    # Auto-start metrics server when module is imported (if enabled)
    metrics_port = int(os.getenv("METRICS_PORT", "8000"))
    if os.getenv("PROMETHEUS_ENABLED", "false").lower() == "true":
        start_metrics_server(metrics_port)
