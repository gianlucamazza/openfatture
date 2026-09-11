"""Header component for PDF invoices."""

import os

from reportlab.lib.colors import HexColor
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas


def draw_header(
    canvas: Canvas,
    y_position: float,
    company_name: str,
    company_vat: str | None = None,
    company_address: str | None = None,
    company_city: str | None = None,
    logo_path: str | None = None,
    primary_color: str = "#2C3E50",
) -> float:
    """Draw invoice header with cedente (issuer) info and optional logo.

    Args:
        canvas: ReportLab canvas
        y_position: Starting Y position
        company_name: Company name (Denominazione)
        company_vat: VAT number (Partita IVA)
        company_address: Company address (Indirizzo)
        company_city: Company city (Comune)
        logo_path: Path to company logo (optional, file existence not required)
        primary_color: Primary color (hex)

    Returns:
        New Y position after drawing header
    """
    color = HexColor(primary_color)

    # Try to load logo if path provided and file exists
    logo_width = 0.0
    if logo_path and os.path.isfile(logo_path):
        try:
            canvas.drawImage(
                logo_path,
                2 * cm,
                y_position - 2.5 * cm,
                width=3.5 * cm,
                height=2.5 * cm,
                preserveAspectRatio=True,
                mask="auto",
            )
            logo_width = 4 * cm
        except Exception:
            # Logo failed to load, continue without it
            logo_width = 0

    # Cedente (issuer) header block
    x_start = 2 * cm + logo_width

    # Section label
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(HexColor("#666666"))
    canvas.drawString(x_start, y_position - 0.5 * cm, "CEDENTE / PRESTATORE")

    # Company name (larger and prominent)
    canvas.setFont("Helvetica-Bold", 14)
    canvas.setFillColor(color)
    canvas.drawString(x_start, y_position - 1.2 * cm, company_name)

    # Company fiscal details
    canvas.setFont("Helvetica", 10)
    canvas.setFillColor(HexColor("#333333"))
    y = y_position - 1.8 * cm

    if company_vat:
        canvas.drawString(x_start, y, f"Partita IVA: {company_vat}")
        y -= 0.5 * cm

    # Address information
    if company_address or company_city:
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(HexColor("#555555"))

        if company_address:
            canvas.drawString(x_start, y, company_address)
            y -= 0.45 * cm

        if company_city:
            canvas.drawString(x_start, y, company_city)
            y -= 0.45 * cm

    # Return new Y position with margin
    return y - 0.8 * cm
