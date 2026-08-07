"""Footer component for PDF invoices."""

from reportlab.lib.colors import HexColor
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas


def draw_footer(
    canvas: Canvas,
    page_number: int,
    total_pages: int,
    show_digital_signature_note: bool = True,
    footer_text: str | None = None,
    footer_color: str = "#999999",
) -> None:
    """Draw invoice footer with page numbers and optional notes.

    Args:
        canvas: ReportLab canvas
        page_number: Current page number
        total_pages: Total number of pages
        show_digital_signature_note: Show digital signature info
        footer_text: Custom footer text
        footer_color: Footer text color (hex)
    """
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(HexColor(footer_color))

    # Page number (centered)
    page_text = f"Pagina {page_number} di {total_pages}"
    text_width = canvas.stringWidth(page_text, "Helvetica", 8)
    canvas.drawString((21 * cm - text_width) / 2, 1.5 * cm, page_text)  # A4 width = 21cm

    # Digital signature note (left)
    if show_digital_signature_note:
        note = "Documento generato elettronicamente - Conservazione digitale ai sensi del DM 17/06/2014"
        canvas.drawString(2 * cm, 1 * cm, note)

    # Custom footer text (right)
    if footer_text:
        text_width = canvas.stringWidth(footer_text, "Helvetica", 8)
        canvas.drawString(19 * cm - text_width, 1 * cm, footer_text)
