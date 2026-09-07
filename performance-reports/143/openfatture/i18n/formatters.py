"""Custom Fluent formatters for currency, dates, and numbers.

This module provides locale-aware formatting functions that can be used
in Fluent messages for proper internationalization of financial data.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from babel.dates import format_date, format_datetime
from babel.numbers import format_currency, format_decimal, format_percent

from openfatture.i18n.loader import get_locale


def format_euro(amount: Decimal | float | str, locale: str | None = None) -> str:
    """Format amount as EUR currency.

    Args:
        amount: Amount to format
        locale: Optional locale override

    Returns:
        Formatted currency string

    Examples:
        >>> format_euro(Decimal("1234.56"))
        "€ 1.234,56"  # Italian (default)

        >>> format_euro(1234.56, locale="en")
        "€1,234.56"   # English

        >>> format_euro(1234.56, locale="de")
        "1.234,56 €"  # German
    """
    current_locale = locale or get_locale()

    # Convert to Decimal if string
    if isinstance(amount, str):
        amount = Decimal(amount)

    # Map locale codes to Babel locale identifiers
    locale_map = {
        "it": "it_IT",
        "en": "en_US",  # Use US format for numbers (international standard)
        "es": "es_ES",
        "fr": "fr_FR",
        "de": "de_DE",
    }

    babel_locale = locale_map.get(current_locale, "it_IT")

    return format_currency(amount, "EUR", locale=babel_locale)


def format_number(value: Decimal | float | int | str, locale: str | None = None) -> str:
    """Format number with locale-specific separators.

    Args:
        value: Number to format
        locale: Optional locale override

    Returns:
        Formatted number string

    Examples:
        >>> format_number(1234567.89)
        "1.234.567,89"  # Italian

        >>> format_number(1234567.89, locale="en")
        "1,234,567.89"  # English
    """
    current_locale = locale or get_locale()

    if isinstance(value, str):
        value = Decimal(value)

    locale_map = {
        "it": "it_IT",
        "en": "en_US",
        "es": "es_ES",
        "fr": "fr_FR",
        "de": "de_DE",
    }

    babel_locale = locale_map.get(current_locale, "it_IT")

    return format_decimal(value, locale=babel_locale)


def format_percentage(
    value: Decimal | float | str, locale: str | None = None, decimals: int = 2
) -> str:
    """Format value as percentage.

    Args:
        value: Value to format (0.22 = 22%)
        locale: Optional locale override
        decimals: Number of decimal places

    Returns:
        Formatted percentage string

    Examples:
        >>> format_percentage(0.22)
        "22,00%"  # Italian

        >>> format_percentage(0.22, locale="en")
        "22.00%"  # English

        >>> format_percentage(Decimal("0.04"), decimals=0)
        "4%"
    """
    current_locale = locale or get_locale()

    if isinstance(value, str):
        value = Decimal(value)

    locale_map = {
        "it": "it_IT",
        "en": "en_US",
        "es": "es_ES",
        "fr": "fr_FR",
        "de": "de_DE",
    }

    babel_locale = locale_map.get(current_locale, "it_IT")

    return format_percent(value, format=f"#,##0.{'0' * decimals}%", locale=babel_locale)


def format_date_localized(
    dt: date | datetime, format_str: str = "medium", locale: str | None = None
) -> str:
    """Format date with locale-specific formatting.

    Args:
        dt: Date or datetime to format
        format_str: Format type ("short", "medium", "long", "full") or custom pattern
        locale: Optional locale override

    Returns:
        Formatted date string

    Examples:
        >>> format_date_localized(date(2024, 3, 15))
        "15 mar 2024"  # Italian medium

        >>> format_date_localized(date(2024, 3, 15), format_str="long", locale="en")
        "March 15, 2024"  # English long

        >>> format_date_localized(date(2024, 3, 15), format_str="dd/MM/yyyy")
        "15/03/2024"  # Custom pattern
    """
    current_locale = locale or get_locale()

    locale_map = {
        "it": "it_IT",
        "en": "en_US",
        "es": "es_ES",
        "fr": "fr_FR",
        "de": "de_DE",
    }

    babel_locale = locale_map.get(current_locale, "it_IT")

    if isinstance(dt, datetime):
        return format_datetime(dt, format=format_str, locale=babel_locale)
    else:
        return format_date(dt, format=format_str, locale=babel_locale)


def format_invoice_number(numero: str, anno: int | str, locale: str | None = None) -> str:
    """Format invoice number with year.

    Args:
        numero: Invoice number
        anno: Year
        locale: Optional locale override

    Returns:
        Formatted invoice reference

    Examples:
        >>> format_invoice_number("001", 2024)
        "Fattura 001/2024"  # Italian

        >>> format_invoice_number("042", 2024, locale="en")
        "Invoice 042/2024"  # English
    """
    from openfatture.i18n import _

    label = _("common-invoice", locale=locale)
    return f"{label} {numero}/{anno}"


def format_vat_rate(rate: Decimal | float | int, locale: str | None = None) -> str:
    """Format VAT rate.

    Args:
        rate: VAT rate (22 = 22%)
        locale: Optional locale override

    Returns:
        Formatted VAT rate string

    Examples:
        >>> format_vat_rate(22)
        "IVA 22%"  # Italian

        >>> format_vat_rate(22, locale="en")
        "VAT 22%"  # English (but IVA preserved for legal accuracy)
    """
    from openfatture.i18n import _

    # Always use "IVA" for Italian tax law accuracy
    # Even in English, "IVA" is standard for FatturaPA context
    vat_label = "IVA" if locale in (None, "it") else _("common-vat", locale=locale)

    return f"{vat_label} {rate}%"


# Register custom formatters for Fluent (if needed)
CUSTOM_FORMATTERS: dict[str, Any] = {
    "CURRENCY": format_euro,
    "NUMBER": format_number,
    "PERCENTAGE": format_percentage,
    "DATE": format_date_localized,
    "INVOICE_NUMBER": format_invoice_number,
    "VAT_RATE": format_vat_rate,
}
