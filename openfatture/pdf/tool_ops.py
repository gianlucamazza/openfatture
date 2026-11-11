"""Tools for PDF generation (invoices, quotes).

Every PDF is a courtesy copy: the fiscal original is the FatturaPA XML sent
through SDI. Without an explicit ``output_path`` files go under
``<data_dir>/exports``, never into the current working directory.
"""

from pathlib import Path
from typing import Any

from pydantic import validate_call

from openfatture.pdf.generator import (
    DEFAULT_TEMPLATE,
    TEMPLATES,
    PDFGenerator,
    PDFGeneratorConfig,
)
from openfatture.pdf.preventivo_generator import PreventivoPDFGenerator
from openfatture.platform.config import Settings, get_settings
from openfatture.platform.errors import describe_error
from openfatture.platform.logging import get_logger
from openfatture.platform.security import validate_integer_input
from openfatture.storage.database.models import Fattura, Preventivo
from openfatture.storage.session import db_session

logger = get_logger(__name__)


def _company_config(settings: Settings, **overrides: Any) -> PDFGeneratorConfig:
    """PDF configuration with the cedente's data, plus per-document options."""
    values: dict[str, Any] = {
        "company_name": settings.cedente_denominazione,
        "company_vat": settings.cedente_partita_iva or settings.cedente_codice_fiscale,
        "company_cf": settings.cedente_codice_fiscale,
        "company_address": settings.cedente_indirizzo,
        "company_city": (
            f"{settings.cedente_cap} {settings.cedente_comune} ({settings.cedente_provincia})"
        ),
        "regime_fiscale": settings.cedente_regime_fiscale,
        "logo_path": settings.email_logo_url,
        "primary_color": settings.email_primary_color,
    }
    values.update({key: value for key, value in overrides.items() if value is not None})
    return PDFGeneratorConfig(**values)


def _default_output(settings: Settings, folder: str, name: str) -> str:
    """A path inside the exports directory, creating its folder."""
    directory = settings.exports_dir / folder
    directory.mkdir(parents=True, exist_ok=True)
    return str(directory / name)


def _written(pdf_path: Path) -> dict[str, Any]:
    return {
        "pdf_path": str(pdf_path.absolute()),
        "file_size": pdf_path.stat().st_size,
        "courtesy_copy": True,
        "message": f"PDF generato (copia di cortesia): {pdf_path.name}",
    }


# =============================================================================
# PDF Generation Tools
# =============================================================================


@validate_call
def generate_invoice_pdf(
    fattura_id: int,
    output_path: str | None = None,
    template: str | None = None,
    enable_qr_code: bool = False,
    watermark_text: str | None = None,
    logo_path: str | None = None,
) -> dict[str, Any]:
    """
    Generate the courtesy-copy PDF of an invoice.

    Args:
        fattura_id: Invoice ID to generate PDF for
        output_path: Output file path (default: exports/fatture/fattura_N_YYYY.pdf)
        template: Template name (minimalist/professional/branded; default professional)
        enable_qr_code: Enable SEPA QR code for payments (default: False)
        watermark_text: Optional watermark text (e.g., "BOZZA", "DRAFT")
        logo_path: Company logo overriding the configured one

    Returns:
        Dictionary with generation result and PDF path
    """
    fattura_id = validate_integer_input(fattura_id, min_value=1)
    template = template or DEFAULT_TEMPLATE
    if template not in TEMPLATES:
        return {
            "success": False,
            "error": f"Invalid template: {template}. Valid options: {', '.join(TEMPLATES)}",
        }

    with db_session() as db:
        try:
            fattura = db.query(Fattura).filter(Fattura.id == fattura_id).first()
            if not fattura:
                return {"success": False, "error": f"Fattura {fattura_id} not found"}

            settings = get_settings()
            config = _company_config(
                settings,
                template=template,
                logo_path=logo_path,
                enable_qr_code=enable_qr_code,
                enable_pdfa=True,
                watermark_text=watermark_text,
            )
            target = output_path or _default_output(
                settings, "fatture", f"fattura_{fattura.numero}_{fattura.anno}.pdf"
            )
            pdf_path = PDFGenerator(config).generate(fattura, output_path=target)

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
                "issued_elsewhere": bool(fattura.issued_elsewhere),
                "template": template,
                **_written(pdf_path),
            }

        except Exception as e:
            logger.error("generate_invoice_pdf_failed", fattura_id=fattura_id, error=str(e))
            return {"success": False, "error": describe_error(e)}


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
        output_path: Output file path (default: exports/preventivi/preventivo_N_YYYY.pdf)
        watermark_text: Optional watermark text (default: "BOZZA" for draft quotes)

    Returns:
        Dictionary with generation result and PDF path
    """
    preventivo_id = validate_integer_input(preventivo_id, min_value=1)

    with db_session() as db:
        try:
            preventivo = db.query(Preventivo).filter(Preventivo.id == preventivo_id).first()
            if not preventivo:
                return {"success": False, "error": f"Preventivo {preventivo_id} not found"}

            settings = get_settings()
            if preventivo.stato.value == "bozza" and not watermark_text:
                watermark_text = "BOZZA"

            config = _company_config(settings, watermark_text=watermark_text)
            target = output_path or _default_output(
                settings, "preventivi", f"preventivo_{preventivo.numero}_{preventivo.anno}.pdf"
            )
            pdf_path = PreventivoPDFGenerator(config).generate(preventivo, output_path=target)

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
                "stato": preventivo.stato.value,
                "has_watermark": bool(watermark_text),
                **_written(pdf_path),
            }

        except Exception as e:
            logger.error(
                "generate_preventivo_pdf_failed", preventivo_id=preventivo_id, error=str(e)
            )
            return {"success": False, "error": describe_error(e)}


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
            "courtesy_copy_note": (
                "Il PDF è una copia di cortesia: l'originale fiscale è l'XML trasmesso via SDI."
            ),
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
                "default_template": DEFAULT_TEMPLATE,
                "has_logo": bool(settings.email_logo_url),
                "primary_color": settings.email_primary_color,
                "secondary_color": "#95A5A6",
            },
            "qr_code_options": {
                "types": ["sepa"],
                "description": "SEPA credit transfer (EPC) QR code for the amount due",
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
        return {"error": describe_error(e)}
