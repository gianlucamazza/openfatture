"""Table component for invoice line items."""

from typing import Any

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Table, TableStyle


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

    # Table data
    data = [headers]

    for idx, riga in enumerate(righe, start=1):
        data.append(
            [
                str(idx),
                str(riga.get("descrizione", ""))[:60],  # Truncate long descriptions
                f"{riga.get('quantita', 0):.2f}",
                riga.get("unita_misura", "ore"),
                f"{riga.get('prezzo_unitario', 0):.2f}",
                f"{riga.get('aliquota_iva', 0):.0f}",
                f"{riga.get('totale', 0):.2f}",
            ]
        )

    # Column widths (total = 17cm for A4 with 2cm margins)
    col_widths = [0.8 * cm, 7 * cm, 1.5 * cm, 1.5 * cm, 2 * cm, 1.5 * cm, 2.5 * cm]

    # Create table
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
                # Data rows
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("ALIGN", (0, 1), (0, -1), "CENTER"),  # Row number
                ("ALIGN", (1, 1), (1, -1), "LEFT"),  # Description
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),  # Numbers
                ("TOPPADDING", (0, 1), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
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
