"""AI tool adapters over `openfatture.pdf.tool_ops`."""

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
from openfatture.pdf.tool_ops import (
    generate_invoice_pdf,
    generate_preventivo_pdf,
    get_pdf_configuration,
)


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
