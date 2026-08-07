"""Tools for PDF generation (invoices, quotes)."""

from typing import Any

from pydantic import validate_call

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
from openfatture.services.pdf.generator import PDFGenerator, PDFGeneratorConfig
from openfatture.services.pdf.preventivo_generator import PreventivoPDFGenerator
from openfatture.storage.database.base import get_session
from openfatture.storage.database.models import Fattura, Preventivo
from openfatture.utils.config import get_settings
from openfatture.utils.logging import get_logger
from openfatture.utils.security import validate_integer_input

logger = get_logger(__name__)


# =============================================================================
# PDF Generation Tools
# =============================================================================


@validate_call
def generate_invoice_pdf(
    fattura_id: int,
    output_path: str | None = None,
    template: str = "minimalist",
    enable_qr_code: bool = False,
    watermark_text: str | None = None,
) -> dict[str, Any]:
    """
    Generate PDF for an invoice.

    Args:
        fattura_id: Invoice ID to generate PDF for
        output_path: Output file path (auto-generates if None)
        template: Template name (minimalist/professional/branded, default: minimalist)
        enable_qr_code: Enable SEPA QR code for payments (default: False)
        watermark_text: Optional watermark text (e.g., "BOZZA", "DRAFT")

    Returns:
        Dictionary with generation result and PDF path
    """
    # Validate input
    fattura_id = validate_integer_input(fattura_id, min_value=1)

    # Validate template
    valid_templates = ["minimalist", "professional", "branded"]
    if template not in valid_templates:
        return {
            "success": False,
            "error": f"Invalid template: {template}. Valid options: {', '.join(valid_templates)}",
        }

    db = get_session()
    try:
        # Get invoice
        fattura = db.query(Fattura).filter(Fattura.id == fattura_id).first()

        if not fattura:
            return {"success": False, "error": f"Fattura {fattura_id} not found"}

        # Load settings for company info
        settings = get_settings()

        # Create PDF configuration
        config = PDFGeneratorConfig(
            template=template,
            company_name=settings.cedente_denominazione,
            company_vat=settings.cedente_partita_iva or settings.cedente_codice_fiscale,
            company_address=settings.cedente_indirizzo,
            company_city=f"{settings.cedente_cap} {settings.cedente_comune} ({settings.cedente_provincia})",
            logo_path=settings.email_logo_url if hasattr(settings, "email_logo_url") else None,
            primary_color=(
                settings.email_primary_color
                if hasattr(settings, "email_primary_color")
                else "#2C3E50"
            ),
            enable_qr_code=enable_qr_code,
            qr_code_type="sepa",
            enable_pdfa=True,
            watermark_text=watermark_text,
        )

        # Create generator
        generator = PDFGenerator(config)

        # Generate PDF
        pdf_path = generator.generate(fattura, output_path=output_path)

        logger.info(
            "invoice_pdf_generated",
            fattura_id=fattura_id,
            numero=f"{fattura.numero}/{fattura.anno}",
            pdf_path=str(pdf_path),
            template=template,
        )

        return {
            "success": True,
            "fattura_id": fattura_id,
            "numero": f"{fattura.numero}/{fattura.anno}",
            "pdf_path": str(pdf_path.absolute()),
            "file_size": pdf_path.stat().st_size,
            "template": template,
            "message": f"PDF generato: {pdf_path.name}",
        }

    except Exception as e:
        logger.error("generate_invoice_pdf_failed", fattura_id=fattura_id, error=str(e))
        return {"success": False, "error": str(e)}
    finally:
        db.close()


@validate_call
def generate_preventivo_pdf(
    preventivo_id: int,
    output_path: str | None = None,
    watermark_text: str | None = None,
) -> dict[str, Any]:
    """
    Generate PDF for a preventivo (quote/estimate).

    Args:
        preventivo_id: Preventivo ID to generate PDF for
        output_path: Output file path (auto-generates if None)
        watermark_text: Optional watermark text (default: "BOZZA" for draft quotes)

    Returns:
        Dictionary with generation result and PDF path
    """
    # Validate input
    preventivo_id = validate_integer_input(preventivo_id, min_value=1)

    db = get_session()
    try:
        # Get preventivo
        preventivo = db.query(Preventivo).filter(Preventivo.id == preventivo_id).first()

        if not preventivo:
            return {"success": False, "error": f"Preventivo {preventivo_id} not found"}

        # Load settings for company info
        settings = get_settings()

        # Auto-watermark for draft quotes
        if preventivo.stato.value == "bozza" and not watermark_text:
            watermark_text = "BOZZA"

        # Create PDF configuration
        config = PDFGeneratorConfig(
            company_name=settings.cedente_denominazione,
            company_vat=settings.cedente_partita_iva or settings.cedente_codice_fiscale,
            company_address=settings.cedente_indirizzo,
            company_city=f"{settings.cedente_cap} {settings.cedente_comune} ({settings.cedente_provincia})",
            logo_path=settings.email_logo_url if hasattr(settings, "email_logo_url") else None,
            primary_color=(
                settings.email_primary_color
                if hasattr(settings, "email_primary_color")
                else "#2C3E50"
            ),
            watermark_text=watermark_text,
            footer_text="Questo preventivo non costituisce fattura",
        )

        # Create generator
        generator = PreventivoPDFGenerator(config)

        # Generate PDF
        pdf_path = generator.generate(preventivo, output_path=output_path)

        logger.info(
            "preventivo_pdf_generated",
            preventivo_id=preventivo_id,
            numero=f"{preventivo.numero}/{preventivo.anno}",
            pdf_path=str(pdf_path),
            stato=preventivo.stato.value,
        )

        return {
            "success": True,
            "preventivo_id": preventivo_id,
            "numero": f"{preventivo.numero}/{preventivo.anno}",
            "pdf_path": str(pdf_path.absolute()),
            "file_size": pdf_path.stat().st_size,
            "stato": preventivo.stato.value,
            "has_watermark": bool(watermark_text),
            "message": f"PDF generato: {pdf_path.name}",
        }

    except Exception as e:
        logger.error("generate_preventivo_pdf_failed", preventivo_id=preventivo_id, error=str(e))
        return {"success": False, "error": str(e)}
    finally:
        db.close()


