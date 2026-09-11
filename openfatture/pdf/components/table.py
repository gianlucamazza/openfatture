"""Table component for invoice line items."""

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
    max_height: float = 15 * cm,
) -> tuple[float, bool]:
    """Draw invoice line items table.

    Args:
        canvas: ReportLab canvas
        y_position: Starting Y position
        righe: List of invoice lines (dicts with descrizione, quantita, prezzo_unitario, etc.)
        primary_color: Header color (hex)
        max_height: Maximum table height (for pagination)

    Returns:
        Tuple of (new Y position, needs_new_page)
    """
    if not righe:
        return y_position, False

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
        descrizione = str(riga.get("descrizione", ""))
        desc_paragraph = Paragraph(descrizione, desc_style)

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

    # Create table with row height
    # Let rows auto-size based on wrapped content
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

    # Calculate table height
    table_width, table_height = table.wrap(17 * cm, max_height)

    # Check if table fits on current page
    needs_new_page = table_height > max_height or y_position - table_height < 5 * cm

    if not needs_new_page:
        # Draw table
        table.drawOn(canvas, 2 * cm, y_position - table_height)
        return y_position - table_height - 0.5 * cm, False
    else:
        # Table too large, needs pagination (handled by caller)
        return y_position, True
