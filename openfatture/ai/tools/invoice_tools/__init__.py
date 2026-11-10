"""Tools for invoice operations (thin adapters).

Domain logic lives in application services:

- reads: ``billing.application.invoice_queries``
- writes: ``billing.application.invoice_commands``
- SDI: ``sdi.application.invoice_sdi_ops``

Public tool functions re-export those use-cases for the ToolRegistry.
"""

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
from openfatture.billing.application.cassa_ops import set_cassa_previdenziale

from .invoices import (
    create_invoice,
    delete_invoice,
    update_invoice,
    update_invoice_status,
)
from .line_helpers import (
    create_course_line,
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
    "create_course_line",
    "format_course_description",
    "update_riga",
    "delete_riga",
    "validate_invoice_xml",
    "send_invoice_to_sdi",
    "update_invoice",
    "delete_invoice",
    "update_invoice_status",
    "set_cassa_previdenziale",
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
                    description=(
                        "VAT rate percentage; omit for the cedente default "
                        "(0% with natura N2.2 in the forfettario regime, else 22%)"
                    ),
                    required=False,
                ),
                ToolParameter(
                    name="unita_misura",
                    type=ToolParameterType.STRING,
                    description="Unit of measure (default 'ore')",
                    required=False,
                    default="ore",
                ),
                ToolParameter(
                    name="natura",
                    type=ToolParameterType.STRING,
                    description=(
                        "VAT natura, only with a 0% rate: N2.2 forfettario (default), "
                        "N1 for the stamp duty charged to the customer, N4 exempt, ..."
                    ),
                    required=False,
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
                    name="natura",
                    type=ToolParameterType.STRING,
                    description="VAT natura, only with a 0% rate (e.g. N2.2, N1, N4)",
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
            enabled=False,
            examples=[
                "send_invoice_to_sdi(fattura_id=123)",
                "send_invoice_to_sdi(fattura_id=123, signed=True)",
            ],
            tags=["write", "send", "critical", "transmit"],
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
        Tool(
            name="set_cassa_previdenziale",
            description=(
                "Set or remove the invoice's social security contribution (rivalsa, "
                "DatiCassaPrevidenziale), e.g. INPS gestione separata TC22 at 4%. "
                "The amount is computed on the lines (excluding N1) and added to the totals."
            ),
            category="invoices",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID",
                    required=True,
                ),
                ToolParameter(
                    name="tipo_cassa",
                    type=ToolParameterType.STRING,
                    description="TC01..TC22 (TC22 = INPS gestione separata); omit to remove",
                    required=False,
                ),
                ToolParameter(
                    name="al_cassa",
                    type=ToolParameterType.NUMBER,
                    description="Contribution rate percentage (e.g. 4)",
                    required=False,
                    default=0,
                ),
                ToolParameter(
                    name="aliquota_iva",
                    type=ToolParameterType.NUMBER,
                    description="VAT rate on the contribution; omit for the cedente default",
                    required=False,
                ),
                ToolParameter(
                    name="natura",
                    type=ToolParameterType.STRING,
                    description="VAT natura of the contribution with a 0% rate (default N2.2 for forfettario)",
                    required=False,
                ),
            ],
            func=set_cassa_previdenziale,
            requires_confirmation=True,
            examples=[
                "set_cassa_previdenziale(fattura_id=12, tipo_cassa='TC22', al_cassa=4)",
                "set_cassa_previdenziale(fattura_id=12)",
            ],
            tags=["write", "update"],
        ),
        # Line helper tools
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
                    description="VAT rate percentage; omit for the cedente default",
                    required=False,
                ),
                ToolParameter(
                    name="natura",
                    type=ToolParameterType.STRING,
                    description="VAT natura, only with a 0% rate (default N2.2 for forfettario)",
                    required=False,
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
