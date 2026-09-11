"""Professional template - Corporate design with logo support."""

from typing import Any

from reportlab.lib.colors import HexColor
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas

from openfatture.pdf.templates.base import BaseTemplate


class ProfessionalTemplate(BaseTemplate):
    """Professional template with corporate design.

    Features:
    - Navy blue color scheme
    - Logo support
    - Professional typography with improved spacing
    - Cedente (issuer) header block
    - IBAN/payment information block
    - Structured layout with clean boxes
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

        - Accent line
        """
        secondary_color = HexColor(self.get_secondary_color())

        # Accent line below header
        canvas.setStrokeColor(secondary_color)
        canvas.setLineWidth(2)
        canvas.line(2 * cm, y_position, 19 * cm, y_position)

        return y_position - 0.8 * cm
