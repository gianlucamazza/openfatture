"""Header component for PDF invoices."""

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
    """Draw invoice header with company info and optional logo.

    Args:
        canvas: ReportLab canvas
        y_position: Starting Y position
        company_name: Company name
        company_vat: VAT number
        company_address: Company address
        company_city: Company city
        logo_path: Path to company logo (optional)
        primary_color: Primary color (hex)

    Returns:
        New Y position after drawing header
    """
    color = HexColor(primary_color)

    # Logo (if provided)
    if logo_path:
        try:
            canvas.drawImage(
                logo_path,
                2 * cm,
                y_position - 2 * cm,
                width=3 * cm,
                height=2 * cm,
                preserveAspectRatio=True,
                mask="auto",
            )
            logo_width = 3 * cm
        except Exception:
            # Logo not found or invalid, skip
            logo_width = 0
    else:
        logo_width = 0

    # Company name
    canvas.setFont("Helvetica-Bold", 16)
    canvas.setFillColor(color)
    canvas.drawString(2 * cm + logo_width + 0.5 * cm, y_position - 1 * cm, company_name)

    # Company details
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(HexColor("#555555"))

    y = y_position - 1.5 * cm

    if company_vat:
        canvas.drawString(2 * cm + logo_width + 0.5 * cm, y, f"P.IVA: {company_vat}")
        y -= 0.4 * cm

    if company_address:
        canvas.drawString(2 * cm + logo_width + 0.5 * cm, y, company_address)
        y -= 0.4 * cm

    if company_city:
        canvas.drawString(2 * cm + logo_width + 0.5 * cm, y, company_city)
        y -= 0.4 * cm

    # Return new Y position with margin
    return y - 1 * cm
