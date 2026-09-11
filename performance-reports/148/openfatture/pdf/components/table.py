"""Table component for invoice line items."""

from html import escape
from typing import Any

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph, Table, TableStyle


def draw_invoice_table(
    canvas: Canvas,
    y_position: float,
    righe: list[dict[str, Any]],
    primary_color: str = "#2C3E50",
    available_height: float | None = None,
) -> tuple[float, list[Any]]:
    """Draw invoice line items table with proper multi-page splitting.

    Args:
        canvas: ReportLab canvas
        y_position: Starting Y position
        righe: List of invoice lines (dicts with descrizione, quantita, prezzo_unitario, etc.)
        primary_color: Header color (hex)
        available_height: Available height for table (if None, uses remaining page space)

    Returns:
        Tuple of (new Y position, remaining_tables_list)
        - If remaining_tables_list is empty, table fit on current page
        - If remaining_tables_list has items, they need to be drawn on subsequent pages
        Note: remaining tables are Flowable objects (Table instances from split())
    """
    if not righe:
        return y_position, []

    # Calculate available height if not provided
    if available_height is None:
        # Reserve space for bottom margin (2cm) + footer (2cm) + safety margin (1cm)
        available_height = y_position - 5 * cm

    # Table header
    headers = ["#", "Descrizione", "Q.tà", "Unità", "Prezzo €", "IVA %", "Totale €"]

    # Create paragraph style for description column (with text wrapping)
    desc_style = ParagraphStyle(
        "Description",
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        alignment=TA_LEFT,
        leftIndent=0,
        rightIndent=0,
        spaceAfter=0,
        spaceBefore=0,
    )

    # Table data - using list[Any] to accommodate both strings and Paragraph objects
    data: list[list[Any]] = [headers]

    for idx, riga in enumerate(righe, start=1):
        # Use Paragraph for description to enable text wrapping
        # Escape HTML special characters to prevent ReportLab markup injection
        descrizione = str(riga.get("descrizione", ""))
        descrizione_escaped = escape(descrizione, quote=False)
        desc_paragraph = Paragraph(descrizione_escaped, desc_style)

        data.append(
            [
                str(idx),
                desc_paragraph,  # Now wraps instead of truncating
                f"{riga.get('quantita', 0):.2f}",
                riga.get("unita_misura", "ore"),
                f"{riga.get('prezzo_unitario', 0):.2f}",
                f"{riga.get('aliquota_iva', 0):.0f}",
                f"{riga.get('totale', 0):.2f}",
            ]
        )

    # Column widths (total = 17cm for A4 with 2cm margins)
    col_widths = [0.8 * cm, 7 * cm, 1.5 * cm, 1.5 * cm, 2 * cm, 1.5 * cm, 2.5 * cm]

    # Create table with repeated headers for split pages
    table = Table(data, colWidths=col_widths, repeatRows=1)

    # Table style
    color = HexColor(primary_color)

    table.setStyle(
        TableStyle(
            [
                # Header
                ("BACKGROUND", (0, 0), (-1, 0), color),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                # Data rows
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("ALIGN", (0, 1), (0, -1), "CENTER"),  # Row number
                ("ALIGN", (1, 1), (1, -1), "LEFT"),  # Description
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),  # Numbers
                ("VALIGN", (0, 0), (-1, -1), "TOP"),  # Align all cells to top
                ("TOPPADDING", (0, 1), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                # Grid
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("LINEBELOW", (0, 0), (-1, 0), 2, color),
                # Alternating row colors
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, HexColor("#F9F9F9")]),
            ]
        )
    )

    # Try to fit table in available space
    table_width, table_height = table.wrap(17 * cm, available_height)

    # Check if table fits
    if table_height <= available_height:
        # Table fits on current page
        table.drawOn(canvas, 2 * cm, y_position - table_height)
        return y_position - table_height - 0.5 * cm, []
    else:
        # Table doesn't fit, use split() to break it across pages
        # split() returns list of tables that fit in available_height
        tables = table.split(17 * cm, available_height)

        if not tables:
            # Edge case: even one row doesn't fit (shouldn't happen with our settings)
            # Draw what we can and return empty list
            table.drawOn(canvas, 2 * cm, y_position - table_height)
            return y_position - table_height - 0.5 * cm, []

        # Draw first table on current page
        first_table = tables[0]
        first_width, first_height = first_table.wrap(17 * cm, available_height)
        first_table.drawOn(canvas, 2 * cm, y_position - first_height)

        # Return remaining tables to be drawn on next pages
        remaining = tables[1:] if len(tables) > 1 else []
        return y_position - first_height - 0.5 * cm, remaining
