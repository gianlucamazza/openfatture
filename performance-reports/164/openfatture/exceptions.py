"""Standardized exception hierarchy for OpenFatture.

This module provides a comprehensive, type-safe exception hierarchy following
modern Python best practices (2025). All exceptions include rich context for
debugging and structured logging.

Usage:
    from openfatture.exceptions import ValidationError, DatabaseError

    try:
        validate_invoice(data)
    except ValidationError as e:
        logger.error("validation_failed", error=str(e), context=e.context)
"""

from __future__ import annotations

from typing import Any


class OpenFattureError(Exception):
    """Base exception for all OpenFatture errors.

    All custom exceptions should inherit from this class to enable
    centralized error handling and logging.

    Attributes:
        message: Human-readable error message
        context: Additional context for debugging (dict)
        original_error: Original exception if wrapped
    """

    def __init__(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ) -> None:
        """Initialize exception with rich context.

        Args:
            message: Human-readable error description
            context: Additional structured data for debugging
            original_error: Original exception if this wraps another error
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.original_error = original_error

    def __str__(self) -> str:
        """Format exception with context for logging."""
        base = self.message
        if self.context:
            ctx_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            base = f"{base} ({ctx_str})"
        if self.original_error:
            base = f"{base} [caused by: {type(self.original_error).__name__}]"
        return base

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"{self.__class__.__name__}(message={self.message!r}, context={self.context!r})"


# =============================================================================
# Validation & Input Errors
# =============================================================================


class ValidationError(OpenFattureError):
    """Raised when input validation fails.

    Used for invalid user input, malformed data, or constraint violations.
    """

    def __init__(
        self,
        message: str,
        *,
        field: str | None = None,
        value: Any = None,
        constraint: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Error description
            field: Name of the invalid field
            value: The invalid value (will be sanitized in logs)
            constraint: Validation constraint that was violated
            **kwargs: Additional context
        """
        context = kwargs.get("context", {})
        if field:
            context["field"] = field
        if value is not None:
            context["value"] = str(value)[:100]  # Truncate for safety
        if constraint:
            context["constraint"] = constraint
        kwargs["context"] = context
        super().__init__(message, **kwargs)


