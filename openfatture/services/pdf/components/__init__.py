"""PDF components for invoice generation."""

from openfatture.services.pdf.components.footer import draw_footer
from openfatture.services.pdf.components.header import draw_header
from openfatture.services.pdf.components.qrcode import draw_qr_code
from openfatture.services.pdf.components.table import draw_invoice_table

__all__ = [
    "draw_header",
    "draw_footer",
    "draw_invoice_table",
    "draw_qr_code",
]
