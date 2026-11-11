"""PDF Generator for OpenFatture invoices.

Enterprise-grade PDF generation with:
- Multiple templates (minimalist, professional, branded)
- PDF/A-3 compliance for legal archiving
- QR code support (pagoPa, SEPA)
- Automatic pagination
- Type-safe configuration
"""

import io
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas

from openfatture.billing.application.totals import amount_due, vat_summary
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
    company_cf: str | None = Field(default=None, description="Company codice fiscale")
    company_address: str | None = Field(default=None, description="Company address")
    company_city: str | None = Field(default=None, description="Company city")
    regime_fiscale: str | None = Field(default=None, description="Tax regime code (e.g., RF19)")
    logo_path: str | None = Field(default=None, description="Path to logo")

    # Colors (for branded template)
    primary_color: str = Field(default="#2C3E50", description="Primary color (hex)")
    secondary_color: str = Field(default="#95A5A6", description="Secondary color (hex)")

    # QR Code
    enable_qr_code: bool = Field(default=False, description="Enable QR code for payments")

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

        # First pass counts the pages for the "Pagina N di M" footers.
        dry_run = _FooterCanvas(
            io.BytesIO(), pagesize=A4, total_pages=0, footer_text=self.config.footer_text
        )
        self._draw_invoice(dry_run, fattura_data)
        canvas = _FooterCanvas(
            str(output_file),
            pagesize=A4,
            total_pages=dry_run.getPageNumber(),
            footer_text=self.config.footer_text,
        )

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
                    "natura": riga.natura,
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
                "giorni_scadenza": getattr(pag, "giorni_scadenza", 30),
                "iban": pag.iban,
                "bic_swift": pag.bic_swift,
                "importo": pag.importo,
            }

        cassa_data = [
            {
                "tipo_cassa": cassa.tipo_cassa,
                "al_cassa": cassa.al_cassa,
                "importo_contributo_cassa": cassa.importo_contributo_cassa,
                "imponibile_cassa": cassa.imponibile_cassa,
                "aliquota_iva": cassa.aliquota_iva,
                "natura": cassa.natura,
            }
            for cassa in fattura.cassa_previdenziale
        ]

        # Cedente data (from config)
        cedente_data = {
            "denominazione": self.config.company_name,
            "partita_iva": self.config.company_vat,
            "codice_fiscale": self.config.company_cf,
            "indirizzo": self.config.company_address,
            "citta": self.config.company_city,
            "regime_fiscale": self.config.regime_fiscale,
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
            "importo_da_pagare": amount_due(fattura.totale, fattura.ritenuta_acconto),
            "riepilogo": [
                {"aliquota_iva": aliquota, "natura": natura, "imponibile": imp, "imposta": tax}
                for (aliquota, natura), (imp, tax) in vat_summary(
                    fattura.righe, fattura.cassa_previdenziale
                ).items()
            ],
            "stato": fattura.stato.value,
            "note": fattura.note,
            "cedente": cedente_data,
            "cliente": cliente_data,
            "righe": righe_data,
            "pagamento": pagamento_data,
            "cassa_previdenziale": cassa_data,
        }

    def _draw_invoice(self, canvas: Canvas, fattura_data: dict[str, Any]) -> None:
        """Draw the invoice, breaking pages so no section crosses the footer."""
        top = A4[1] - 2 * cm
        y = draw_header(
            canvas,
            top,
            company_name=self.config.company_name or "OpenFatture",
            company_vat=self.config.company_vat,
            company_cf=self.config.company_cf,
            company_address=self.config.company_address,
            company_city=self.config.company_city,
            regime_fiscale=self.config.regime_fiscale,
            logo_path=self.config.logo_path,
            primary_color=self.template.get_primary_color(),
        )
        y = self.template.draw_custom_elements(canvas, fattura_data, y)
        y = self.template.draw_invoice_info(canvas, fattura_data, y)
        y = self.template.draw_client_info(canvas, fattura_data["cliente"], y)

        # Line items: split across pages as needed.
        if y - _CONTENT_BOTTOM < _MIN_TABLE_HEIGHT:
            canvas.showPage()
            y = top
        y, remaining = draw_invoice_table(
            canvas,
            y,
            fattura_data["righe"],
            primary_color=self.template.get_primary_color(),
            available_height=y - _CONTENT_BOTTOM,
        )
        while remaining:
            canvas.showPage()
            y = top
            table = remaining.pop(0)
            available = y - _CONTENT_BOTTOM
            _, height = table.wrap(17 * cm, available)
            if height > available:
                parts = table.split(17 * cm, available)
                table, remaining = parts[0], [*parts[1:], *remaining]
                _, height = table.wrap(17 * cm, available)
            table.drawOn(canvas, 2 * cm, y - height)
            y -= height + 0.5 * cm

        # Sections after the table, each kept whole on a page.
        sections: list[Callable[[Canvas, float], float]] = [
            lambda c, at: self.template.draw_dati_riepilogo(c, fattura_data, at),
            lambda c, at: self.template.draw_summary(c, fattura_data, at),
        ]
        if fattura_data.get("cassa_previdenziale"):
            sections.append(
                lambda c, at: self.template.draw_cassa_previdenziale(
                    c, fattura_data["cassa_previdenziale"], at
                )
            )
        sections.append(
            lambda c, at: self.template.draw_payment_info(c, fattura_data["pagamento"], at)
        )
        if self.config.enable_qr_code and (fattura_data["pagamento"] or {}).get("iban"):
            sections.append(lambda c, at: self._draw_payment_qr(c, fattura_data, at))
        sections.append(lambda c, at: self.template.draw_notes(c, fattura_data.get("note"), at))
        if fattura_data.get("importo_bollo", Decimal(0)) > 0:
            sections.append(
                lambda c, at: self.template.draw_bollo_footer(c, fattura_data["importo_bollo"], at)
            )

        for draw in sections:
            if y - _section_height(draw, y) < _CONTENT_BOTTOM:
                canvas.showPage()
                y = top
            y = draw(canvas, y)

    def _draw_payment_qr(self, canvas: Canvas, fattura_data: dict[str, Any], y: float) -> float:
        """Draw the SEPA credit transfer (EPC) QR for the amount the customer pays."""
        pagamento = fattura_data["pagamento"]
        qr_data = generate_sepa_qr_data(
            beneficiary_name=self.config.company_name or "OpenFatture",
            iban=pagamento["iban"],
            amount=float(fattura_data["importo_da_pagare"]),
            reference=f"Fattura {fattura_data['numero']}/{fattura_data['anno']}",
            bic=pagamento.get("bic_swift"),
        )
        size = 3 * cm
        draw_qr_code(canvas, x_position=15.5 * cm, y_position=y - size, data=qr_data, size=size)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(15.5 * cm, y - size - 0.4 * cm, "Paga con QR Code")
        return y - size - 0.8 * cm


# Footer area (page number, notes) below this line; content stays above it.
_CONTENT_BOTTOM = 2.0 * cm
_MIN_TABLE_HEIGHT = 3 * cm


def _section_height(draw: Callable[[Canvas, float], float], y: float) -> float:
    """Height a section takes, measured by drawing it on a scratch canvas."""
    return y - draw(Canvas(io.BytesIO(), pagesize=A4), y)


class _FooterCanvas(Canvas):
    """Canvas that draws the "Pagina N di M" footer on every page it ends."""

    def __init__(self, *args: Any, total_pages: int, footer_text: str | None, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._total_pages = total_pages
        self._footer_text = footer_text

    def showPage(self) -> None:
        draw_footer(
            self,
            page_number=self.getPageNumber(),
            total_pages=self._total_pages,
            show_digital_signature_note=True,
            footer_text=self._footer_text,
        )
        super().showPage()


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
