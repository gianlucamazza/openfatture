"""AI tool adapters over `openfatture.pdf.tool_ops`."""

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType, ToolRisk
from openfatture.ai.tools.output_paths import confined_output
from openfatture.pdf.generator import DEFAULT_TEMPLATE, TEMPLATES
from openfatture.pdf.tool_ops import (
    generate_invoice_pdf,
    generate_invoice_summary_pdf,
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
            risk=ToolRisk.LOCAL_ARTIFACT,
            description=(
                "Generate the courtesy-copy PDF of an invoice, including invoices issued "
                "elsewhere, as PDF/A with the configured company data. The fiscal original "
                "remains the FatturaPA XML (generate_invoice_xml). Writes "
                "fatture/fattura_<numero>_<anno>.pdf in the exports directory unless "
                "output_path is given, overwriting an existing file. Returns success, "
                "fattura_id, numero, template, issued_elsewhere, pdf_path (absolute), "
                "file_size and courtesy_copy. Errors: invoice not found, invalid template, "
                "output_path outside the exports directory."
            ),
            category="pdf",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID (fattura_id)",
                    required=True,
                ),
                ToolParameter(
                    name="output_path",
                    type=ToolParameterType.STRING,
                    description=(
                        "PDF path relative to the exports directory (an absolute path must "
                        "be inside it); the default file name when omitted"
                    ),
                    required=False,
                ),
                ToolParameter(
                    name="template",
                    type=ToolParameterType.STRING,
                    description=(
                        "Layout: minimalist (plain), professional (with logo, the default) "
                        "or branded (logo, configured colours and watermark)"
                    ),
                    required=False,
                    default=DEFAULT_TEMPLATE,
                    enum=list(TEMPLATES),
                ),
                ToolParameter(
                    name="enable_qr_code",
                    type=ToolParameterType.BOOLEAN,
                    description="Print a SEPA credit-transfer (EPC) QR code for the amount due (default false)",
                    required=False,
                    default=False,
                ),
                ToolParameter(
                    name="watermark_text",
                    type=ToolParameterType.STRING,
                    description=(
                        "Text printed diagonally across each page, such as BOZZA; drawn "
                        "only with the branded template, ignored by the others"
                    ),
                    required=False,
                ),
            ],
            func=confined_output(generate_invoice_pdf),
            examples=[
                "generate_invoice_pdf(fattura_id=123)",
                "generate_invoice_pdf(fattura_id=456, template='professional', enable_qr_code=True)",
                "generate_invoice_pdf(fattura_id=789, template='branded', watermark_text=\"DRAFT\")",
            ],
            tags=["pdf", "invoice", "generate", "document"],
        ),
        Tool(
            name="generate_preventivo_pdf",
            risk=ToolRisk.LOCAL_ARTIFACT,
            description=(
                "Generate the PDF of a preventivo (quote) with the configured company data. "
                "A quote in bozza status gets the BOZZA watermark unless watermark_text is "
                "given. Writes preventivi/preventivo_<numero>_<anno>.pdf in the exports "
                "directory unless output_path is given, overwriting an existing file. "
                "Returns success, preventivo_id, numero, stato, has_watermark, pdf_path "
                "(absolute) and file_size. Errors: quote not found, output_path outside the "
                "exports directory."
            ),
            category="pdf",
            parameters=[
                ToolParameter(
                    name="preventivo_id",
                    type=ToolParameterType.INTEGER,
                    description="Quote ID (preventivo_id)",
                    required=True,
                ),
                ToolParameter(
                    name="output_path",
                    type=ToolParameterType.STRING,
                    description=(
                        "PDF path relative to the exports directory (an absolute path must "
                        "be inside it); the default file name when omitted"
                    ),
                    required=False,
                ),
                ToolParameter(
                    name="watermark_text",
                    type=ToolParameterType.STRING,
                    description="Watermark text; defaults to BOZZA for draft quotes and to none otherwise",
                    required=False,
                ),
            ],
            func=confined_output(generate_preventivo_pdf),
            examples=[
                "generate_preventivo_pdf(preventivo_id=10)",
                'generate_preventivo_pdf(preventivo_id=20, watermark_text="CONFIDENTIAL")',
            ],
            tags=["pdf", "preventivo", "quote", "generate", "document"],
        ),
        Tool(
            name="generate_invoice_summary_pdf",
            risk=ToolRisk.LOCAL_ARTIFACT,
            description=(
                "Generate a PDF summary of one year's invoice situation: every document with "
                "its SDI and payment status, totals and the share of each client. Local "
                "drafts are excluded; credit notes (TD04) reduce net_invoiced and carry no "
                "collection. Writes riepiloghi/riepilogo_fatture_<anno>.pdf in the exports "
                "directory unless output_path is given, overwriting an existing file. "
                "Returns success, anno, documents_count, totals (invoiced, credit_notes, "
                "net_invoiced, collected, outstanding, overdue, unscheduled), pdf_path and "
                "file_size, so it also answers questions about collected and outstanding "
                "amounts. For VAT totals use generate_vat_report; for due dates use "
                "get_due_dates."
            ),
            category="pdf",
            parameters=[
                ToolParameter(
                    name="anno",
                    type=ToolParameterType.INTEGER,
                    description="Invoice year, 2000-2100; the current year when omitted",
                    required=False,
                ),
                ToolParameter(
                    name="output_path",
                    type=ToolParameterType.STRING,
                    description=(
                        "PDF path relative to the exports directory (an absolute path must "
                        "be inside it); the default file name when omitted"
                    ),
                    required=False,
                ),
            ],
            func=confined_output(generate_invoice_summary_pdf),
            examples=[
                "generate_invoice_summary_pdf()",
                "generate_invoice_summary_pdf(anno=2025)",
            ],
            tags=["pdf", "report", "summary", "riepilogo", "situazione"],
        ),
        Tool(
            name="get_pdf_configuration",
            risk=ToolRisk.READ,
            description=(
                "Describe the PDF options: the available templates with their features, "
                "the current company data printed on PDFs (name, VAT number, address), the "
                "default template, whether a logo and which primary colour are configured, "
                "and the QR-code and watermark options. Read-only; use it to choose "
                "arguments for generate_invoice_pdf or to check the company data before "
                "generating."
            ),
            category="pdf",
            parameters=[],
            func=get_pdf_configuration,
            examples=["get_pdf_configuration()"],
            tags=["pdf", "config", "templates", "info"],
        ),
    ]
