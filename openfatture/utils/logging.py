"""
Structured logging configuration using structlog.

Best practices 2025:
- JSON logging for production
- Correlation IDs for request tracking
- Sensitive data filtering
- Performance metrics
"""

import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any

import structlog
from structlog.types import EventDict, Processor

# Context variable for tracking correlation IDs across async boundaries
_correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def set_correlation_id(correlation_id: str | None = None) -> str:
    """
    Set correlation ID for the current context.

    Args:
        correlation_id: Custom correlation ID. If None, generates a new UUID.

    Returns:
        The correlation ID that was set.
    """
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    _correlation_id_var.set(correlation_id)
    return correlation_id


def get_correlation_id() -> str | None:
    """Get the current correlation ID from context."""
    return _correlation_id_var.get()


def clear_correlation_id() -> None:
    """Clear the correlation ID from context."""
    _correlation_id_var.set(None)


def add_correlation_id(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Add correlation ID to all log entries.

    This allows tracking a single request/invoice through the entire system.
    Uses contextvars for proper async-safe correlation ID tracking.
    """
    correlation_id = get_correlation_id()
    if "correlation_id" not in event_dict:
        event_dict["correlation_id"] = correlation_id
    return event_dict


def filter_sensitive_data(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Filter sensitive data from logs (passwords, API keys, etc.).

    Critical for GDPR compliance and security.
    """
    sensitive_keys = {
        "password",
        "api_key",
        "secret",
        "token",
        "pec_password",
        "ai_api_key",
        "certificate_password",
    }

    for key in sensitive_keys:
        if key in event_dict:
            event_dict[key] = "***REDACTED***"

    # Also check nested event dict
    if "event" in event_dict and isinstance(event_dict["event"], dict):
        for key in sensitive_keys:
            if key in event_dict["event"]:
                event_dict["event"][key] = "***REDACTED***"

    return event_dict


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add application context to every log entry."""
    from openfatture import __version__

    event_dict["app"] = "openfatture"
    event_dict["version"] = __version__
    return event_dict


def configure_logging(
    log_level: str = "INFO",
    json_logs: bool = False,
    dev_mode: bool = True,
) -> None:
    """
    Configure structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        json_logs: Whether to output JSON logs (recommended for production)
        dev_mode: Whether to use development-friendly output
    """
    # Shared processors for all configurations
    shared_processors: list[Processor] = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        add_correlation_id,
        add_app_context,
        filter_sensitive_data,
    ]

    if dev_mode:
        # Development: colorful console output
        processors = shared_processors + [structlog.dev.ConsoleRenderer(colors=True)]
    elif json_logs:
        # Production: JSON output for log aggregation (ELK, Loki, etc.)
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Simple production: key-value pairs
        processors = shared_processors + [
            structlog.processors.KeyValueRenderer(key_order=["timestamp", "level", "event"]),
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Usage:
        logger = get_logger(__name__)
        logger.info("invoice_created", invoice_id=123, amount=1000.00)
    """
    return structlog.get_logger(name)


# Performance logging helpers
class LogPerformance:
    """
    Context manager for logging performance metrics.

    Usage:
        with LogPerformance("xml_generation", logger):
            # ... expensive operation
            pass
    """

    def __init__(self, operation: str, logger: structlog.stdlib.BoundLogger):
        self.operation = operation
        self.logger = logger
        self.start_time: float = 0

    def __enter__(self) -> "LogPerformance":
        import time

        self.start_time = time.perf_counter()
        self.logger.debug(f"{self.operation}_started")
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        import time

        duration = time.perf_counter() - self.start_time

        if exc_type is None:
            self.logger.info(
                f"{self.operation}_completed",
                duration_ms=round(duration * 1000, 2),
                operation=self.operation,
            )
        else:
            self.logger.error(
                f"{self.operation}_failed",
                duration_ms=round(duration * 1000, 2),
                operation=self.operation,
                error=str(exc_val),
                error_type=exc_type.__name__ if exc_type else None,
            )


# Audit logging helpers
def log_invoice_created(
    logger: structlog.stdlib.BoundLogger,
    invoice_id: int,
    invoice_number: str,
    client_name: str,
    amount: float,
) -> None:
    """Log invoice creation for audit trail."""
    logger.info(
        "invoice_created",
        action="create",
        resource="invoice",
        invoice_id=invoice_id,
        invoice_number=invoice_number,
        client_name=client_name,
        amount=amount,
    )


def log_invoice_sent(
    logger: structlog.stdlib.BoundLogger,
    invoice_id: int,
    invoice_number: str,
    recipient: str,
) -> None:
    """Log invoice sending for audit trail."""
    logger.info(
        "invoice_sent",
        action="send",
        resource="invoice",
        invoice_id=invoice_id,
        invoice_number=invoice_number,
        recipient=recipient,
    )


def log_sdi_notification(
    logger: structlog.stdlib.BoundLogger,
    invoice_id: int,
    notification_type: str,
    status: str,
) -> None:
    """Log SDI notification for audit trail."""
    logger.info(
        "sdi_notification_received",
        action="notification",
        resource="sdi",
        invoice_id=invoice_id,
        notification_type=notification_type,
        status=status,
    )


# Initialize logging on module import
configure_logging()
