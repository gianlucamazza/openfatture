"""Base template for PDF generation."""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas


class BaseTemplate(ABC):
    """Abstract base class for PDF templates.

    All templates must implement:
    - get_primary_color(): Return primary color hex
    - get_secondary_color(): Return secondary color hex
    - draw_custom_elements(): Draw template-specific elements
    """

    def __init__(self):
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

        return y - 0.5 * cm

    def draw_summary(
        self, canvas: Canvas, fattura_data: dict[str, Any], y_position: float
    ) -> float:
        """Draw invoice summary (totals).

        Args:
            canvas: ReportLab canvas
            fattura_data: Invoice data
            y_position: Current Y position

        Returns:
            New Y position after drawing
        """
        primary_color = HexColor(self.get_primary_color())

        # Summary box (right-aligned)
        box_width = 7 * cm
        box_x = 19 * cm - box_width

        # Background
        canvas.setFillColor(HexColor("#F5F5F5"))
        canvas.rect(box_x, y_position - 3 * cm, box_width, 3 * cm, fill=True, stroke=False)

        # Border
        canvas.setStrokeColor(primary_color)
        canvas.setLineWidth(1)
        canvas.rect(box_x, y_position - 3 * cm, box_width, 3 * cm, fill=False, stroke=True)

        # Summary items
        canvas.setFont("Helvetica", 10)
        canvas.setFillColor(HexColor("#333333"))

        y = y_position - 0.7 * cm

        # Imponibile
        canvas.drawString(box_x + 0.3 * cm, y, "Imponibile:")
        canvas.drawRightString(
            box_x + box_width - 0.3 * cm, y, f"€ {fattura_data['imponibile']:.2f}"
        )
        y -= 0.6 * cm

        # IVA
        canvas.drawString(box_x + 0.3 * cm, y, "IVA:")
        canvas.drawRightString(box_x + box_width - 0.3 * cm, y, f"€ {fattura_data['iva']:.2f}")
        y -= 0.6 * cm

        # Ritenuta (if present)
        if fattura_data.get("ritenuta_acconto", Decimal(0)) > 0:
            canvas.drawString(box_x + 0.3 * cm, y, "Ritenuta d'acconto:")
            canvas.drawRightString(
                box_x + box_width - 0.3 * cm, y, f"- € {fattura_data['ritenuta_acconto']:.2f}"
            )
            y -= 0.6 * cm

        # Bollo (if present)
        if fattura_data.get("importo_bollo", Decimal(0)) > 0:
            canvas.drawString(box_x + 0.3 * cm, y, "Bollo:")
            canvas.drawRightString(
                box_x + box_width - 0.3 * cm, y, f"€ {fattura_data['importo_bollo']:.2f}"
            )
            y -= 0.6 * cm

        # Total (bold)
        canvas.setFont("Helvetica-Bold", 12)
        canvas.setFillColor(primary_color)
        y -= 0.2 * cm
        canvas.drawString(box_x + 0.3 * cm, y, "TOTALE:")
        canvas.drawRightString(box_x + box_width - 0.3 * cm, y, f"€ {fattura_data['totale']:.2f}")

        return y_position - 3.5 * cm

    def draw_payment_info(
        self, canvas: Canvas, pagamento_data: dict[str, Any] | None, y_position: float
    ) -> float:
        """Draw payment information.

        Args:
            canvas: ReportLab canvas
            pagamento_data: Payment data (optional)
            y_position: Current Y position

        Returns:
            New Y position after drawing
        """
        if not pagamento_data:
            return y_position

        canvas.setFont("Helvetica-Bold", 11)
        canvas.setFillColor(HexColor("#333333"))
        canvas.drawString(2 * cm, y_position, "Modalità di pagamento:")

        canvas.setFont("Helvetica", 10)
        y = y_position - 0.6 * cm

        # Payment method
        canvas.drawString(2 * cm, y, f"Modalità: {pagamento_data.get('modalita', 'Bonifico')}")
        y -= 0.5 * cm

        # Due date
        if pagamento_data.get("data_scadenza"):
            scadenza = pagamento_data["data_scadenza"].strftime("%d/%m/%Y")
            canvas.drawString(2 * cm, y, f"Scadenza: {scadenza}")
            y -= 0.5 * cm

        # IBAN
        if pagamento_data.get("iban"):
            canvas.drawString(2 * cm, y, f"IBAN: {pagamento_data['iban']}")
            y -= 0.5 * cm

        # BIC
        if pagamento_data.get("bic_swift"):
            canvas.drawString(2 * cm, y, f"BIC/SWIFT: {pagamento_data['bic_swift']}")
            y -= 0.5 * cm

        return y - 0.5 * cm

    def draw_notes(self, canvas: Canvas, note: str | None, y_position: float) -> float:
        """Draw invoice notes.

        Args:
            canvas: ReportLab canvas
            note: Invoice notes
            y_position: Current Y position

        Returns:
            New Y position after drawing
        """
        if not note:
            return y_position

        canvas.setFont("Helvetica-Bold", 10)
        canvas.setFillColor(HexColor("#333333"))
        canvas.drawString(2 * cm, y_position, "Note:")

        canvas.setFont("Helvetica", 9)
        y = y_position - 0.5 * cm

        # Split notes into lines (max 80 chars per line)
        words = note.split()
        lines = []
        current_line = ""

        for word in words:
            if len(current_line) + len(word) + 1 <= 80:
                current_line += word + " "
            else:
                lines.append(current_line.strip())
                current_line = word + " "

        if current_line:
            lines.append(current_line.strip())

        for line in lines:
            canvas.drawString(2 * cm, y, line)
            y -= 0.4 * cm

        return y - 0.3 * cm
