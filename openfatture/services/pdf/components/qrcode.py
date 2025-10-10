"""QR Code component for pagoPa integration."""

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas


def draw_qr_code(
    canvas: Canvas,
    x_position: float,
    y_position: float,
    data: str,
    size: float = 3 * cm,
) -> None:
    """Draw QR code for pagoPa or other payment systems.

    Args:
        canvas: ReportLab canvas
        x_position: X position
        y_position: Y position (bottom-left corner)
        data: QR code data (e.g., pagoPa URL or SEPA payment string)
        size: QR code size (square)
    """
    # Create QR code widget
    qr = QrCodeWidget(data)

    # Create drawing
    drawing = Drawing(size, size)
    drawing.add(qr)

    # Scale to fit
    qr.barWidth = size
    qr.barHeight = size

    # Render on canvas
    renderPDF.draw(drawing, canvas, x_position, y_position)


def generate_pagopa_qr_data(
    creditor_fiscal_code: str,
    notice_number: str,
    amount: float,
) -> str:
    """Generate pagoPa QR code data.

    Args:
        creditor_fiscal_code: Creditor's fiscal code
        notice_number: Payment notice number (18 digits)
        amount: Amount in EUR (cents)

    Returns:
        pagoPa QR code string

    Example:
        >>> data = generate_pagopa_qr_data("12345678901", "123456789012345678", 10050)
        >>> # data = "PAGOPA|002|123456789012345678|12345678901|10050"
    """
    # pagoPa QR format: PAGOPA|version|notice_number|fiscal_code|amount_cents
    version = "002"
    amount_cents = int(amount * 100)

    return f"PAGOPA|{version}|{notice_number}|{creditor_fiscal_code}|{amount_cents}"


def generate_sepa_qr_data(
    beneficiary_name: str,
    iban: str,
    amount: float,
    reference: str,
    bic: str | None = None,
) -> str:
    """Generate SEPA payment QR code (EPC QR Code).

    Args:
        beneficiary_name: Beneficiary name
        iban: IBAN
        amount: Amount in EUR
        reference: Payment reference
        bic: BIC/SWIFT code (optional)

    Returns:
        EPC QR code string

    Format:
        https://www.europeanpaymentscouncil.eu/document-library/guidance-documents/quick-response-code-guidelines-enable-data-capture-initiation
    """
    lines = [
        "BCD",  # Service tag
        "002",  # Version
        "1",  # Character set (1 = UTF-8)
        "SCT",  # Identification (SEPA Credit Transfer)
        bic or "",  # BIC (optional)
        beneficiary_name[:70],  # Beneficiary name (max 70 chars)
        iban.replace(" ", ""),  # IBAN (no spaces)
        f"EUR{amount:.2f}",  # Amount with currency
        "",  # Purpose (optional)
        "",  # Structured reference (optional)
        reference[:140],  # Unstructured reference (max 140 chars)
        "",  # Beneficiary to originator info (optional)
    ]

    return "\n".join(lines)
