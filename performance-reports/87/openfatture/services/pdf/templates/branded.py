"""Branded template - Customizable with company branding."""

from typing import Any

from reportlab.lib.colors import HexColor
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas

from openfatture.services.pdf.templates.base import BaseTemplate


class BrandedTemplate(BaseTemplate):
    """Branded template with full customization.

    Features:
    - Custom color scheme
    - Logo and watermark support
    - Brand-specific typography
    - Fully customizable elements
    """

    def __init__(
        self,
        primary_color: str = "#E74C3C",
        secondary_color: str = "#95A5A6",
        logo_path: str | None = None,
        watermark_text: str | None = None,
    ):
        """Initialize branded template.

        Args:
            primary_color: Primary brand color (hex)
            secondary_color: Secondary brand color (hex)
            logo_path: Path to company logo (optional)
            watermark_text: Watermark text (optional, e.g., "BOZZA", "COPIA")
        """
        super().__init__()
        self._primary_color = primary_color
        self._secondary_color = secondary_color
        self.logo_path = logo_path
        self.watermark_text = watermark_text

    def get_primary_color(self) -> str:
        """Return custom primary color."""
        return self._primary_color

    def get_secondary_color(self) -> str:
        """Return custom secondary color."""
        return self._secondary_color

    def draw_custom_elements(
        self, canvas: Canvas, fattura_data: dict[str, Any], y_position: float
    ) -> float:
        """Draw branded template elements.

        - Watermark (if configured)
        - Brand-specific decorations
        """
        primary_color = HexColor(self.get_primary_color())
        secondary_color = HexColor(self.get_secondary_color())

        # Left sidebar accent (vertical)
        canvas.setFillColor(primary_color)
        canvas.setFillAlpha(0.15)
        canvas.rect(0, 0, 0.5 * cm, self.page_height, fill=True, stroke=False)
        canvas.setFillAlpha(1.0)

        # Decorative corner elements
        canvas.setStrokeColor(secondary_color)
        canvas.setLineWidth(2)

        # Top-left corner
        canvas.line(2 * cm, self.page_height - 2 * cm, 4 * cm, self.page_height - 2 * cm)
        canvas.line(2 * cm, self.page_height - 2 * cm, 2 * cm, self.page_height - 4 * cm)

        # Top-right corner
        canvas.line(17 * cm, self.page_height - 2 * cm, 19 * cm, self.page_height - 2 * cm)
        canvas.line(19 * cm, self.page_height - 2 * cm, 19 * cm, self.page_height - 4 * cm)

        # Watermark (if configured)
        if self.watermark_text:
            self._draw_watermark(canvas, self.watermark_text)

        # Horizontal separator with gradient effect (simulated with lines)
        for i in range(5):
            alpha = 0.3 - (i * 0.05)
            canvas.setStrokeColor(secondary_color)
            canvas.setStrokeAlpha(alpha)
            canvas.line(2 * cm, y_position - (i * 0.05 * cm), 19 * cm, y_position - (i * 0.05 * cm))
        canvas.setStrokeAlpha(1.0)

        return y_position - 0.7 * cm

    def _draw_watermark(self, canvas: Canvas, text: str) -> None:
        """Draw diagonal watermark across page.

        Args:
            canvas: ReportLab canvas
            text: Watermark text (e.g., "BOZZA", "COPIA")
        """
        canvas.saveState()

        # Rotate and position
        canvas.translate(self.page_width / 2, self.page_height / 2)
        canvas.rotate(45)

        # Draw text
        canvas.setFont("Helvetica-Bold", 72)
        canvas.setFillColor(HexColor(self.get_secondary_color()))
        canvas.setFillAlpha(0.1)

        text_width = canvas.stringWidth(text, "Helvetica-Bold", 72)
        canvas.drawString(-text_width / 2, 0, text)

        canvas.restoreState()
