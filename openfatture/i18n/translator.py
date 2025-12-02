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
        "🧾 Crea Nuova Fattura"  # Italian (default)

        >>> _("cli-fattura-created", numero="001")
        "✅ Fattura 001 creata con successo!"

        >>> _("cli-fattura-create-title", locale="en")
        "🧾 Create New Invoice"  # English

        >>> _("errors-invoice-not-found", numero="INV-123")
        "Fattura INV-123 non trovata"  # Italian

    Fallback behavior:
        1. Try requested locale
        2. Try English (if different from requested)
        3. Try Italian (default)
        4. Return message_id if all fail
    """
    current_locale = locale or get_locale()

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


def translate_dict(data: dict[str, Any], locale: str | None = None) -> dict[str, Any]:
    """Recursively translate all string values in a dictionary.

    Useful for translating configuration dictionaries or API responses.

    Args:
        data: Dictionary with string values as message IDs
        locale: Optional locale override

    Returns:
        Dictionary with translated values

    Example:
        >>> data = {"title": "cli-fattura-create-title", "count": 10}
        >>> translate_dict(data)
        {"title": "🧾 Crea Nuova Fattura", "count": 10}
    """
    result: dict[str, Any] = {}

    for key, value in data.items():
        if isinstance(value, str):
            # Try to translate, keep original if not a message ID
            translated = _(value, locale=locale)
            result[key] = translated if translated != value else value
        elif isinstance(value, dict):
            result[key] = translate_dict(value, locale=locale)
        elif isinstance(value, list):
            result[key] = [
                translate_dict(item, locale=locale) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value

    return result


def translate_list(items: list[str], locale: str | None = None) -> list[str]:
    """Translate a list of message IDs.

    Args:
        items: List of message IDs
        locale: Optional locale override

    Returns:
        List of translated strings

    Example:
        >>> translate_list(["common-yes", "common-no", "common-cancel"])
        ["Sì", "No", "Annulla"]
    """
    return [_(item, locale=locale) for item in items]
