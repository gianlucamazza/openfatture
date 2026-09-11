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

    # Style for natura label (smaller, gray)
    natura_style = ParagraphStyle(
        "Natura",
        fontName="Helvetica",
        fontSize=7,
        leading=9,
        alignment=TA_LEFT,
        leftIndent=0,
        rightIndent=0,
        spaceAfter=0,
        spaceBefore=0,
        textColor=HexColor("#666666"),
    )

    # Table data - using list[Any] to accommodate both strings and Paragraph objects
    data: list[list[Any]] = [headers]

    # Mapping of natura codes to Italian labels
    natura_labels = {
        "N1": "N1 - Esclusa ex art.15",
        "N2.1": "N2.1 - Non soggette ad IVA ai sensi degli artt. da 7 a 7-septies del DPR 633/72",
        "N2.2": "N2.2 - Non soggette - altri casi",
        "N3.1": "N3.1 - Non imponibili - esportazioni",
        "N3.2": "N3.2 - Non imponibili - cessioni intracomunitarie",
        "N3.3": "N3.3 - Non imponibili - cessioni verso San Marino",
        "N3.4": "N3.4 - Non imponibili - operazioni assimilate alle cessioni all'esportazione",
        "N3.5": "N3.5 - Non imponibili - a seguito di dichiarazioni d'intento",
        "N3.6": "N3.6 - Non imponibili - altre operazioni",
        "N4": "N4 - Esenti",
        "N5": "N5 - Regime del margine / IVA non esposta in fattura",
        "N6.1": "N6.1 - Inversione contabile - cessione di rottami e altri materiali",
        "N6.2": "N6.2 - Inversione contabile - cessione di oro e argento",
        "N6.3": "N6.3 - Inversione contabile - subappalto nel settore edile",
        "N6.4": "N6.4 - Inversione contabile - cessione di fabbricati",
        "N6.5": "N6.5 - Inversione contabile - cessione di telefoni cellulari",
        "N6.6": "N6.6 - Inversione contabile - cessione di prodotti elettronici",
        "N6.7": "N6.7 - Inversione contabile - prestazioni comparto edile e settori connessi",
        "N6.8": "N6.8 - Inversione contabile - operazioni settore energetico",
        "N6.9": "N6.9 - Inversione contabile - altri casi",
        "N7": "N7 - IVA assolta in altro stato UE",
    }

    for idx, riga in enumerate(righe, start=1):
        # Use Paragraph for description to enable text wrapping
        # Escape HTML special characters to prevent ReportLab markup injection
        descrizione = str(riga.get("descrizione", ""))
        descrizione_escaped = escape(descrizione, quote=False)

        # Check if natura is present
        natura = riga.get("natura")
        if natura:
            # Add natura label below description
            natura_label = natura_labels.get(natura, f"Natura: {natura}")
            # Combine description and natura using HTML-like markup
            combined_text = f"{descrizione_escaped}<br/><font size=7 color='#666666'><i>Natura: {natura_label}</i></font>"
            desc_paragraph = Paragraph(combined_text, desc_style)
        else:
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
