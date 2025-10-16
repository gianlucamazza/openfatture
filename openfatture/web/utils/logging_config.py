"""Structured logging configuration for Streamlit web app - Best Practices 2025.

Provides structured logging with:
- Request tracking
- Performance metrics
- Error context
- User actions
"""

import logging
import time
from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from typing import Any

import streamlit as st

# Configure module logger
logger = logging.getLogger("openfatture.web")


class WebLogger:
    """Structured logger for web application events."""

    def __init__(self):
        """Initialize web logger."""
        self.logger = logger

    def log_page_view(self, page_name: str, user_id: str | None = None) -> None:
        """
        Log page view event.

        Args:
            page_name: Name of the page being viewed
            user_id: Optional user identifier
        """
        self.logger.info(
            "page_view",
            extra={
                "event_type": "page_view",
                "page": page_name,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def log_user_action(
        self, action: str, details: dict[str, Any] | None = None, user_id: str | None = None
    ) -> None:
        """
        Log user action event.

        Args:
            action: Action identifier (e.g., "create_invoice", "upload_file")
            details: Additional action details
            user_id: Optional user identifier
        """
        self.logger.info(
            f"user_action: {action}",
            extra={
                "event_type": "user_action",
                "action": action,
                "details": details or {},
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def log_error(
        self,
        error: Exception,
        context: str,
        details: dict[str, Any] | None = None,
        user_id: str | None = None,
    ) -> None:
        """
        Log error with context.

        Args:
            error: Exception that occurred
            context: Context where error occurred (e.g., "invoice_creation")
            details: Additional error details
            user_id: Optional user identifier
        """
        self.logger.error(
            f"error in {context}: {str(error)}",
            extra={
                "event_type": "error",
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context,
                "details": details or {},
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
            },
            exc_info=True,
        )

    def log_performance(
        self, operation: str, duration_ms: float, details: dict[str, Any] | None = None
    ) -> None:
        """
        Log performance metric.

        Args:
            operation: Operation identifier
            duration_ms: Duration in milliseconds
            details: Additional performance details
        """
        self.logger.info(
            f"performance: {operation} took {duration_ms:.2f}ms",
            extra={
                "event_type": "performance",
                "operation": operation,
                "duration_ms": duration_ms,
                "details": details or {},
                "timestamp": datetime.now().isoformat(),
            },
        )

    def log_ai_request(
        self,
        provider: str,
        model: str,
        tokens: int | None = None,
        cost_usd: float | None = None,
        latency_ms: float | None = None,
    ) -> None:
        """
        Log AI API request metrics.

        Args:
            provider: AI provider name
            model: Model identifier
            tokens: Total tokens used
            cost_usd: Estimated cost in USD
            latency_ms: Request latency in milliseconds
        """
        self.logger.info(
            f"ai_request: {provider}/{model}",
            extra={
                "event_type": "ai_request",
                "provider": provider,
                "model": model,
                "tokens": tokens,
                "cost_usd": cost_usd,
                "latency_ms": latency_ms,
                "timestamp": datetime.now().isoformat(),
            },
        )


# Global logger instance
web_logger = WebLogger()


@contextmanager
def log_operation(operation: str, details: dict[str, Any] | None = None):
    """
    Context manager for logging operations with timing.

    Args:
        operation: Operation identifier
        details: Additional operation details

    Usage:
        >>> with log_operation("create_invoice", {"client_id": 123}):
        ...     create_invoice(...)
    """
    start_time = time.time()

    try:
        yield
        duration_ms = (time.time() - start_time) * 1000
        web_logger.log_performance(operation, duration_ms, details)

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        web_logger.log_error(e, operation, details)
        raise


def log_function_call(func: Callable) -> Callable:
    """
    Decorator to log function calls with timing.

    Args:
        func: Function to decorate

    Returns:
        Wrapped function with logging

    Usage:
        >>> @log_function_call
        ... def expensive_operation():
        ...     # ... operation logic
        ...     pass
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        func_name = f"{func.__module__}.{func.__name__}"

        try:
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000

            web_logger.log_performance(
                operation=func_name,
                duration_ms=duration_ms,
                details={"args_count": len(args), "kwargs_count": len(kwargs)},
            )

            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            web_logger.log_error(
                e,
                func_name,
                {"args_count": len(args), "kwargs_count": len(kwargs), "duration_ms": duration_ms},
            )
            raise

    return wrapper


def track_page_visit(page_name: str) -> None:
    """
    Track page visit in session state and log.

    Args:
        page_name: Name of the page

    Usage:
        >>> # At top of each page
        >>> track_page_visit("invoices")
    """
    # Initialize visit tracking if not exists
    if "page_visits" not in st.session_state:
        st.session_state.page_visits = {}

    # Increment visit count
    current_count = st.session_state.page_visits.get(page_name, 0)
    st.session_state.page_visits[page_name] = current_count + 1

    # Log the visit
    web_logger.log_page_view(page_name)


def get_usage_metrics() -> dict[str, Any]:
    """
    Get usage metrics from session state.

    Returns:
        Dictionary with usage metrics

    Usage:
        >>> metrics = get_usage_metrics()
        >>> st.metric("Page Visits", metrics["total_page_visits"])
    """
    page_visits = st.session_state.get("page_visits", {})

    return {
        "total_page_visits": sum(page_visits.values()),
        "unique_pages_visited": len(page_visits),
        "page_visits": page_visits,
        "session_start": st.session_state.get("session_start", datetime.now()).isoformat(),
    }


# Export convenience functions
log_page_view = web_logger.log_page_view
log_user_action = web_logger.log_user_action
log_error = web_logger.log_error
log_performance = web_logger.log_performance
log_ai_request = web_logger.log_ai_request
