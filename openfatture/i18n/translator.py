"""Core translation function and utilities.

This module provides the main translation function _() that handles
message lookup, variable interpolation, and fallback logic.
"""

from typing import Any

import structlog

from openfatture.i18n.loader import format_value, get_locale

logger = structlog.get_logger(__name__)


def _(message_id: str, locale: str | None = None, **variables: Any) -> str:
    """Translate a message with optional variable interpolation.

    This is the main translation function used throughout the application.
    It uses Mozilla Fluent for advanced i18n features like pluralization,
    gender variants, and date/number formatting.

    Args:
        message_id: Fluent message ID (e.g., "cli-fattura-create-title")
        locale: Optional locale override (uses current locale if None)
        **variables: Variables for message interpolation

    Returns:
        Translated and formatted message

    Examples:
        >>> _("cli-fattura-create-title")
        "Crea Nuova Fattura" # Italian (default)

        >>> _("cli-fattura-created", numero="001")
        "Fattura 001 creata con successo!"

        >>> _("cli-fattura-create-title", locale="en")
        "Create New Invoice" # English

        >>> _("errors-invoice-not-found", numero="INV-123")
        "Fattura INV-123 non trovata"  # Italian

    Fallback behavior:
        1. Try requested locale
        2. Try English (if different from requested)
        3. Try Italian (default)
        4. Return message_id if all fail
    """
    current_locale = locale or get_locale()

    # Year-like variables are identifiers, not quantities: render them verbatim
    # so Fluent's numeric formatter does not insert a thousands separator
    # (e.g. a year 2025 must not become "2,025" / "2.025"). Quantity variables
    # such as `count`/`months` stay numeric so plural selectors keep working.
    for year_var in ("anno", "year", "tax_year"):
        if isinstance(variables.get(year_var), int):
            variables[year_var] = str(variables[year_var])

    # Try to get formatted message
    result = format_value(current_locale, message_id, variables)

    if result is not None:
        return result

    # Fallback: return message_id with warning
    logger.warning(
        f"Translation not found: {message_id} (locale: {current_locale})",
        extra={"message_id": message_id, "locale": current_locale, "variables": variables},
    )

    # Return message_id as fallback (better than empty string for debugging)
    if variables:
        # Try basic string formatting if variables provided
        try:
            return f"{message_id} ({', '.join(f'{k}={v}' for k, v in variables.items())})"
        except Exception:
            pass

    return message_id
