"""Course line helper: a formatted description on a single invoice line."""

from typing import Any

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType, ToolRisk
from openfatture.billing.application.line_commands import create_riga


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
    aliquota_iva: float | None = None,
    natura: str | None = None,
) -> dict[str, Any]:
    """Add a course or training line: one service at ``imponibile``.

    Rate and natura default like :func:`create_riga` (0% N2.2 in the
    forfettario regime).
    """
    return create_riga(
        fattura_id=fattura_id,
        descrizione=format_course_description(
            course_title=course_title,
            start_date=start_date,
            end_date=end_date,
            location=location,
            additional_notes=additional_notes,
        ),
        quantita=1.0,
        prezzo_unitario=imponibile,
        aliquota_iva=aliquota_iva,
        unita_misura="servizio",
        natura=natura,
    )


__all__ = ["create_course_line", "format_course_description"]


def tools() -> list[Tool]:
    """Assistant tool definitions for the line helpers."""
    return [
        Tool(
            name="create_course_line",
            risk=ToolRisk.MUTATE,
            description="Create a lump-sum line for a course with formatted FT-style description (title, dates, location).",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID",
                    required=True,
                ),
                ToolParameter(
                    name="course_title",
                    type=ToolParameterType.STRING,
                    description="Course title",
                    required=True,
                ),
                ToolParameter(
                    name="imponibile",
                    type=ToolParameterType.NUMBER,
                    description="Total course fee in euros",
                    required=True,
                ),
                ToolParameter(
                    name="start_date",
                    type=ToolParameterType.STRING,
                    description="Course start date (DD.MM.YYYY)",
                    required=True,
                ),
                ToolParameter(
                    name="end_date",
                    type=ToolParameterType.STRING,
                    description="Course end date (DD.MM.YYYY, optional)",
                    required=False,
                ),
                ToolParameter(
                    name="location",
                    type=ToolParameterType.STRING,
                    description="Course location (optional)",
                    required=False,
                ),
                ToolParameter(
                    name="additional_notes",
                    type=ToolParameterType.STRING,
                    description="Additional notes (optional)",
                    required=False,
                ),
                ToolParameter(
                    name="aliquota_iva",
                    type=ToolParameterType.NUMBER,
                    description="VAT rate percentage; omit for the cedente default",
                    required=False,
                ),
                ToolParameter(
                    name="natura",
                    type=ToolParameterType.STRING,
                    description="VAT natura, only with a 0% rate (default N2.2 for forfettario)",
                    required=False,
                ),
            ],
            func=create_course_line,
            requires_confirmation=True,
            examples=[
                "create_course_line(fattura_id=123, course_title='Corso RES', imponibile=960.00, start_date='09.09.2026', end_date='10.09.2026', location='Limolane 12/Roma')",
                "create_course_line(fattura_id=456, course_title='Training session', imponibile=500.00, start_date='15.01.2026')",
            ],
            tags=["write", "create", "line", "course"],
        ),
    ]
