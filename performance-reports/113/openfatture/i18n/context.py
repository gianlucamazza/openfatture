"""Translation context management for complex scenarios.

This module provides context managers and utilities for handling
translation contexts in multi-threaded or async scenarios.
"""

import contextvars
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import structlog

from openfatture.i18n.loader import get_locale, set_locale

logger = structlog.get_logger(__name__)

# Context variable for async-safe locale storage
_locale_context: contextvars.ContextVar[str] = contextvars.ContextVar(
    "locale_context", default="it"
)


@contextmanager
def locale_context(locale: str) -> Generator[None, None, None]:
    """Context manager for temporary locale switching.

    Useful for rendering templates or generating reports in a specific
    language without affecting the global locale state.

    Args:
        locale: Temporary locale code

    Yields:
        None

    Example:
        >>> from openfatture.i18n import _, locale_context
        >>> _("common-yes")  # Uses default locale
        "Sì"
        >>> with locale_context("en"):
        ...     _("common-yes")  # Temporarily uses English
        "Yes"
        >>> _("common-yes")  # Back to default locale
        "Sì"
    """
    original_locale = get_locale()

    try:
        set_locale(locale)
        logger.debug(f"Entered locale context: {locale}")
        yield
    finally:
        set_locale(original_locale)
        logger.debug(f"Restored locale context: {original_locale}")


def get_context_locale() -> str:
    """Get locale from context variable (async-safe).

    Returns:
        Current locale from context or default
    """
    try:
        return _locale_context.get()
    except LookupError:
        return get_locale()


def set_context_locale(locale: str) -> None:
    """Set locale in context variable (async-safe).

    Args:
        locale: Language code to set
    """
    _locale_context.set(locale)


class TranslationContext:
    """Translation context for complex scenarios with metadata.

    Useful for AI prompts or email templates that need locale-specific
    business context and variables.
    """

    def __init__(self, locale: str | None = None, **variables: Any):
        """Initialize translation context.

        Args:
            locale: Optional locale override
            **variables: Context variables for message interpolation
        """
        self.locale = locale or get_locale()
        self.variables = variables

    def translate(self, message_id: str, **extra_vars: Any) -> str:
        """Translate message with context variables.

        Args:
            message_id: Fluent message ID
            **extra_vars: Additional variables (merged with context variables)

        Returns:
            Translated message
        """
        from openfatture.i18n import _

        # Merge context variables with extra variables
        all_vars = {**self.variables, **extra_vars}

        return _(message_id, locale=self.locale, **all_vars)

    def __enter__(self) -> "TranslationContext":
        """Enter context manager."""
        set_locale(self.locale)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager."""
        # Restore to default locale (handled by loader's thread-local)
        pass
