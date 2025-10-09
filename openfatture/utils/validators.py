"""Validation utilities for Italian fiscal data."""

import re


def validate_partita_iva(partita_iva: str) -> bool:
    """
    Validate Italian VAT number (Partita IVA).

    Args:
        partita_iva: VAT number to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not partita_iva or len(partita_iva) != 11:
        return False

    if not partita_iva.isdigit():
        return False

    # Check digit algorithm
    s = 0
    for i in range(10):
        n = int(partita_iva[i])
        if i % 2 == 0:
            s += n
        else:
            s += (n * 2) % 10 + (n * 2) // 10

    check_digit = (10 - s % 10) % 10
    return check_digit == int(partita_iva[10])


def validate_codice_fiscale(codice_fiscale: str) -> bool:
    """
    Validate Italian tax code (Codice Fiscale).

    Args:
        codice_fiscale: Tax code to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not codice_fiscale or len(codice_fiscale) != 16:
        return False

    pattern = r"^[A-Z]{6}[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{3}[A-Z]$"
    return bool(re.match(pattern, codice_fiscale.upper()))


def validate_codice_destinatario(codice: str) -> bool:
    """
    Validate SDI recipient code.

    Args:
        codice: Recipient code (7 alphanumeric characters or '0000000' for PEC)

    Returns:
        bool: True if valid, False otherwise
    """
    if not codice or len(codice) != 7:
        return False

    return codice.isalnum()


def validate_pec_email(email: str) -> bool:
    """
    Basic PEC email validation.

    Args:
        email: Email address to validate

    Returns:
        bool: True if valid email format, False otherwise
    """
    if not email:
        return False

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def format_importo(importo: float, decimals: int = 2) -> str:
    """
    Format amount for FatturaPA (with proper decimal places).

    Args:
        importo: Amount to format
        decimals: Number of decimal places (default: 2)

    Returns:
        str: Formatted amount
    """
    return f"{importo:.{decimals}f}"
