"""PDF Generator for OpenFatture invoices.

Enterprise-grade PDF generation with:
- Multiple templates (minimalist, professional, branded)
- PDF/A-3 compliance for legal archiving
- QR code support (pagoPa, SEPA)
- Automatic pagination
- Type-safe configuration
"""

from decimal import Decimal
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas

from openfatture.pdf.components import (
    draw_footer,
    draw_header,
    draw_invoice_table,
    draw_qr_code,
)
from openfatture.pdf.components.qrcode import generate_sepa_qr_data
from openfatture.pdf.templates import (
    BaseTemplate,
    BrandedTemplate,
    MinimalistTemplate,
    ProfessionalTemplate,
)
from openfatture.platform.logging import get_logger

logger = get_logger(__name__)


class PDFGeneratorConfig(BaseModel):
    """PDF Generator configuration.

    Example:
        >>> config = PDFGeneratorConfig(
        ...     template="professional", logo_path="./logo.png", enable_qr_code=True
        ... )
    """

    # Template
    template: str = Field(default="professional", description="Template name")

    # Company info (for header)
    company_name: str = Field(default="", description="Company name")
    company_vat: str | None = Field(default=None, description="Company VAT number")
    company_address: str | None = Field(default=None, description="Company address")
    company_city: str | None = Field(default=None, description="Company city")
    logo_path: str | None = Field(default=None, description="Path to logo")

    # Colors (for branded template)
    primary_color: str = Field(default="#2C3E50", description="Primary color (hex)")
    secondary_color: str = Field(default="#95A5A6", description="Secondary color (hex)")

    # QR Code
    enable_qr_code: bool = Field(default=False, description="Enable QR code for payments")
    qr_code_type: str = Field(default="sepa", description="QR code type (sepa, pagopa)")

    # PDF/A
    enable_pdfa: bool = Field(default=True, description="Enable PDF/A-3 compliance")

    # Watermark
    watermark_text: str | None = Field(default=None, description="Watermark text (e.g., BOZZA)")

    # Footer
    footer_text: str | None = Field(default=None, description="Custom footer text")


