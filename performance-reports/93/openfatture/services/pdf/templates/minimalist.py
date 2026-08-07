"""Minimalist template - Clean and simple design."""

from typing import Any

from reportlab.lib.colors import HexColor
from reportlab.pdfgen.canvas import Canvas

from openfatture.services.pdf.templates.base import BaseTemplate


class MinimalistTemplate(BaseTemplate):
    """Minimalist template with clean, simple design.

    Features:
    - Black and white color scheme
    - Simple typography
    - Minimal visual elements
    - Focus on content clarity
    """

    def get_primary_color(self) -> str:
        """Black primary color."""
        return "#000000"

    def get_secondary_color(self) -> str:
        """Gray secondary color."""
        return "#666666"

    def draw_custom_elements(
        self, canvas: Canvas, fattura_data: dict[str, Any], y_position: float
    ) -> float:
        """Minimalist template has no custom elements.

        Just a simple horizontal line separator.
        """
        # Draw separator line
        canvas.setStrokeColor(HexColor("#CCCCCC"))
        canvas.setLineWidth(0.5)
        canvas.line(2, y_position, 19, y_position)

        return y_position - 0.5
