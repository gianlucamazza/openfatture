"""Footer component for PDF invoices."""

from reportlab.lib.colors import HexColor
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas

# The fiscal original of an Italian e-invoice is the FatturaPA XML that went
# through SDI; any PDF rendering is only a courtesy copy.
COURTESY_COPY_NOTE = (
    "Copia di cortesia priva di valore fiscale: l'originale è la fattura "
    "elettronica XML trasmessa tramite SDI."
)


def draw_footer(
    canvas: Canvas,
    page_number: int,
    total_pages: int,
    legal_note: str | None = None,
    footer_text: str | None = None,
    footer_color: str = "#999999",
) -> None:
    """Draw the footer: page numbers, an optional legal note and custom text.

    Args:
        canvas: ReportLab canvas
        page_number: Current page number
        total_pages: Total number of pages
        legal_note: Statement about the document's legal value (left)
        footer_text: Custom footer text (right, below the legal note)
        footer_color: Footer text color (hex)
    """
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(HexColor(footer_color))

    # Page number (centered)
    page_text = f"Pagina {page_number} di {total_pages}"
    text_width = canvas.stringWidth(page_text, "Helvetica", 8)
    canvas.drawString((21 * cm - text_width) / 2, 1.5 * cm, page_text)  # A4 width = 21cm

    if legal_note:
        canvas.drawString(2 * cm, 1 * cm, legal_note)

    if footer_text:
        text_width = canvas.stringWidth(footer_text, "Helvetica", 8)
        canvas.drawString(19 * cm - text_width, 0.6 * cm, footer_text)