class PDFGenerator:
    """PDF Generator for invoices.

    Example:
        >>> from openfatture.pdf import PDFGenerator, PDFGeneratorConfig
        >>> from openfatture.storage.database import get_session
        >>> from openfatture.storage.database.models import Fattura
        >>>
        >>> # Configure generator
        >>> config = PDFGeneratorConfig(
        ...     template="professional",
        ...     company_name="ACME S.r.l.",
        ...     company_vat="12345678901",
        ...     logo_path="./logo.png",
        ...     enable_qr_code=True,
        ... )
        >>>
        >>> # Create generator
        >>> generator = PDFGenerator(config)
        >>>
        >>> # Load invoice from DB
        >>> with get_session() as session:
        ...     fattura = session.query(Fattura).filter_by(id=123).first()
        ...     pdf_path = generator.generate(fattura, output_path="fattura_123.pdf")
        >>>
        >>> print(f"PDF generated: {pdf_path}")
    """

    def __init__(self, config: PDFGeneratorConfig | None = None):
        """Initialize PDF generator.

        Args:
            config: PDF generator configuration (uses defaults if None)
        """
        self.config = config or PDFGeneratorConfig()
        self.template = self._create_template()

        logger.info(
            "pdf_generator_initialized",
            template=self.config.template,
            enable_qr=self.config.enable_qr_code,
            enable_pdfa=self.config.enable_pdfa,
        )

    def _create_template(self) -> BaseTemplate:
        """Create template instance based on configuration.

        Returns:
            Template instance

        Raises:
            ValueError: If template name is invalid
        """
        template_name = self.config.template.lower()

        if template_name == "minimalist":
            return MinimalistTemplate()

        elif template_name == "professional":
            return ProfessionalTemplate(logo_path=self.config.logo_path)

        elif template_name == "branded":
            return BrandedTemplate(
                primary_color=self.config.primary_color,
                secondary_color=self.config.secondary_color,
                logo_path=self.config.logo_path,
                watermark_text=self.config.watermark_text,
            )

        else:
            raise ValueError(
                f"Invalid template: {template_name}. "
                f"Valid options: minimalist, professional, branded"
            )

    def generate(
        self,
        fattura: Any,  # Fattura model instance
        output_path: str | None = None,
    ) -> Path:
        """Generate PDF for invoice.

        Args:
            fattura: Fattura model instance (from database)
            output_path: Output file path (auto-generates if None)

        Returns:
            Path to generated PDF

        Example:
            >>> pdf_path = generator.generate(fattura, "fattura_001.pdf")
        """
        # Convert model to dict
        fattura_data = self._fattura_to_dict(fattura)

        # Auto-generate filename if not provided
        if output_path is None:
            output_path = f"fattura_{fattura.numero}_{fattura.anno}.pdf"

        output_file = Path(output_path)

        logger.info(
            "generating_pdf",
            fattura_id=fattura.id,
            numero=f"{fattura.numero}/{fattura.anno}",
            output_path=str(output_file),
        )

        # Create PDF
        canvas = Canvas(str(output_file), pagesize=A4)

        # Set PDF metadata
        canvas.setAuthor(self.config.company_name or "OpenFatture")
        canvas.setTitle(f"Fattura {fattura.numero}/{fattura.anno}")
        canvas.setSubject(f"Fattura per {fattura.cliente.denominazione}")
        canvas.setCreator("OpenFatture - AI-Powered Invoicing")

        # Draw invoice
        self._draw_invoice(canvas, fattura_data)

        # Save PDF
        canvas.save()

        logger.info(
            "pdf_generated_successfully",
            fattura_id=fattura.id,
            output_path=str(output_file),
            file_size=output_file.stat().st_size,
        )

        return output_file

    def _fattura_to_dict(self, fattura: Any) -> dict[str, Any]:
        """Convert Fattura model to dictionary for template rendering.

        Args:
            fattura: Fattura model instance

        Returns:
            Dictionary with invoice data
        """
        # Client data
        cliente_data = {
            "denominazione": fattura.cliente.denominazione,
            "partita_iva": fattura.cliente.partita_iva,
            "codice_fiscale": fattura.cliente.codice_fiscale,
            "indirizzo": fattura.cliente.indirizzo,
            "numero_civico": fattura.cliente.numero_civico,
            "cap": fattura.cliente.cap,
            "comune": fattura.cliente.comune,
            "provincia": fattura.cliente.provincia,
        }

        # Invoice lines
        righe_data = []
        for riga in fattura.righe:
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

        # Payment data (first payment)
        pagamento_data = None
        if fattura.pagamenti:
            pag = fattura.pagamenti[0]
            pagamento_data = {
                "modalita": pag.modalita,
                "data_scadenza": pag.data_scadenza,
                "iban": pag.iban,
                "bic_swift": pag.bic_swift,
                "importo": pag.importo,
            }

        return {
            "id": fattura.id,
            "numero": fattura.numero,
            "anno": fattura.anno,
            "data_emissione": fattura.data_emissione,
            "tipo_documento": fattura.tipo_documento.value,
            "imponibile": fattura.imponibile,
            "iva": fattura.iva,
            "totale": fattura.totale,
            "ritenuta_acconto": fattura.ritenuta_acconto or Decimal(0),
            "aliquota_ritenuta": fattura.aliquota_ritenuta or Decimal(0),
            "importo_bollo": fattura.importo_bollo or Decimal(0),
            "stato": fattura.stato.value,
            "note": fattura.note,
            "cliente": cliente_data,
            "righe": righe_data,
            "pagamento": pagamento_data,
        }

    def _draw_invoice(self, canvas: Canvas, fattura_data: dict[str, Any]) -> None:
        """Draw complete invoice on canvas.

        Args:
            canvas: ReportLab canvas
            fattura_data: Invoice data dictionary
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
            primary_color=self.template.get_primary_color(),
        )

        # Custom template elements
        y = self.template.draw_custom_elements(canvas, fattura_data, y)

        # Invoice info (number, date)
        y = self.template.draw_invoice_info(canvas, fattura_data, y)

        # Client info
        y = self.template.draw_client_info(canvas, fattura_data["cliente"], y)

        # Calculate space needed for summary, payment, notes (post-table content)
        # Reserve space to prevent negative box_y in summary
        summary_height = self._calculate_summary_height(fattura_data)
        payment_height = self._calculate_payment_height(fattura_data["pagamento"])
        notes_height = self._calculate_notes_height(fattura_data.get("note"))
        footer_height = 2 * cm  # Footer space at bottom

        # Total space needed after table (individual calcs already include margins)
        post_table_space = summary_height + payment_height + notes_height + footer_height

        # Available height for table (ensure summary won't get negative y)
        available_for_table = y - post_table_space

        # If not enough space for table + summary, start table on new page
        # Threshold: table header (~0.8cm) + 1 row (~1.5cm) + small margin = ~3cm
        if available_for_table < 3 * cm:
            # Start new page for table
            canvas.showPage()
            page_width, page_height = A4
            y = page_height - 2 * cm

            # Redraw header on new page
            y = draw_header(
                canvas,
                y,
                company_name=self.config.company_name or "OpenFatture",
                company_vat=self.config.company_vat,
                company_address=self.config.company_address,
                company_city=self.config.company_city,
                logo_path=self.config.logo_path,
                primary_color=self.template.get_primary_color(),
            )

            # Recalculate available space on fresh page
            available_for_table = y - post_table_space

        # Draw invoice table with available space
        y, remaining_tables = draw_invoice_table(
            canvas,
            y,
            fattura_data["righe"],
            primary_color=self.template.get_primary_color(),
            available_height=available_for_table,
        )

        # Handle remaining table portions on new pages
        page_num = 1
        while remaining_tables:
            page_num += 1
            canvas.showPage()

            # Draw footer for previous page
            draw_footer(
                canvas,
                page_number=page_num - 1,
                total_pages=page_num + len(remaining_tables),  # Estimate
                show_digital_signature_note=True,
                footer_text=self.config.footer_text,
            )

            # Reset Y for new page
            page_width, page_height = A4
            y = page_height - 2 * cm

            # Draw continued table
            next_table = remaining_tables[0]
            available_height = y - post_table_space
            table_width, table_height = next_table.wrap(17 * cm, available_height)

            if table_height <= available_height:
                # Table fits
                next_table.drawOn(canvas, 2 * cm, y - table_height)
                y = y - table_height - 0.5 * cm
                remaining_tables = remaining_tables[1:]
            else:
                # Still doesn't fit, split further
                split_tables = next_table.split(17 * cm, available_height)
                if split_tables:
                    first = split_tables[0]
                    first_width, first_height = first.wrap(17 * cm, available_height)
                    first.drawOn(canvas, 2 * cm, y - first_height)
                    y = y - first_height - 0.5 * cm
                    # Replace with remaining parts
                    remaining_tables = split_tables[1:] + remaining_tables[1:]  # type: ignore[operator]
                else:
                    # Can't split further, draw what we have
                    next_table.drawOn(canvas, 2 * cm, y - table_height)
                    y = y - table_height - 0.5 * cm
                    remaining_tables = remaining_tables[1:]

        # Draw footer for last table page
        draw_footer(
            canvas,
            page_number=page_num,
            total_pages=page_num,
            show_digital_signature_note=True,
            footer_text=self.config.footer_text,
        )

        # Summary (totals)
        y = self.template.draw_summary(canvas, fattura_data, y)

        # Payment info
        y = self.template.draw_payment_info(canvas, fattura_data["pagamento"], y)

        # QR Code (if enabled and payment data available)
        if self.config.enable_qr_code and fattura_data["pagamento"]:
            self._draw_payment_qr(canvas, fattura_data)

        # Notes
        y = self.template.draw_notes(canvas, fattura_data.get("note"), y)

    def _calculate_summary_height(self, fattura_data: dict[str, Any]) -> float:
        """Calculate height needed for summary box.

        Args:
            fattura_data: Invoice data

        Returns:
            Height in cm
        """
        from decimal import Decimal

        line_height = 0.6 * cm
        num_lines = 3  # Imponibile, IVA, Total

        # Add lines for optional fields
        if fattura_data.get("ritenuta_acconto", Decimal(0)) > 0:
            num_lines += 1
        if fattura_data.get("importo_bollo", Decimal(0)) > 0:
            num_lines += 1

        box_height = (num_lines * line_height) + 1.4 * cm
        # Add spacing before and after (reduced from 1.5cm total to 1.0cm)
        return box_height + 0.8 * cm + 0.2 * cm

    def _calculate_payment_height(self, pagamento_data: dict[str, Any] | None) -> float:
        """Calculate height needed for payment info section.

        Args:
            pagamento_data: Payment data

        Returns:
            Height in cm
        """
        if not pagamento_data:
            return 0

        # Title + spacing
        height = 0.8 * cm + 0.6 * cm

        # Method line
        height += 0.5 * cm

        # Optional lines
        if pagamento_data.get("data_scadenza"):
            height += 0.5 * cm
        if pagamento_data.get("iban"):
            height += 0.5 * cm
        if pagamento_data.get("bic_swift"):
            height += 0.5 * cm

        # Spacing after (reduced from 0.5cm since summary has spacing before)
        height += 0.3 * cm

        return height

    def _calculate_notes_height(self, note: str | None) -> float:
        """Calculate height needed for notes section.

        Args:
            note: Notes text

        Returns:
            Height in cm
        """
        if not note:
            return 0

        # Title + spacing
        height = 0.8 * cm + 0.5 * cm

        # Estimate lines (max 80 chars per line)
        words = note.split()
        lines_count = 1
        current_line_len = 0

        for word in words:
            if current_line_len + len(word) + 1 <= 80:
                current_line_len += len(word) + 1
            else:
                lines_count += 1
                current_line_len = len(word) + 1

        # Line height
        height += lines_count * 0.4 * cm

        # Spacing after
        height += 0.3 * cm

        return height

    def _draw_payment_qr(self, canvas: Canvas, fattura_data: dict[str, Any]) -> None:
        """Draw payment QR code.

        Args:
            canvas: ReportLab canvas
            fattura_data: Invoice data
        """
        pagamento = fattura_data["pagamento"]

        if not pagamento or not pagamento.get("iban"):
            return

        # Generate QR data
        if self.config.qr_code_type == "sepa":
            qr_data = generate_sepa_qr_data(
                beneficiary_name=self.config.company_name or "OpenFatture",
                iban=pagamento["iban"],
                amount=float(fattura_data["totale"]),
                reference=f"Fattura {fattura_data['numero']}/{fattura_data['anno']}",
                bic=pagamento.get("bic_swift"),
            )
        else:
            # pagoPa not yet implemented
            logger.warning("pagopa_qr_not_implemented")
            return

        # Draw QR code (bottom-right corner)
        draw_qr_code(
            canvas,
            x_position=15.5 * cm,
            y_position=2.5 * cm,
            data=qr_data,
            size=3 * cm,
        )

        # Label
        canvas.setFont("Helvetica", 8)
        canvas.drawString(15.5 * cm, 2 * cm, "Paga con QR Code")


def create_pdf_generator(template: str = "professional", **kwargs: Any) -> PDFGenerator:
    """Factory function to create PDF generator.

    Args:
        template: Template name (professional/minimalist/branded, default: professional)
        **kwargs: Additional configuration parameters

    Returns:
        PDFGenerator instance

    Example:
        >>> generator = create_pdf_generator(
        ...     template="professional", company_name="ACME S.r.l.", logo_path="./logo.png"
        ... )
    """
    config = PDFGeneratorConfig(template=template, **kwargs)
    return PDFGenerator(config)
