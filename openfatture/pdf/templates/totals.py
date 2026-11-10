"""Totals of an invoice PDF: the VAT breakdown table and the totals box."""

from decimal import Decimal
from typing import Any

from reportlab.lib.colors import Color, HexColor
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas

NATURA_LABELS = {
    "N1": "Escluse ex art. 15",
    "N2.1": "Non soggette - art. 7-bis",
    "N2.2": "Non soggette - altri casi",
    "N3.1": "Non imponibili - esportazioni",
    "N3.2": "Non imponibili - cessioni intracomunitarie",
    "N3.3": "Non imponibili - cessioni verso San Marino",
    "N3.4": "Non imponibili - operazioni assimilate",
    "N3.5": "Non imponibili - dichiarazioni d'intento",
    "N3.6": "Non imponibili - altre operazioni",
    "N4": "Esenti",
    "N5": "Regime del margine",
    "N6.1": "Inversione contabile - cessione rottami",
    "N6.2": "Inversione contabile - cessione oro",
    "N6.3": "Inversione contabile - subappalto",
    "N6.4": "Inversione contabile - cessione fabbricati",
    "N6.5": "Inversione contabile - cessione telefoni cellulari",
    "N6.6": "Inversione contabile - cessione prodotti elettronici",
    "N6.7": "Inversione contabile - prestazioni settore edile",
    "N6.8": "Inversione contabile - operazioni settore energetico",
    "N6.9": "Inversione contabile - altri casi",
    "N7": "IVA assolta in altro stato UE",
}


def summary_rows(fattura_data: dict[str, Any]) -> list[tuple[str, Decimal]]:
    """Rows of the totals box; the last one is what the customer pays.

    The stamp duty is not a row: it is paid virtually, and when it is charged
    to the customer it is already an N1 line in the totals.
    """
    rows: list[tuple[str, Decimal]] = [
        ("Imponibile", fattura_data["imponibile"]),
        ("IVA", fattura_data["iva"]),
        ("Totale documento", fattura_data["totale"]),
    ]
    ritenuta = fattura_data.get("ritenuta_acconto") or Decimal(0)
    if ritenuta > 0:
        rows.append(("Ritenuta d'acconto", -ritenuta))
        rows.append(("Netto a pagare", fattura_data["importo_da_pagare"]))
    return rows