@validate_call
def get_pdf_configuration() -> dict[str, Any]:
    """
    Get available PDF configuration options and current defaults.

    Returns:
        Dictionary with available templates, colors, and configuration options
    """
    try:
        # Load settings
        settings = get_settings()

        return {
            "available_templates": [
                {
                    "name": "minimalist",
                    "description": "Clean and simple design with minimal branding",
                    "features": ["Basic header", "Simple table", "Standard footer"],
                },
                {
                    "name": "professional",
                    "description": "Professional design with logo and custom styling",
                    "features": ["Logo support", "Custom colors", "Enhanced layout"],
                },
                {
                    "name": "branded",
                    "description": "Fully branded design with company colors and watermark",
                    "features": [
                        "Logo support",
                        "Custom colors",
                        "Watermark support",
                        "Enhanced branding",
                    ],
                },
            ],
            "current_defaults": {
                "company_name": settings.cedente_denominazione,
                "company_vat": settings.cedente_partita_iva or settings.cedente_codice_fiscale,
                "company_address": settings.cedente_indirizzo,
                "company_city": f"{settings.cedente_cap} {settings.cedente_comune} ({settings.cedente_provincia})",
                "has_logo": hasattr(settings, "email_logo_url") and settings.email_logo_url,
                "primary_color": getattr(settings, "email_primary_color", "#2C3E50"),
                "secondary_color": "#95A5A6",
            },
            "qr_code_options": {
                "types": ["sepa", "pagopa"],
                "description": "QR code for instant payment (SEPA or PagoPa)",
                "supported": True,
            },
            "pdf_features": {
                "pdf_a_compliance": "PDF/A-3 compliant for legal archiving",
                "automatic_pagination": "Multi-page support for long invoices",
                "watermark_support": "Add watermark text (e.g., BOZZA, DRAFT)",
                "qr_code_payments": "SEPA instant payment QR codes",
            },
            "customization_tips": [
                "Use 'professional' template for logo and custom colors",
                "Use 'branded' template for watermarks and full branding",
                "Enable QR codes for faster payments",
                "Add watermark_text='BOZZA' for draft invoices",
            ],
        }

    except Exception as e:
        logger.error("get_pdf_configuration_failed", error=str(e))
        return {"error": str(e)}


# =============================================================================
# Tool Definitions
# =============================================================================


def get_pdf_tools() -> list[Tool]:
    """
    Get all PDF generation tools.

    Returns:
        List of Tool instances
    """
    return [
        Tool(
            name="generate_invoice_pdf",
            description="Generate PDF for an invoice with customizable template and options",
            category="pdf",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID to generate PDF for",
                    required=True,
                ),
                ToolParameter(
                    name="output_path",
                    type=ToolParameterType.STRING,
                    description="Output file path (auto-generates if None)",
                    required=False,
                ),
                ToolParameter(
                    name="template",
                    type=ToolParameterType.STRING,
                    description="Template name (minimalist/professional/branded)",
                    required=False,
                    default="minimalist",
                    enum=["minimalist", "professional", "branded"],
                ),
                ToolParameter(
                    name="enable_qr_code",
                    type=ToolParameterType.BOOLEAN,
                    description="Enable SEPA QR code for payments",
                    required=False,
                    default=False,
                ),
                ToolParameter(
                    name="watermark_text",
                    type=ToolParameterType.STRING,
                    description="Optional watermark text (e.g., BOZZA, DRAFT)",
                    required=False,
                ),
            ],
            func=generate_invoice_pdf,
            examples=[
                "generate_invoice_pdf(fattura_id=123)",
                "generate_invoice_pdf(fattura_id=456, template='professional', enable_qr_code=True)",
                "generate_invoice_pdf(fattura_id=789, template='branded', watermark_text=\"DRAFT\")",
            ],
            tags=["pdf", "invoice", "generate", "document"],
        ),
        Tool(
            name="generate_preventivo_pdf",
            description="Generate PDF for a preventivo (quote/estimate) with auto-watermark for drafts",
            category="pdf",
            parameters=[
                ToolParameter(
                    name="preventivo_id",
                    type=ToolParameterType.INTEGER,
                    description="Preventivo ID to generate PDF for",
                    required=True,
                ),
                ToolParameter(
                    name="output_path",
                    type=ToolParameterType.STRING,
                    description="Output file path (auto-generates if None)",
                    required=False,
                ),
                ToolParameter(
                    name="watermark_text",
                    type=ToolParameterType.STRING,
                    description="Optional watermark text (default: BOZZA for drafts)",
                    required=False,
                ),
            ],
            func=generate_preventivo_pdf,
            examples=[
                "generate_preventivo_pdf(preventivo_id=10)",
                'generate_preventivo_pdf(preventivo_id=20, watermark_text="CONFIDENTIAL")',
            ],
            tags=["pdf", "preventivo", "quote", "generate", "document"],
        ),
        Tool(
            name="get_pdf_configuration",
            description="Get available PDF templates, configuration options, and current defaults",
            category="pdf",
            parameters=[],
            func=get_pdf_configuration,
            examples=["get_pdf_configuration()"],
            tags=["pdf", "config", "templates", "info"],
        ),
    ]
