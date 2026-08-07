"""PDF components for invoice generation."""

from openfatture.pdf.components.footer import draw_footer
from openfatture.pdf.components.header import draw_header
from openfatture.pdf.components.qrcode import draw_qr_code
from openfatture.pdf.components.table import draw_invoice_table

__all__ = [
    "draw_header",
    "draw_footer",
    "draw_invoice_table",
    "draw_qr_code",
]
