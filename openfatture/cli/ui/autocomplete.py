"""Autocomplete helper functions for common Italian inputs."""

import questionary
from questionary import ValidationError, Validator

from openfatture.cli.ui.autocomplete_data import (
    CAP_COMUNI,
    DESCRIZIONI_SERVIZI,
    MODALITA_PAGAMENTO,
    NATURE_IVA,
    PROVINCE_ITALIANE,
    REGIMI_FISCALI,
    UNITA_MISURA,
)
from openfatture.cli.ui.styles import openfatture_style


# Validators
class ProvinciaValidator(Validator):
    """Validate Italian province codes."""

    def validate(self, document):
        if document.text and document.text.upper() not in PROVINCE_ITALIANE:
            raise ValidationError(
                message="Provincia non valida (es: RM, MI, NA)",
                cursor_position=len(document.text),
            )


class CAPValidator(Validator):
    """Validate Italian postal codes."""

    def validate(self, document):
        if document.text and (len(document.text) != 5 or not document.text.isdigit()):
            raise ValidationError(
                message="CAP deve essere di 5 cifre",
                cursor_position=len(document.text),
            )


# Autocomplete functions


def autocomplete_provincia(
    message: str = "Provincia (2 lettere):",
    default: str = "",
) -> str:
    """
    Autocomplete for Italian provinces.

    Args:
        message: Prompt message
        default: Default value

    Returns:
        Province code (e.g., "RM", "MI")
    """
    result = questionary.autocomplete(
        message,
        choices=PROVINCE_ITALIANE,
        default=default,
        style=openfatture_style,
        validate=ProvinciaValidator,
    ).ask()

    return result.upper() if result else ""


def autocomplete_cap(
    message: str = "CAP (5 cifre):",
    default: str = "",
    comune: str | None = None,
) -> str:
    """
    Autocomplete for Italian postal codes.

    Args:
        message: Prompt message
        default: Default value
        comune: If provided, suggests CAPs for that city

    Returns:
        CAP string (5 digits)
    """
    # If we have the city, suggest specific CAPs
    suggestions = CAP_COMUNI.get(comune, []) if comune else []

    result = questionary.autocomplete(
        message,
        choices=suggestions if suggestions else [],
        default=default,
        style=openfatture_style,
        validate=CAPValidator,
    ).ask()

    return result if result else ""


def autocomplete_regime_fiscale(
    message: str = "Regime fiscale:",
    default: str = "RF19",
) -> str:
    """
    Autocomplete for tax regimes.

    Args:
        message: Prompt message
        default: Default regime code

    Returns:
        Regime code (e.g., "RF19")
    """
    # Create choices with descriptions
    choices = [f"{code} - {desc}" for code, desc in REGIMI_FISCALI]

    result = questionary.autocomplete(
        message,
        choices=choices,
        default=f"{default} - {dict(REGIMI_FISCALI).get(default, '')}",
        style=openfatture_style,
    ).ask()

    # Extract just the code
    if result:
        return result.split(" - ")[0]
    return default


def autocomplete_natura_iva(
    message: str = "Natura IVA (per operazioni esenti):",
    default: str = "",
) -> str:
    """
    Autocomplete for VAT nature codes.

    Args:
        message: Prompt message
        default: Default nature code

    Returns:
        Nature code (e.g., "N1", "N3.1")
    """
    choices = [f"{code} - {desc}" for code, desc in NATURE_IVA]

    result = questionary.autocomplete(
        message,
        choices=choices,
        default=default,
        style=openfatture_style,
    ).ask()

    # Extract just the code
    if result:
        return result.split(" - ")[0]
    return ""


def autocomplete_descrizione_servizio(
    message: str = "Descrizione servizio:",
    default: str = "",
) -> str:
    """
    Autocomplete for common service descriptions.

    Args:
        message: Prompt message
        default: Default description

    Returns:
        Service description
    """
    return questionary.autocomplete(
        message,
        choices=DESCRIZIONI_SERVIZI,
        default=default,
        style=openfatture_style,
    ).ask()


def autocomplete_unita_misura(
    message: str = "Unit of measure:",
    default: str = "hours",
) -> str:
    """
    Autocomplete for units of measure.

    Args:
        message: Prompt message
        default: Default unit

    Returns:
        Unit (e.g., "ore", "pezzi")
    """
    return questionary.autocomplete(
        message,
        choices=UNITA_MISURA,
        default=default,
        style=openfatture_style,
    ).ask()


def autocomplete_modalita_pagamento(
    message: str = "Payment method:",
    default: str = "Bank transfer",
) -> str:
    """
    Autocomplete for payment methods.

    Args:
        message: Prompt message
        default: Default payment method

    Returns:
        Payment method
    """
    return questionary.autocomplete(
        message,
        choices=MODALITA_PAGAMENTO,
        default=default,
        style=openfatture_style,
    ).ask()
