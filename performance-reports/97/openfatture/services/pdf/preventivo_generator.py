"""PDF Generator for preventivi (quotes/estimates)."""

from pathlib import Path
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas

from openfatture.services.pdf.components import draw_footer, draw_header, draw_invoice_table
from openfatture.services.pdf.generator import PDFGeneratorConfig
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class PreventivoPDFGenerator:
    """PDF Generator for preventivi (quotes/estimates).

    Simplified version of PDFGenerator focused on quotes.
    Reuses existing PDF components for consistency.
    """

    def __init__(self, config: PDFGeneratorConfig | None = None):
        """Initialize PDF generator for preventivi.

        Args:
            config: PDF generator configuration (uses defaults if None)
        """
        self.config = config or PDFGeneratorConfig()

        logger.info(
            "preventivo_pdf_generator_initialized",
            enable_watermark=bool(self.config.watermark_text),
        )

    def generate(
        self,
        preventivo: Any,  # Preventivo model instance
        output_path: str | None = None,
    ) -> Path:
        """Generate PDF for preventivo.

        Args:
            preventivo: Preventivo model instance (from database)
            output_path: Output file path (auto-generates if None)

        Returns:
            Path to generated PDF

        Example:
            >>> pdf_path = generator.generate(preventivo, "preventivo_001.pdf")
        """
        # Convert model to dict
        preventivo_data = self._preventivo_to_dict(preventivo)

        # Auto-generate filename if not provided
        if output_path is None:
            output_path = f"preventivo_{preventivo.numero}_{preventivo.anno}.pdf"

        output_file = Path(output_path)

        logger.info(
            "generating_preventivo_pdf",
            preventivo_id=preventivo.id,
            numero=f"{preventivo.numero}/{preventivo.anno}",
            output_path=str(output_file),
        )

        # Create PDF
        canvas = Canvas(str(output_file), pagesize=A4)

        # Set PDF metadata
        canvas.setAuthor(self.config.company_name or "OpenFatture")
        canvas.setTitle(f"Preventivo {preventivo.numero}/{preventivo.anno}")
        canvas.setSubject(f"Preventivo per {preventivo.cliente.denominazione}")
        canvas.setCreator("OpenFatture - AI-Powered Invoicing")

        # Draw preventivo
        self._draw_preventivo(canvas, preventivo_data)

        # Save PDF
        canvas.save()

        logger.info(
            "preventivo_pdf_generated_successfully",
            preventivo_id=preventivo.id,
            output_path=str(output_file),
            file_size=output_file.stat().st_size,
        )

        return output_file

    def _preventivo_to_dict(self, preventivo: Any) -> dict[str, Any]:
        """Convert Preventivo model to dictionary for rendering.

        Args:
            preventivo: Preventivo model instance

        Returns:
            Dictionary with preventivo data
        """
        # Client data
        cliente_data = {
            "denominazione": preventivo.cliente.denominazione,
            "partita_iva": preventivo.cliente.partita_iva,
            "codice_fiscale": preventivo.cliente.codice_fiscale,
            "indirizzo": preventivo.cliente.indirizzo,
            "numero_civico": preventivo.cliente.numero_civico,
            "cap": preventivo.cliente.cap,
            "comune": preventivo.cliente.comune,
            "provincia": preventivo.cliente.provincia,
        }

        # Line items
        righe_data = []
        for riga in preventivo.righe:
            righe_data.append(
                {
                    "descrizione": riga.descrizione,
                    "quantita": riga.quantita,
                    "prezzo_unitario": riga.prezzo_unitario,
                    "unita_misura": riga.unita_misura,
                    "aliquota_iva": riga.aliquota_iva,
                    "imponibile": riga.imponibile,
                    "iva": riga.iva,
                    "totale": riga.totale,
                }
            )

        return {
            "id": preventivo.id,
            "numero": preventivo.numero,
            "anno": preventivo.anno,
            "data_emissione": preventivo.data_emissione,
            "data_scadenza": preventivo.data_scadenza,
            "validita_giorni": preventivo.validita_giorni,
            "imponibile": preventivo.imponibile,
            "iva": preventivo.iva,
            "totale": preventivo.totale,
            "stato": preventivo.stato.value,
            "note": preventivo.note,
            "condizioni": preventivo.condizioni,
            "cliente": cliente_data,
            "righe": righe_data,
        }

    def _draw_preventivo(self, canvas: Canvas, preventivo_data: dict[str, Any]) -> None:
        """Draw complete preventivo on canvas.

        Args:
            canvas: ReportLab canvas
            preventivo_data: Preventivo data dictionary
        """
        page_width, page_height = A4
        y = page_height - 2 * cm

        # Header with company info
        y = draw_header(
            canvas,
            y,
            company_name=self.config.company_name or "OpenFatture",
            company_vat=self.config.company_vat,
            company_address=self.config.company_address,
            company_city=self.config.company_city,
            logo_path=self.config.logo_path,
            primary_color=self.config.primary_color,
        )

        y -= 1 * cm

        # PREVENTIVO title (prominent)
        canvas.setFont("Helvetica-Bold", 20)
        canvas.setFillColorRGB(0.17, 0.24, 0.31)  # Dark blue
        canvas.drawString(2 * cm, y, "PREVENTIVO")

        y -= 0.8 * cm

        # Preventivo info (number, dates)
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(2 * cm, y, f"N. {preventivo_data['numero']}/{preventivo_data['anno']}")

        canvas.setFont("Helvetica", 10)
        y -= 0.5 * cm
        canvas.drawString(2 * cm, y, f"Data emissione: {preventivo_data['data_emissione']}")

        y -= 0.5 * cm
        canvas.setFont("Helvetica-Bold", 10)
        canvas.setFillColorRGB(0.8, 0.2, 0.2)  # Red for expiration
        canvas.drawString(2 * cm, y, f"Valido fino al: {preventivo_data['data_scadenza']}")
        canvas.setFillColorRGB(0, 0, 0)  # Reset to black

        y -= 0.4 * cm
        canvas.setFont("Helvetica", 9)
        canvas.drawString(2 * cm, y, f"({preventivo_data['validita_giorni']} giorni)")

        y -= 1.2 * cm

        # Client info
        y = self._draw_client_info(canvas, preventivo_data["cliente"], y)

        y -= 1 * cm

        # Line items table
        y, _ = draw_invoice_table(
            canvas,
            y,
            preventivo_data["righe"],
            primary_color=self.config.primary_color,
        )

        y -= 1 * cm

        # Summary (totals)
        y = self._draw_summary(canvas, preventivo_data, y)

        # Notes and conditions
        if preventivo_data.get("note"):
            y -= 1 * cm
            y = self._draw_notes(canvas, preventivo_data["note"], y)

        if preventivo_data.get("condizioni"):
            y -= 0.8 * cm
            y = self._draw_conditions(canvas, preventivo_data["condizioni"], y)

        # Watermark if BOZZA
        if preventivo_data["stato"] == "bozza" or self.config.watermark_text:
            self._draw_watermark(canvas, self.config.watermark_text or "BOZZA")

        # Footer
        draw_footer(
            canvas,
            page_number=1,
            total_pages=1,
            show_digital_signature_note=False,
            footer_text=self.config.footer_text or "Questo preventivo non costituisce fattura",
        )

    def _draw_client_info(self, canvas: Canvas, cliente_data: dict[str, Any], y: float) -> float:
        """Draw client information block."""
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(2 * cm, y, "Cliente:")

        y -= 0.6 * cm
        canvas.setFont("Helvetica", 10)
        canvas.drawString(2 * cm, y, cliente_data["denominazione"])

        if cliente_data.get("partita_iva"):
            y -= 0.5 * cm
            canvas.drawString(2 * cm, y, f"P.IVA: {cliente_data['partita_iva']}")

        if cliente_data.get("indirizzo"):
            y -= 0.5 * cm
            indirizzo_completo = f"{cliente_data['indirizzo']}"
            if cliente_data.get("numero_civico"):
                indirizzo_completo += f", {cliente_data['numero_civico']}"
            canvas.drawString(2 * cm, y, indirizzo_completo)

            if cliente_data.get("cap") and cliente_data.get("comune"):
                y -= 0.5 * cm
                citta = f"{cliente_data['cap']} {cliente_data['comune']}"
                if cliente_data.get("provincia"):
                    citta += f" ({cliente_data['provincia']})"
                canvas.drawString(2 * cm, y, citta)

        return y

    def _draw_summary(self, canvas: Canvas, preventivo_data: dict[str, Any], y: float) -> float:
        """Draw totals summary."""
        page_width, _ = A4
        x_label = page_width - 8 * cm
        x_value = page_width - 4 * cm

        # Box for totals
        canvas.setStrokeColorRGB(0.8, 0.8, 0.8)
        canvas.setFillColorRGB(0.95, 0.95, 0.95)
        canvas.rect(x_label - 0.3 * cm, y - 2.5 * cm, 6 * cm, 2.8 * cm, fill=True, stroke=True)

        canvas.setFillColorRGB(0, 0, 0)
        canvas.setFont("Helvetica", 10)

        y -= 0.6 * cm
        canvas.drawString(x_label, y, "Imponibile:")
        canvas.drawRightString(x_value, y, f"€ {preventivo_data['imponibile']:.2f}")

        y -= 0.5 * cm
        canvas.drawString(x_label, y, "IVA:")
        canvas.drawRightString(x_value, y, f"€ {preventivo_data['iva']:.2f}")

        y -= 0.7 * cm
        canvas.setFont("Helvetica-Bold", 12)
        canvas.drawString(x_label, y, "TOTALE:")
        canvas.drawRightString(x_value, y, f"€ {preventivo_data['totale']:.2f}")

        return y - 1.5 * cm

    def _draw_notes(self, canvas: Canvas, note: str, y: float) -> float:
        """Draw notes section."""
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(2 * cm, y, "Note:")

        y -= 0.5 * cm
        canvas.setFont("Helvetica", 9)

        # Wrap text if too long
        max_width = 17 * cm
        words = note.split()
        line = ""

        for word in words:
            test_line = f"{line} {word}".strip()
            if canvas.stringWidth(test_line, "Helvetica", 9) < max_width:
                line = test_line
            else:
                canvas.drawString(2 * cm, y, line)
                y -= 0.4 * cm
                line = word

        if line:
            canvas.drawString(2 * cm, y, line)
            y -= 0.4 * cm

        return y

    def _draw_conditions(self, canvas: Canvas, condizioni: str, y: float) -> float:
        """Draw terms and conditions section."""
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(2 * cm, y, "Termini e condizioni:")

        y -= 0.5 * cm
        canvas.setFont("Helvetica", 8)

        # Wrap text if too long
        max_width = 17 * cm
        words = condizioni.split()
        line = ""

        for word in words:
            test_line = f"{line} {word}".strip()
            if canvas.stringWidth(test_line, "Helvetica", 8) < max_width:
                line = test_line
            else:
                canvas.drawString(2 * cm, y, line)
                y -= 0.35 * cm
                line = word

        if line:
            canvas.drawString(2 * cm, y, line)
            y -= 0.35 * cm

        return y

    def _draw_watermark(self, canvas: Canvas, text: str) -> None:
        """Draw watermark text diagonally across page."""
        page_width, page_height = A4

        canvas.saveState()
        canvas.setFont("Helvetica-Bold", 80)
        canvas.setFillColorRGB(0.9, 0.9, 0.9)
        canvas.translate(page_width / 2, page_height / 2)
        canvas.rotate(45)
        canvas.drawCentredString(0, 0, text.upper())
        canvas.restoreState()


def create_preventivo_pdf_generator(**kwargs: Any) -> PreventivoPDFGenerator:
    """Factory function to create preventivo PDF generator.

    Args:
        **kwargs: Configuration parameters (same as PDFGeneratorConfig)

    Returns:
        PreventivoPDFGenerator instance

    Example:
        >>> generator = create_preventivo_pdf_generator(
        ...     company_name="ACME S.r.l.",
        ...     logo_path="./logo.png",
        ...     watermark_text="BOZZA"
        ... )
    """
    config = PDFGeneratorConfig(**kwargs)
    return PreventivoPDFGenerator(config)
