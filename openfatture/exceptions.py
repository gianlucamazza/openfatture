"""OpenFatture exception types.

Application services report expected failures as ``{"error": ...}`` results;
exceptions are reserved for conditions callers must handle explicitly, such as
FatturaPA XML that fails schema validation.
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


class IntegrationError(OpenFattureError):
    """Base class for external service integration errors."""


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
