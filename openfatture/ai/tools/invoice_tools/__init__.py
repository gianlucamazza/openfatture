"""Tools for invoice operations (thin adapters).

Domain logic lives in application services:

- reads: ``billing.application.invoice_queries``
- writes: ``billing.application.invoice_commands``
- SDI: ``sdi.application.invoice_sdi_ops``

Public tool functions re-export those use-cases for the ToolRegistry.
"""

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType

from .invoices import (
    create_invoice,
    delete_invoice,
    update_invoice,
    update_invoice_status,
)
from .line_helpers import (
    create_course_line,
    create_lump_line,
    create_rate_line,
    format_course_description,
)
from .nota_credito import (
    create_nota_credito_from_fattura,
)
from .queries import (
    get_invoice_details,
    get_invoice_stats,
    search_invoices,
)
from .righe import (
    create_riga,
    delete_riga,
    update_riga,
)
from .sdi import (
    send_invoice_to_sdi,
    validate_invoice_xml,
)

__all__ = [
    "search_invoices",
    "get_invoice_details",
    "get_invoice_stats",
    "create_invoice",
    "create_nota_credito_from_fattura",
    "create_riga",
    "create_lump_line",
    "create_rate_line",
    "create_course_line",
    "format_course_description",
    "update_riga",
    "delete_riga",
    "validate_invoice_xml",
    "send_invoice_to_sdi",
    "update_invoice",
    "delete_invoice",
    "update_invoice_status",
    "get_invoice_tools",
]


# =============================================================================
# Tool Definitions
# =============================================================================


