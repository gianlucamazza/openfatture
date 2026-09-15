"""Helper tools for creating invoice lines in different styles.

Provides convenience functions for creating lines in:
- "lump" style: 1 × imponibile (single item at total price)
- "rate" style: qty × unit_price (multiple items at unit price)
- "course" style: formatted descriptions for training courses/events
"""

from typing import Any

from openfatture.billing.application.invoice_commands import create_riga


def create_lump_line(
    fattura_id: int,
    descrizione: str,
    imponibile: float,
    aliquota_iva: float = 22.0,
    unita_misura: str = "servizio",
) -> dict[str, Any]:
    """
    Create a "lump" style line: 1 × imponibile.

    This style is common for:
    - Professional services billed as a whole (e.g., "Consulting project")
    - Fixed-price deliverables
    - Training courses (one course, one price)

    Args:
        fattura_id: Invoice ID
        descrizione: Item description
        imponibile: Total taxable amount (€)
        aliquota_iva: VAT rate (%) - default 22%
        unita_misura: Unit of measure - default "servizio"

    Returns:
        Dictionary with result or error

    Example:
        create_lump_line(
            fattura_id=123,
            descrizione="Corso di formazione Python",
            imponibile=960.00,
            aliquota_iva=0.0  # Forfettario N2.2
        )
        Result: "1 servizio × €960.00 = €960.00"
    """
    return create_riga(
        fattura_id=fattura_id,
        descrizione=descrizione,
        quantita=1.0,
        prezzo_unitario=imponibile,
        aliquota_iva=aliquota_iva,
        unita_misura=unita_misura,
    )


def create_rate_line(
    fattura_id: int,
    descrizione: str,
    quantita: float,
    prezzo_unitario: float,
    aliquota_iva: float = 22.0,
    unita_misura: str = "ore",
) -> dict[str, Any]:
    """
    Create a "rate" style line: qty × unit_price.

    This style is common for:
    - Hourly work (e.g., "10 hours × €80/hr")
    - Per-unit goods (e.g., "5 items × €20 each")
    - Time-based billing

    Args:
        fattura_id: Invoice ID
        descrizione: Item description
        quantita: Quantity
        prezzo_unitario: Unit price (€)
        aliquota_iva: VAT rate (%) - default 22%
        unita_misura: Unit of measure - default "ore"

    Returns:
        Dictionary with result or error

    Example:
        create_rate_line(
            fattura_id=123,
            descrizione="Consulenza tecnica",
            quantita=12,
            prezzo_unitario=80.00,
            aliquota_iva=22.0
        )
        Result: "12 ore × €80.00 = €960.00"
    """
    return create_riga(
        fattura_id=fattura_id,
        descrizione=descrizione,
        quantita=quantita,
        prezzo_unitario=prezzo_unitario,
        aliquota_iva=aliquota_iva,
        unita_misura=unita_misura,
    )


def format_course_description(
    course_title: str,
    start_date: str,
    end_date: str | None = None,
    location: str | None = None,
    additional_notes: str | None = None,
) -> str:
    """
    Format a professional description for training courses/events.

    Creates a structured description in FatturaPA style:
    "Corso di formazione: \"<title>\" eseguito dal <start> al <end> presso <location>"

    Args:
        course_title: Course or event title
        start_date: Start date (format: DD.MM.YYYY or YYYY-MM-DD)
        end_date: End date (optional, defaults to same as start_date)
        location: Location/venue (optional)
        additional_notes: Additional details (optional)

    Returns:
        Formatted description string

    Examples:
        format_course_description(
            course_title="Python avanzato per data science",
            start_date="14.09.2026",
            end_date="14.09.2026",
            location="Sede del cliente, Milano"
        )
        Result: 'Corso di formazione: "Python avanzato per data science" eseguito dal 14.09.2026 al 14.09.2026 presso Sede del cliente, Milano'

        format_course_description(
            course_title="Workshop Django",
            start_date="2026-09-14",
            location="Online"
        )
        Result: 'Corso di formazione: "Workshop Django" eseguito il 2026-09-14 presso Online'
    """
    # Ensure end_date defaults to start_date for single-day events
    if end_date is None:
        end_date = start_date

    parts = [f'Corso di formazione: "{course_title}"']

    # Date range
    if start_date == end_date:
        parts.append(f"eseguito il {start_date}")
    else:
        parts.append(f"eseguito dal {start_date} al {end_date}")

    # Location
    if location:
        parts.append(f"presso {location}")

    # Build main description
    description = " ".join(parts)

    # Add additional notes if provided
    if additional_notes:
        description += f"\n\n{additional_notes}"

    return description


def create_course_line(
    fattura_id: int,
    course_title: str,
    imponibile: float,
    start_date: str,
    end_date: str | None = None,
    location: str | None = None,
    additional_notes: str | None = None,
    aliquota_iva: float = 0.0,
) -> dict[str, Any]:
    """
    Create a course/training line with professional formatting.

    Combines format_course_description + create_lump_line for convenience.

    Args:
        fattura_id: Invoice ID
        course_title: Course or event title
        imponibile: Total course fee (€)
        start_date: Start date (format: DD.MM.YYYY or YYYY-MM-DD)
        end_date: End date (optional, defaults to same as start_date)
        location: Location/venue (optional)
        additional_notes: Additional details (optional)
        aliquota_iva: VAT rate (%) - default 0% for forfettario

    Returns:
        Dictionary with result or error

    Example:
        create_course_line(
            fattura_id=123,
            course_title="Python avanzato per data science",
            imponibile=960.00,
            start_date="14.09.2026",
            end_date="14.09.2026",
            location="Sede del cliente, Milano",
            aliquota_iva=0.0
        )
    """
    descrizione = format_course_description(
        course_title=course_title,
        start_date=start_date,
        end_date=end_date,
        location=location,
        additional_notes=additional_notes,
    )

    return create_lump_line(
        fattura_id=fattura_id,
        descrizione=descrizione,
        imponibile=imponibile,
        aliquota_iva=aliquota_iva,
        unita_misura="servizio",
    )


__all__ = [
    "create_lump_line",
    "create_rate_line",
    "format_course_description",
    "create_course_line",
]