class ConfigurationError(OpenFattureError):
    """Raised when application configuration is invalid or missing.

    Used for missing environment variables, invalid settings, or
    configuration file errors.
    """

    def __init__(
        self,
        message: str,
        *,
        setting: str | None = None,
        expected: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize configuration error.

        Args:
            message: Error description
            setting: Name of the problematic setting
            expected: Expected value or type
            **kwargs: Additional context
        """
        context = kwargs.get("context", {})
        if setting:
            context["setting"] = setting
        if expected:
            context["expected"] = expected
        kwargs["context"] = context
        super().__init__(message, **kwargs)


# =============================================================================
# Database & Persistence Errors
# =============================================================================


class DatabaseError(OpenFattureError):
    """Base class for database-related errors."""


class RecordNotFoundError(DatabaseError):
    """Raised when a database record is not found.

    Args:
        entity_type: Type of entity (e.g., "Fattura", "Cliente")
        entity_id: ID of the missing entity
    """

    def __init__(
        self,
        message: str,
        *,
        entity_type: str | None = None,
        entity_id: int | str | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.get("context", {})
        if entity_type:
            context["entity_type"] = entity_type
        if entity_id:
            context["entity_id"] = str(entity_id)
        kwargs["context"] = context
        super().__init__(message, **kwargs)


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""


class DatabaseIntegrityError(DatabaseError):
    """Raised when database integrity constraints are violated."""


# =============================================================================
# Business Logic Errors
# =============================================================================


class BusinessLogicError(OpenFattureError):
    """Base class for business rule violations."""


class InvoiceStateError(BusinessLogicError):
    """Raised when invoice operation violates state machine rules.

    Example: Trying to edit an invoice that's already been sent to SDI.
    """

    def __init__(
        self,
        message: str,
        *,
        invoice_id: str | None = None,
        current_state: str | None = None,
        attempted_action: str | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.get("context", {})
        if invoice_id:
            context["invoice_id"] = invoice_id
        if current_state:
            context["current_state"] = current_state
        if attempted_action:
            context["attempted_action"] = attempted_action
        kwargs["context"] = context
        super().__init__(message, **kwargs)


class PaymentError(BusinessLogicError):
    """Raised when payment operations fail."""


class TaxCalculationError(BusinessLogicError):
    """Raised when tax/VAT calculation fails."""


# =============================================================================
# External Integration Errors
# =============================================================================


class IntegrationError(OpenFattureError):
    """Base class for external service integration errors."""


class SDIError(IntegrationError):
    """Raised when SDI (Sistema di Interscambio) integration fails.

    Used for PEC sending, XML validation, notification processing.
    """

    def __init__(
        self,
        message: str,
        *,
        error_code: str | None = None,
        sdi_message: str | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.get("context", {})
        if error_code:
            context["error_code"] = error_code
        if sdi_message:
            context["sdi_message"] = sdi_message
        kwargs["context"] = context
        super().__init__(message, **kwargs)


class PECError(IntegrationError):
    """Raised when PEC email operations fail."""


class XMLValidationError(IntegrationError):
    """Raised when FatturaPA XML validation fails."""

    def __init__(
        self,
        message: str,
        *,
        xml_path: str | None = None,
        validation_errors: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.get("context", {})
        if xml_path:
            context["xml_path"] = xml_path
        if validation_errors:
            context["validation_error_count"] = len(validation_errors)
            context["first_error"] = validation_errors[0] if validation_errors else None
        kwargs["context"] = context
        super().__init__(message, **kwargs)


class PaymentGatewayError(IntegrationError):
    """Raised when payment gateway integration fails."""


class BankImportError(IntegrationError):
    """Raised when bank statement import fails."""

    def __init__(
        self,
        message: str,
        *,
        file_format: str | None = None,
        line_number: int | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.get("context", {})
        if file_format:
            context["file_format"] = file_format
        if line_number:
            context["line_number"] = line_number
        kwargs["context"] = context
        super().__init__(message, **kwargs)


# =============================================================================
# AI & ML Errors (reuse existing hierarchy from ai.providers.base)
# =============================================================================


class AIError(OpenFattureError):
    """Base class for AI/ML related errors."""


class AIProviderError(AIError):
    """Raised when AI provider (OpenAI, Anthropic, Ollama) fails."""

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        model: str | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.get("context", {})
        if provider:
            context["provider"] = provider
        if model:
            context["model"] = model
        kwargs["context"] = context
        super().__init__(message, **kwargs)


class AIProviderAuthError(AIProviderError):
    """Raised when AI provider authentication fails."""


class AIProviderRateLimitError(AIProviderError):
    """Raised when AI provider rate limit is exceeded."""


class AIProviderTimeoutError(AIProviderError):
    """Raised when AI provider request times out."""


# =============================================================================
# File & Storage Errors
# =============================================================================


class FileOperationError(OpenFattureError):
    """Base class for file operation errors."""


class FileNotFoundError(FileOperationError):
    """Raised when a required file is not found."""


class FilePermissionError(FileOperationError):
    """Raised when file permissions are insufficient."""


class FileFormatError(FileOperationError):
    """Raised when file format is invalid or unsupported."""


# =============================================================================
# Automation & Hooks Errors
# =============================================================================


class HookExecutionError(OpenFattureError):
    """Raised when custom hook execution fails.

    Used for user-defined automation scripts/hooks.
    """

    def __init__(
        self,
        message: str,
        *,
        hook_name: str | None = None,
        exit_code: int | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.get("context", {})
        if hook_name:
            context["hook_name"] = hook_name
        if exit_code is not None:
            context["exit_code"] = exit_code
        kwargs["context"] = context
        super().__init__(message, **kwargs)


# =============================================================================
# HTTP & Network Errors
# =============================================================================


class NetworkError(OpenFattureError):
    """Base class for network-related errors."""


class HTTPError(NetworkError):
    """Raised when HTTP request fails."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        url: str | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.get("context", {})
        if status_code:
            context["status_code"] = status_code
        if url:
            context["url"] = url[:100]  # Truncate long URLs
        kwargs["context"] = context
        super().__init__(message, **kwargs)


class TimeoutError(NetworkError):
    """Raised when network operation times out."""


# =============================================================================
# Utility Functions
# =============================================================================


def wrap_exception(
    error: Exception,
    message: str,
    *,
    exception_class: type[OpenFattureError] = OpenFattureError,
    **context: Any,
) -> OpenFattureError:
    """Wrap an external exception in OpenFatture exception hierarchy.

    Useful for converting third-party exceptions (SQLAlchemy, requests, etc.)
    into our standardized exceptions while preserving the original error.

    Args:
        error: Original exception to wrap
        message: Human-readable description
        exception_class: Which OpenFatture exception to use
        **context: Additional context to attach

    Returns:
        Wrapped exception with original error preserved

    Example:
        try:
            session.commit()
        except IntegrityError as e:
            raise wrap_exception(
                e,
                "Failed to save invoice due to duplicate number",
                exception_class=DatabaseIntegrityError,
                invoice_number="INV-001"
            )
    """
    return exception_class(
        message,
        context=context,
        original_error=error,
    )


__all__ = [
    # Base
    "OpenFattureError",
    # Validation
    "ValidationError",
    "ConfigurationError",
    # Database
    "DatabaseError",
    "RecordNotFoundError",
    "DatabaseConnectionError",
    "DatabaseIntegrityError",
    # Business Logic
    "BusinessLogicError",
    "InvoiceStateError",
    "PaymentError",
    "TaxCalculationError",
    # Integration
    "IntegrationError",
    "SDIError",
    "PECError",
    "XMLValidationError",
    "PaymentGatewayError",
    "BankImportError",
    # AI
    "AIError",
    "AIProviderError",
    "AIProviderAuthError",
    "AIProviderRateLimitError",
    "AIProviderTimeoutError",
    # Files
    "FileOperationError",
    "FileNotFoundError",
    "FilePermissionError",
    "FileFormatError",
    # Automation
    "HookExecutionError",
    # Network
    "NetworkError",
    "HTTPError",
    "TimeoutError",
    # Utilities
    "wrap_exception",
]