def draw_dati_riepilogo(
    canvas: Canvas, fattura_data: dict[str, Any], y_position: float, primary_color: Color
) -> float:
    """Draw the Dati di riepilogo table (tax rate / natura breakdown).

    Returns the Y position after the table.
    """
    # Same breakdown as the XML DatiRiepilogo (billing.application.totals)
    riepilogo: dict[tuple[Decimal, str | None], dict[str, Decimal]] = {
        (row["aliquota_iva"], row["natura"]): {
            "imponibile": row["imponibile"],
            "iva": row["imposta"],
        }
        for row in fattura_data.get("riepilogo", [])
    }

    if not riepilogo:
        return y_position

    # Add spacing before riepilogo
    y_position -= 0.6 * cm

    # Table dimensions
    table_width = 17 * cm
    table_x = 2 * cm
    row_height = 0.6 * cm
    header_height = 0.7 * cm

    # Title
    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(primary_color)
    canvas.drawString(table_x, y_position - 0.5 * cm, "DATI DI RIEPILOGO")

    y_position -= 0.8 * cm

    # Header background
    canvas.setFillColor(HexColor("#F5F5F5"))
    canvas.rect(
        table_x, y_position - header_height, table_width, header_height, fill=True, stroke=False
    )

    # Header border
    canvas.setStrokeColor(primary_color)
    canvas.setLineWidth(1)
    canvas.rect(
        table_x, y_position - header_height, table_width, header_height, fill=False, stroke=True
    )

    # Header text
    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(HexColor("#333333"))
    y_header = y_position - 0.5 * cm

    col_widths = [3 * cm, 7 * cm, 3.5 * cm, 3.5 * cm]
    col_positions = [
        table_x + 0.2 * cm,
        table_x + col_widths[0] + 0.2 * cm,
        table_x + col_widths[0] + col_widths[1] + 0.2 * cm,
        table_x + col_widths[0] + col_widths[1] + col_widths[2] + 0.2 * cm,
    ]

    canvas.drawString(col_positions[0], y_header, "Aliquota IVA")
    canvas.drawString(col_positions[1], y_header, "Natura")
    canvas.drawRightString(col_positions[2] + col_widths[2] - 0.4 * cm, y_header, "Imponibile")
    canvas.drawRightString(col_positions[3] + col_widths[3] - 0.4 * cm, y_header, "Imposta")

    # Data rows
    canvas.setFont("Helvetica", 9)
    y_data = y_position - header_height

    for row_index, ((aliquota, natura), values) in enumerate(riepilogo.items()):
        # Row background (alternating)
        if row_index % 2 == 1:
            canvas.setFillColor(HexColor("#FAFAFA"))
            canvas.rect(
                table_x, y_data - row_height, table_width, row_height, fill=True, stroke=False
            )

        # Row border
        canvas.setStrokeColor(HexColor("#E0E0E0"))
        canvas.setLineWidth(0.5)
        canvas.rect(table_x, y_data - row_height, table_width, row_height, fill=False, stroke=True)

        # Data
        canvas.setFillColor(HexColor("#333333"))
        y_text = y_data - 0.45 * cm

        # Aliquota
        if aliquota > 0:
            canvas.drawString(col_positions[0], y_text, f"{aliquota:.0f}%")
        else:
            canvas.drawString(col_positions[0], y_text, "-")

        natura_label = NATURA_LABELS.get(natura, natura) if natura else "-"
        canvas.drawString(col_positions[1], y_text, natura_label)

        # Imponibile
        canvas.drawRightString(
            col_positions[2] + col_widths[2] - 0.4 * cm, y_text, f"€ {values['imponibile']:.2f}"
        )

        # Imposta
        canvas.drawRightString(
            col_positions[3] + col_widths[3] - 0.4 * cm, y_text, f"€ {values['iva']:.2f}"
        )

        y_data -= row_height

    return y_data - 0.5 * cm


def draw_summary(
    canvas: Canvas, fattura_data: dict[str, Any], y_position: float, primary_color: Color
) -> float:
    """Draw the totals box (right-aligned).

    Returns the Y position after the box.
    """
    # Add spacing before summary to prevent overlap with table
    y_position -= 0.6 * cm

    box_width = 7 * cm
    box_x = 19 * cm - box_width

    line_height = 0.6 * cm
    rows = summary_rows(fattura_data)
    box_height = (len(rows) * line_height) + 1.4 * cm
    box_y = y_position - box_height

    # Background
    canvas.setFillColor(HexColor("#F5F5F5"))
    canvas.rect(box_x, box_y, box_width, box_height, fill=True, stroke=False)

    # Border
    canvas.setStrokeColor(primary_color)
    canvas.setLineWidth(1)
    canvas.rect(box_x, box_y, box_width, box_height, fill=False, stroke=True)

    y = y_position - 0.7 * cm
    for index, (label, amount) in enumerate(rows):
        last = index == len(rows) - 1
        if last:
            canvas.setFont("Helvetica-Bold", 12)
            canvas.setFillColor(primary_color)
            y -= 0.2 * cm
        else:
            canvas.setFont("Helvetica", 10)
            canvas.setFillColor(HexColor("#333333"))
        canvas.drawString(box_x + 0.3 * cm, y, f"{label}:")
        sign = "- " if amount < 0 else ""
        canvas.drawRightString(box_x + box_width - 0.3 * cm, y, f"{sign}€ {abs(amount):.2f}")
        y -= line_height

    return box_y - 0.5 * cm
