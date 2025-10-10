"""Professional template - Corporate design with logo support."""

from typing import Any

from reportlab.lib.colors import HexColor
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas

from openfatture.services.pdf.templates.base import BaseTemplate


class ProfessionalTemplate(BaseTemplate):
    """Professional template with corporate design.

    Features:
    - Navy blue color scheme
    - Logo support
    - Professional typography
    - Structured layout with boxes
    """

    def __init__(self, logo_path: str | None = None):
        """Initialize professional template.

        Args:
            logo_path: Path to company logo (optional)
        """
        super().__init__()
        self.logo_path = logo_path

    def get_primary_color(self) -> str:
        """Navy blue primary color."""
        return "#1E3A5F"

    def get_secondary_color(self) -> str:
        """Light blue secondary color."""
        return "#4A90E2"

    def draw_custom_elements(
        self, canvas: Canvas, fattura_data: dict[str, Any], y_position: float
    ) -> float:
        """Draw professional template elements.

        - Colored header bar
        - Decorative elements
        """
        primary_color = HexColor(self.get_primary_color())
        secondary_color = HexColor(self.get_secondary_color())

        # Top colored bar (full width)
        canvas.setFillColor(primary_color)
        canvas.rect(0, self.page_height - 1 * cm, self.page_width, 1 * cm, fill=True, stroke=False)

        # Accent line below
        canvas.setStrokeColor(secondary_color)
        canvas.setLineWidth(3)
        canvas.line(2 * cm, y_position, 19 * cm, y_position)

        # Corner decorative element (right bottom)
        canvas.setFillColor(secondary_color)
        canvas.setFillAlpha(0.1)
        canvas.circle(20 * cm, 1 * cm, 5 * cm, fill=True, stroke=False)
        canvas.setFillAlpha(1.0)

        return y_position - 0.5 * cm