def get_invoice_tools() -> list[Tool]:
    """
    Get all invoice-related tools.

    Returns:
        List of Tool instances
    """
    return [
        Tool(
            name="search_invoices",
            description="Search for invoices by number, year, status, or client",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="query",
                    type=ToolParameterType.STRING,
                    description="Search query (numero or note)",
                    required=False,
                ),
                ToolParameter(
                    name="anno",
                    type=ToolParameterType.INTEGER,
                    description="Filter by year (e.g., 2025)",
                    required=False,
                ),
                ToolParameter(
                    name="stato",
                    type=ToolParameterType.STRING,
                    description="Filter by status",
                    required=False,
                    enum=["bozza", "da_inviare", "inviata", "accettata", "rifiutata"],
                ),
                ToolParameter(
                    name="cliente_id",
                    type=ToolParameterType.INTEGER,
                    description="Filter by client ID",
                    required=False,
                ),
                ToolParameter(
                    name="limit",
                    type=ToolParameterType.INTEGER,
                    description="Maximum number of results",
                    required=False,
                    default=10,
                ),
            ],
            func=search_invoices,
            examples=[
                "search_invoices(anno=2025)",
                "search_invoices(stato='da_inviare', limit=5)",
                "search_invoices(query='consulenza')",
            ],
            tags=["search", "query"],
        ),
        Tool(
            name="get_invoice_details",
            description="Get detailed information about a specific invoice",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID",
                    required=True,
                ),
            ],
            func=get_invoice_details,
            examples=["get_invoice_details(fattura_id=123)"],
            tags=["details", "view"],
        ),
        Tool(
            name="get_invoice_stats",
            description="Get statistics about invoices (count, totals by status)",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="anno",
                    type=ToolParameterType.INTEGER,
                    description="Year for statistics (current year if not specified)",
                    required=False,
                ),
            ],
            func=get_invoice_stats,
            examples=[
                "get_invoice_stats()",
                "get_invoice_stats(anno=2024)",
            ],
            tags=["stats", "analytics"],
        ),
        # WRITE tools
        Tool(
            name="create_invoice",
            description="Create a new invoice for a client. Returns invoice_id to add line items.",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="cliente_id",
                    type=ToolParameterType.INTEGER,
                    description="Client ID (required)",
                    required=True,
                ),
                ToolParameter(
                    name="anno",
                    type=ToolParameterType.INTEGER,
                    description="Year (current year if not specified)",
                    required=False,
                ),
                ToolParameter(
                    name="numero",
                    type=ToolParameterType.STRING,
                    description="Invoice number (auto-generated if not specified)",
                    required=False,
                ),
                ToolParameter(
                    name="data_emissione",
                    type=ToolParameterType.STRING,
                    description="Issue date YYYY-MM-DD (today if not specified)",
                    required=False,
                ),
                ToolParameter(
                    name="tipo_documento",
                    type=ToolParameterType.STRING,
                    description="Document type (default TD01 - Fattura)",
                    required=False,
                    enum=["TD01", "TD04", "TD06"],
                    default="TD01",
                ),
                ToolParameter(
                    name="note",
                    type=ToolParameterType.STRING,
                    description="Optional notes",
                    required=False,
                ),
            ],
            func=create_invoice,
            requires_confirmation=True,
            examples=[
                "create_invoice(cliente_id=1)",
                "create_invoice(cliente_id=5, note='Q1 2025 consulting')",
            ],
            tags=["write", "create"],
        ),
        Tool(
            name="create_riga",
            description="Add line item to invoice. Updates invoice totals automatically.",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID",
                    required=True,
                ),
                ToolParameter(
                    name="descrizione",
                    type=ToolParameterType.STRING,
                    description="Item description",
                    required=True,
                ),
                ToolParameter(
                    name="quantita",
                    type=ToolParameterType.NUMBER,
                    description="Quantity",
                    required=True,
                ),
                ToolParameter(
                    name="prezzo_unitario",
                    type=ToolParameterType.NUMBER,
                    description="Unit price in euros",
                    required=True,
                ),
                ToolParameter(
                    name="aliquota_iva",
                    type=ToolParameterType.NUMBER,
                    description="VAT rate percentage (default 22%)",
                    required=False,
                    default=22.0,
                ),
                ToolParameter(
                    name="unita_misura",
                    type=ToolParameterType.STRING,
                    description="Unit of measure (default 'ore')",
                    required=False,
                    default="ore",
                ),
            ],
            func=create_riga,
            requires_confirmation=True,
            examples=[
                "create_riga(fattura_id=123, descrizione='Web consulting', quantita=3, prezzo_unitario=150)",
                "create_riga(fattura_id=123, descrizione='Backend dev', quantita=8, prezzo_unitario=100, aliquota_iva=22)",
            ],
            tags=["write", "create"],
        ),
        Tool(
            name="update_riga",
            description="Update line item in invoice (only BOZZA or DA_INVIARE). Updates invoice totals automatically.",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="riga_id",
                    type=ToolParameterType.INTEGER,
                    description="Line item ID",
                    required=True,
                ),
                ToolParameter(
                    name="descrizione",
                    type=ToolParameterType.STRING,
                    description="Item description",
                    required=False,
                ),
                ToolParameter(
                    name="quantita",
                    type=ToolParameterType.NUMBER,
                    description="Quantity",
                    required=False,
                ),
                ToolParameter(
                    name="prezzo_unitario",
                    type=ToolParameterType.NUMBER,
                    description="Unit price in euros",
                    required=False,
                ),
                ToolParameter(
                    name="aliquota_iva",
                    type=ToolParameterType.NUMBER,
                    description="VAT rate percentage",
                    required=False,
                ),
                ToolParameter(
                    name="unita_misura",
                    type=ToolParameterType.STRING,
                    description="Unit of measure",
                    required=False,
                ),
            ],
            func=update_riga,
            requires_confirmation=True,
            examples=[
                "update_riga(riga_id=5, quantita=5)",
                "update_riga(riga_id=10, descrizione='Updated consulting', prezzo_unitario=200)",
            ],
            tags=["write", "update"],
        ),
        Tool(
            name="delete_riga",
            description="CRITICAL: Delete line item from invoice (only BOZZA or DA_INVIARE). Updates invoice totals automatically.",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="riga_id",
                    type=ToolParameterType.INTEGER,
                    description="Line item ID to delete",
                    required=True,
                ),
            ],
            func=delete_riga,
            requires_confirmation=True,
            examples=["delete_riga(riga_id=5)"],
            tags=["write", "delete", "critical"],
        ),
        Tool(
            name="validate_invoice_xml",
            description="Validate FatturaPA XML for invoice before sending to SDI",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID",
                    required=True,
                ),
            ],
            func=validate_invoice_xml,
            examples=["validate_invoice_xml(fattura_id=123)"],
            tags=["validation", "xml"],
        ),
        Tool(
            name="send_invoice_to_sdi",
            description="Send invoice to SDI via PEC. CRITICAL: Cannot be undone!",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID",
                    required=True,
                ),
                ToolParameter(
                    name="signed",
                    type=ToolParameterType.BOOLEAN,
                    description="Whether XML is digitally signed (default False)",
                    required=False,
                    default=False,
                ),
            ],
            func=send_invoice_to_sdi,
            requires_confirmation=True,
            examples=[
                "send_invoice_to_sdi(fattura_id=123)",
                "send_invoice_to_sdi(fattura_id=123, signed=True)",
            ],
            tags=["write", "send", "critical"],
        ),
        Tool(
            name="update_invoice",
            description="Update invoice information (only BOZZA status). Modify date, document type, or notes.",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID to update",
                    required=True,
                ),
                ToolParameter(
                    name="data_emissione",
                    type=ToolParameterType.STRING,
                    description="New issue date YYYY-MM-DD (optional)",
                    required=False,
                ),
                ToolParameter(
                    name="tipo_documento",
                    type=ToolParameterType.STRING,
                    description="New document type (optional)",
                    required=False,
                    enum=["TD01", "TD04", "TD06"],
                ),
                ToolParameter(
                    name="note",
                    type=ToolParameterType.STRING,
                    description="New notes (optional)",
                    required=False,
                ),
            ],
            func=update_invoice,
            requires_confirmation=True,
            examples=[
                "update_invoice(fattura_id=123, note='Updated description')",
                "update_invoice(fattura_id=456, data_emissione='2025-01-15', tipo_documento='TD01')",
            ],
            tags=["write", "update"],
        ),
        Tool(
            name="delete_invoice",
            description="CRITICAL: Delete invoice from database (only BOZZA status). Irreversible operation!",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID to delete",
                    required=True,
                ),
                ToolParameter(
                    name="force",
                    type=ToolParameterType.BOOLEAN,
                    description="Force deletion even if invoice has line items (default False)",
                    required=False,
                    default=False,
                ),
            ],
            func=delete_invoice,
            requires_confirmation=True,
            examples=[
                "delete_invoice(fattura_id=999)",
                "delete_invoice(fattura_id=999, force=True)",
            ],
            tags=["write", "delete", "critical"],
        ),
        Tool(
            name="update_invoice_status",
            description="Update invoice status (workflow: BOZZA DA_INVIARE). Validates invoice completeness.",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID",
                    required=True,
                ),
                ToolParameter(
                    name="new_status",
                    type=ToolParameterType.STRING,
                    description="New status (bozza or da_inviare)",
                    required=True,
                    enum=["bozza", "da_inviare"],
                ),
            ],
            func=update_invoice_status,
            requires_confirmation=True,
            examples=[
                "update_invoice_status(fattura_id=123, new_status='da_inviare')",
                "update_invoice_status(fattura_id=456, new_status='bozza')",
            ],
            tags=["write", "status", "workflow"],
        ),
        Tool(
            name="create_nota_credito_from_fattura",
            description="Create a nota di credito (TD04 credit note) from an existing invoice. Links to source invoice with FatturaPA DatiFattureCollegate. Supports full or partial refund.",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Source invoice ID to create credit note from",
                    required=True,
                ),
                ToolParameter(
                    name="note",
                    type=ToolParameterType.STRING,
                    description="Optional notes for the credit note",
                    required=False,
                ),
                ToolParameter(
                    name="full_refund",
                    type=ToolParameterType.BOOLEAN,
                    description="If True, copies all lines from source; if False, use line_items for partial refund (default True)",
                    required=False,
                    default=True,
                ),
            ],
            func=create_nota_credito_from_fattura,
            requires_confirmation=True,
            examples=[
                "create_nota_credito_from_fattura(fattura_id=123, note='Storno completo')",
                "create_nota_credito_from_fattura(fattura_id=456, full_refund=False, note='Storno parziale')",
            ],
            tags=["write", "create", "credit_note", "storno"],
        ),
        # Line helper tools
        Tool(
            name="create_lump_line",
            description="Create a lump-sum line item (1 × imponibile). Suitable for services or project-based fees.",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID",
                    required=True,
                ),
                ToolParameter(
                    name="descrizione",
                    type=ToolParameterType.STRING,
                    description="Item description",
                    required=True,
                ),
                ToolParameter(
                    name="imponibile",
                    type=ToolParameterType.NUMBER,
                    description="Total taxable amount in euros",
                    required=True,
                ),
                ToolParameter(
                    name="aliquota_iva",
                    type=ToolParameterType.NUMBER,
                    description="VAT rate percentage (default 22%)",
                    required=False,
                    default=22.0,
                ),
                ToolParameter(
                    name="unita_misura",
                    type=ToolParameterType.STRING,
                    description="Unit of measure (default 'servizio')",
                    required=False,
                    default="servizio",
                ),
            ],
            func=create_lump_line,
            requires_confirmation=True,
            examples=[
                "create_lump_line(fattura_id=123, descrizione='Consulting project', imponibile=1500.00)",
                "create_lump_line(fattura_id=456, descrizione='Course fee', imponibile=960.00, aliquota_iva=0.0)",
            ],
            tags=["write", "create", "line"],
        ),
        Tool(
            name="create_rate_line",
            description="Create a rate-based line item (quantità × prezzo_unitario). Suitable for hourly work or goods.",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID",
                    required=True,
                ),
                ToolParameter(
                    name="descrizione",
                    type=ToolParameterType.STRING,
                    description="Item description",
                    required=True,
                ),
                ToolParameter(
                    name="quantita",
                    type=ToolParameterType.NUMBER,
                    description="Quantity",
                    required=True,
                ),
                ToolParameter(
                    name="prezzo_unitario",
                    type=ToolParameterType.NUMBER,
                    description="Unit price in euros",
                    required=True,
                ),
                ToolParameter(
                    name="aliquota_iva",
                    type=ToolParameterType.NUMBER,
                    description="VAT rate percentage (default 22%)",
                    required=False,
                    default=22.0,
                ),
                ToolParameter(
                    name="unita_misura",
                    type=ToolParameterType.STRING,
                    description="Unit of measure (default 'ore')",
                    required=False,
                    default="ore",
                ),
            ],
            func=create_rate_line,
            requires_confirmation=True,
            examples=[
                "create_rate_line(fattura_id=123, descrizione='Web development', quantita=8, prezzo_unitario=100.00)",
                "create_rate_line(fattura_id=456, descrizione='Consulting hours', quantita=3.5, prezzo_unitario=150.00, aliquota_iva=22.0)",
            ],
            tags=["write", "create", "line"],
        ),
        Tool(
            name="create_course_line",
            description="Create a lump-sum line for a course with formatted FT-style description (title, dates, location).",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID",
                    required=True,
                ),
                ToolParameter(
                    name="course_title",
                    type=ToolParameterType.STRING,
                    description="Course title",
                    required=True,
                ),
                ToolParameter(
                    name="imponibile",
                    type=ToolParameterType.NUMBER,
                    description="Total course fee in euros",
                    required=True,
                ),
                ToolParameter(
                    name="start_date",
                    type=ToolParameterType.STRING,
                    description="Course start date (DD.MM.YYYY)",
                    required=True,
                ),
                ToolParameter(
                    name="end_date",
                    type=ToolParameterType.STRING,
                    description="Course end date (DD.MM.YYYY, optional)",
                    required=False,
                ),
                ToolParameter(
                    name="location",
                    type=ToolParameterType.STRING,
                    description="Course location (optional)",
                    required=False,
                ),
                ToolParameter(
                    name="additional_notes",
                    type=ToolParameterType.STRING,
                    description="Additional notes (optional)",
                    required=False,
                ),
                ToolParameter(
                    name="aliquota_iva",
                    type=ToolParameterType.NUMBER,
                    description="VAT rate percentage (default 0% for courses)",
                    required=False,
                    default=0.0,
                ),
            ],
            func=create_course_line,
            requires_confirmation=True,
            examples=[
                "create_course_line(fattura_id=123, course_title='Corso RES', imponibile=960.00, start_date='09.09.2026', end_date='10.09.2026', location='Limolane 12/Roma')",
                "create_course_line(fattura_id=456, course_title='Training session', imponibile=500.00, start_date='15.01.2026')",
            ],
            tags=["write", "create", "line", "course"],
        ),
    ]
