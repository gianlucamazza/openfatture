"""Base template for PDF generation."""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas

from openfatture.pdf.templates import sections, totals


class BaseTemplate(ABC):
    """Abstract base class for PDF templates.

    All templates must implement:
    - get_primary_color(): Return primary color hex
    - get_secondary_color(): Return secondary color hex
    - draw_custom_elements(): Draw template-specific elements

    The section methods below draw in the template's primary color through
    ``templates.totals`` and ``templates.sections``; a template overrides one
    to change that section's layout. Each returns the next Y position.
    """

    def __init__(self) -> None:
        """Initialize template."""
        self.page_width, self.page_height = A4
        self.margin = 2 * cm
        self.current_page = 1
        self.total_pages = 1  # Will be calculated

    @abstractmethod
    def get_primary_color(self) -> str:
        """Get primary color for this template."""
        pass

    @abstractmethod
    def get_secondary_color(self) -> str:
        """Get secondary color for this template."""
        pass

    @abstractmethod
    def draw_custom_elements(
        self, canvas: Canvas, fattura_data: dict[str, Any], y_position: float
    ) -> float:
        """Draw template-specific custom elements.

        Args:
            canvas: ReportLab canvas
            fattura_data: Invoice data
            y_position: Current Y position

        Returns:
            New Y position after drawing
        """
        pass

    def draw_invoice_info(
        self, canvas: Canvas, fattura_data: dict[str, Any], y_position: float
    ) -> float:
        """Draw invoice number, date, and document type.

        Args:
            canvas: ReportLab canvas
            fattura_data: Invoice data
            y_position: Current Y position

        Returns:
            New Y position after drawing
        """
        primary_color = HexColor(self.get_primary_color())

        # Invoice title
        canvas.setFont("Helvetica-Bold", 24)
        canvas.setFillColor(primary_color)
        canvas.drawString(2 * cm, y_position, "FATTURA")

        # Invoice number and date (right-aligned)
        canvas.setFont("Helvetica", 12)
        numero = f"N. {fattura_data['numero']}/{fattura_data['anno']}"
        data = f"Data: {fattura_data['data_emissione'].strftime('%d/%m/%Y')}"

        numero_width = canvas.stringWidth(numero, "Helvetica", 12)
        data_width = canvas.stringWidth(data, "Helvetica", 12)

        canvas.drawString(19 * cm - numero_width, y_position, numero)
        canvas.drawString(19 * cm - data_width, y_position - 0.6 * cm, data)

        return y_position - 1.5 * cm

    def draw_client_info(
        self, canvas: Canvas, cliente_data: dict[str, Any], y_position: float
    ) -> float:
        """Draw client information.

        Args:
            canvas: ReportLab canvas
            cliente_data: Client data
            y_position: Current Y position

        Returns:
            New Y position after drawing
        """
        canvas.setFont("Helvetica-Bold", 11)
        canvas.setFillColor(HexColor("#333333"))
        canvas.drawString(2 * cm, y_position, "Cliente:")

        canvas.setFont("Helvetica", 10)
        y = y_position - 0.6 * cm

        # Name
        canvas.drawString(2 * cm, y, cliente_data["denominazione"])
        y -= 0.5 * cm

        # Tax codes
        if cliente_data.get("partita_iva"):
            canvas.drawString(2 * cm, y, f"P.IVA: {cliente_data['partita_iva']}")
            y -= 0.4 * cm

        if cliente_data.get("codice_fiscale"):
            canvas.drawString(2 * cm, y, f"C.F.: {cliente_data['codice_fiscale']}")
            y -= 0.4 * cm

        # Address
        indirizzo_parts = []
        if cliente_data.get("indirizzo"):
            addr = cliente_data["indirizzo"]
            if cliente_data.get("numero_civico"):
                addr += f", {cliente_data['numero_civico']}"
            indirizzo_parts.append(addr)

        if cliente_data.get("cap") and cliente_data.get("comune"):
            indirizzo_parts.append(f"{cliente_data['cap']} {cliente_data['comune']}")
            if cliente_data.get("provincia"):
                indirizzo_parts[-1] += f" ({cliente_data['provincia']})"

        for line in indirizzo_parts:
            canvas.drawString(2 * cm, y, line)
            y -= 0.4 * cm

        # Add extra spacing after client info before table
        return y - 0.8 * cm

    def draw_dati_riepilogo(
        self, canvas: Canvas, fattura_data: dict[str, Any], y_position: float
    ) -> float:
        """Draw the Dati di riepilogo table (tax rate / natura breakdown)."""
        return totals.draw_dati_riepilogo(
            canvas, fattura_data, y_position, HexColor(self.get_primary_color())
        )

    def draw_summary(
        self, canvas: Canvas, fattura_data: dict[str, Any], y_position: float
    ) -> float:
        """Draw the totals box."""
        return totals.draw_summary(
            canvas, fattura_data, y_position, HexColor(self.get_primary_color())
        )

    def draw_payment_info(
        self, canvas: Canvas, pagamento_data: dict[str, Any] | None, y_position: float
    ) -> float:
        """Draw the payment details box."""
        return sections.draw_payment_info(
            canvas, pagamento_data, y_position, HexColor(self.get_primary_color())
        )

    def draw_notes(self, canvas: Canvas, note: str | None, y_position: float) -> float:
        """Draw the invoice notes."""
        return sections.draw_notes(canvas, note, y_position)

    def draw_cassa_previdenziale(
        self, canvas: Canvas, cassa_data: list[dict[str, Any]], y_position: float
    ) -> float:
        """Draw the social security contribution (DatiCassaPrevidenziale) box."""
        return sections.draw_cassa_previdenziale(
            canvas, cassa_data, y_position, HexColor(self.get_primary_color())
        )

    def draw_bollo_footer(self, canvas: Canvas, importo_bollo: Decimal, y_position: float) -> float:
        """Draw the stamp duty notice (the bollo is always paid virtually)."""
        return sections.draw_bollo_footer(
            canvas, importo_bollo, y_position, HexColor(self.get_primary_color())
        )
