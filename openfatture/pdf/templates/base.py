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

        # Add spacing before summary to prevent overlap with table
        y_position -= 1.0 * cm

        # Summary box (right-aligned)
        box_width = 7 * cm
        box_x = 19 * cm - box_width

        # Calculate box height based on content
        line_height = 0.6 * cm
        num_lines = 3  # Imponibile, IVA, Total

        # Add lines for optional fields
        if fattura_data.get("ritenuta_acconto", Decimal(0)) > 0:
            num_lines += 1
        if fattura_data.get("importo_bollo", Decimal(0)) > 0:
            num_lines += 1

        box_height = (num_lines * line_height) + 1.4 * cm
        box_y = y_position - box_height

        # Background
        canvas.setFillColor(HexColor("#F5F5F5"))
        canvas.rect(box_x, box_y, box_width, box_height, fill=True, stroke=False)

        # Border
        canvas.setStrokeColor(primary_color)
        canvas.setLineWidth(1)
        canvas.rect(box_x, box_y, box_width, box_height, fill=False, stroke=True)

        # Summary items
        canvas.setFont("Helvetica", 10)
        canvas.setFillColor(HexColor("#333333"))

        y = y_position - 0.7 * cm

        # Imponibile
        canvas.drawString(box_x + 0.3 * cm, y, "Imponibile:")
        canvas.drawRightString(
            box_x + box_width - 0.3 * cm, y, f"€ {fattura_data['imponibile']:.2f}"
        )
        y -= line_height

        # IVA
        canvas.drawString(box_x + 0.3 * cm, y, "IVA:")
        canvas.drawRightString(box_x + box_width - 0.3 * cm, y, f"€ {fattura_data['iva']:.2f}")
        y -= line_height

        # Ritenuta (if present)
        if fattura_data.get("ritenuta_acconto", Decimal(0)) > 0:
            canvas.drawString(box_x + 0.3 * cm, y, "Ritenuta d'acconto:")
            canvas.drawRightString(
                box_x + box_width - 0.3 * cm, y, f"- € {fattura_data['ritenuta_acconto']:.2f}"
            )
            y -= line_height

        # Bollo (if present)
        if fattura_data.get("importo_bollo", Decimal(0)) > 0:
            canvas.drawString(box_x + 0.3 * cm, y, "Bollo:")
            canvas.drawRightString(
                box_x + box_width - 0.3 * cm, y, f"€ {fattura_data['importo_bollo']:.2f}"
            )
            y -= line_height

        # Total (bold)
        canvas.setFont("Helvetica-Bold", 12)
        canvas.setFillColor(primary_color)
        y -= 0.2 * cm
        canvas.drawString(box_x + 0.3 * cm, y, "TOTAL:")
        canvas.drawRightString(box_x + box_width - 0.3 * cm, y, f"€ {fattura_data['totale']:.2f}")

        return box_y - 0.5 * cm

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

        # Add spacing before payment info
        y_position -= 0.8 * cm

        primary_color = HexColor(self.get_primary_color())

        # Calculate block height based on content
        line_count = 1  # Method
        if pagamento_data.get("data_scadenza"):
            line_count += 1
        if pagamento_data.get("iban"):
            line_count += 1
        if pagamento_data.get("bic_swift"):
            line_count += 1

        block_height = (line_count * 0.5 + 0.8) * cm
        block_width = 8 * cm

        # Draw background box
        canvas.setFillColor(HexColor("#F8F9FA"))
        canvas.setStrokeColor(primary_color)
        canvas.setLineWidth(1)
        canvas.rect(
            2 * cm, y_position - block_height, block_width, block_height, fill=True, stroke=True
        )

        # Title
        canvas.setFont("Helvetica-Bold", 10)
        canvas.setFillColor(primary_color)
        canvas.drawString(2.3 * cm, y_position - 0.6 * cm, "MODALITÀ DI PAGAMENTO")

        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(HexColor("#333333"))
        y = y_position - 1.1 * cm

        # Payment method
        modalita_map = {
            "MP05": "Bonifico bancario",
            "MP08": "Carta di credito",
            "MP01": "Contanti",
        }
        modalita_label = modalita_map.get(
            pagamento_data.get("modalita", ""), pagamento_data.get("modalita", "Bonifico bancario")
        )
        canvas.drawString(2.3 * cm, y, f"Modalità: {modalita_label}")
        y -= 0.5 * cm

        # Due date
        if pagamento_data.get("data_scadenza"):
            scadenza = pagamento_data["data_scadenza"].strftime("%d/%m/%Y")
            canvas.drawString(2.3 * cm, y, f"Scadenza: {scadenza}")
            y -= 0.5 * cm

        # IBAN (prominent for bank transfers)
        if pagamento_data.get("iban"):
            canvas.setFont("Helvetica-Bold", 9)
            canvas.drawString(2.3 * cm, y, f"IBAN: {pagamento_data['iban']}")
            canvas.setFont("Helvetica", 9)
            y -= 0.5 * cm

        # BIC
        if pagamento_data.get("bic_swift"):
            canvas.drawString(2.3 * cm, y, f"BIC: {pagamento_data['bic_swift']}")
            y -= 0.5 * cm

        return y_position - block_height - 0.5 * cm

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

        # Add spacing before notes
        y_position -= 0.8 * cm

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

    def draw_cassa_previdenziale(
        self, canvas: Canvas, cassa_data: list[dict[str, Any]], y_position: float
    ) -> float:
        """Draw social security contribution (DatiCassaPrevidenziale) block.

        Args:
            canvas: ReportLab canvas
            cassa_data: List of cassa previdenziale entries
            y_position: Current Y position

        Returns:
            New Y position after drawing
        """
        if not cassa_data:
            return y_position

        # Add spacing before block
        y_position -= 0.8 * cm

        primary_color = HexColor(self.get_primary_color())

        # Calculate block dimensions
        entries_count = len(cassa_data)
        line_height = 0.5 * cm
        block_height = (entries_count * 4 * line_height) + 1.2 * cm
        block_width = 8 * cm

        # Draw background box
        canvas.setFillColor(HexColor("#F8F9FA"))
        canvas.setStrokeColor(primary_color)
        canvas.setLineWidth(1)
        canvas.rect(
            2 * cm, y_position - block_height, block_width, block_height, fill=True, stroke=True
        )

        # Title
        canvas.setFont("Helvetica-Bold", 10)
        canvas.setFillColor(primary_color)
        canvas.drawString(2.3 * cm, y_position - 0.6 * cm, "CASSA PREVIDENZIALE")

        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(HexColor("#333333"))
        y = y_position - 1.1 * cm

        # Map tipo_cassa codes to labels
        tipo_cassa_labels = {
            "TC01": "Cassa nazionale previdenza avvocati",
            "TC02": "Cassa previdenza dottori commercialisti",
            "TC03": "Cassa previdenza e assistenza geometri",
            "TC04": "Cassa nazionale previdenza e assistenza ingegneri e architetti",
            "TC05": "Cassa nazionale del notariato",
            "TC06": "Cassa nazionale previdenza e assistenza ragionieri e periti commerciali",
            "TC07": "ENPACL (Consulenti del lavoro)",
            "TC08": "ENPAM (Medici)",
            "TC09": "ENPAP (Psicologi)",
            "TC10": "ENPAF (Farmacisti)",
            "TC11": "ENPAV (Veterinari)",
            "TC12": "ENPAIA (Periti agrari e agrotecnici)",
            "TC13": "EPPI (Periti industriali)",
            "TC14": "EPAP (Attuari, chimici, dottori agronomi e forestali, geologi)",
            "TC15": "ENPAB (Biologi)",
            "TC16": "ENPAPI (Infermieri)",
            "TC17": "ENPAP (Psicologi - duplicato)",
            "TC18": "ENPAIA (Agrotecnici e periti agrari - duplicato)",
            "TC19": "EPPI (Periti industriali - duplicato)",
            "TC20": "EPAP (Attuari, chimici, ecc. - duplicato)",
            "TC21": "ENPAB (Biologi - duplicato)",
            "TC22": "INPS",
        }

        for cassa in cassa_data:
            tipo_cassa = cassa.get("tipo_cassa", "")
            tipo_label = tipo_cassa_labels.get(tipo_cassa, tipo_cassa)

            canvas.setFont("Helvetica-Bold", 9)
            canvas.drawString(2.3 * cm, y, f"Tipo: {tipo_label}")
            y -= line_height

            canvas.setFont("Helvetica", 9)
            canvas.drawString(2.3 * cm, y, f"Aliquota: {cassa.get('al_cassa', 0):.2f}%")
            y -= line_height

            if cassa.get("imponibile_cassa"):
                canvas.drawString(
                    2.3 * cm, y, f"Imponibile: € {cassa.get('imponibile_cassa', 0):.2f}"
                )
                y -= line_height

            canvas.drawString(
                2.3 * cm, y, f"Importo: € {cassa.get('importo_contributo_cassa', 0):.2f}"
            )
            y -= line_height

            # Show natura if present
            if cassa.get("natura"):
                natura = cassa.get("natura", "")
                natura_labels_map = {
                    "N1": "Esclusa ex art.15",
                    "N2.2": "Non soggette - altri casi",
                }
                natura_label = natura_labels_map.get(natura, natura)
                canvas.setFont("Helvetica", 8)
                canvas.setFillColor(HexColor("#666666"))
                canvas.drawString(2.3 * cm, y, f"Natura: {natura_label}")
                canvas.setFillColor(HexColor("#333333"))
                y -= line_height

        return y_position - block_height - 0.5 * cm

    def draw_bollo_footer(self, canvas: Canvas, importo_bollo: Decimal, y_position: float) -> float:
        """Draw bollo (stamp duty) MEF footer text.

        Args:
            canvas: ReportLab canvas
            importo_bollo: Stamp duty amount
            y_position: Current Y position

        Returns:
            New Y position after drawing
        """
        if importo_bollo <= 0:
            return y_position

        # Add spacing before footer
        y_position -= 0.8 * cm

        # Draw bollo footer text
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(HexColor("#333333"))
        canvas.drawString(
            2 * cm,
            y_position,
            "Bollo assolto ai sensi del decreto MEF 17 GIUGNO 2014 (ART. 6)",
        )

        return y_position - 0.5 * cm
