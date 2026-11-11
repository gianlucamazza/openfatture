"""Invoice write tools — adapters over billing.application.invoice_commands."""

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType, ToolRisk
from openfatture.billing.application.invoice_commands import (
    create_invoice,
    delete_invoice,
    update_invoice,
    update_invoice_status,
)

__all__ = [
    "create_invoice",
    "update_invoice",
    "delete_invoice",
    "update_invoice_status",
]


def tools() -> list[Tool]:
    """Assistant tool definitions for invoice writes."""
    return [
        Tool(
            name="create_invoice",
            risk=ToolRisk.MUTATE,
            description=(
                "Create an empty invoice in BOZZA status for an existing client, with zero "
                "totals. Returns invoice_id, numero, anno, cliente and stato; add the lines "
                "with create_riga (or create_course_line) afterwards, since totals are computed "
                "from them. Fails when the client does not exist, the number is already used in "
                "that year (the error names the next free number), or the date is not ISO. For a "
                "credit note of an existing invoice use create_nota_credito_from_fattura; to "
                "invoice an accepted quote use convert_preventivo_to_invoice."
            ),
            category="invoices",
            parameters=[
                ToolParameter(
                    name="cliente_id",
                    type=ToolParameterType.INTEGER,
                    description="Client ID (from search_clients)",
                    required=True,
                ),
                ToolParameter(
                    name="anno",
                    type=ToolParameterType.INTEGER,
                    description="Invoice year (4 digits, 2000-2100); defaults to the current year",
                    required=False,
                ),
                ToolParameter(
                    name="numero",
                    type=ToolParameterType.STRING,
                    description="Invoice number as text, unique within the year; omit to take the next progressive number",
                    required=False,
                ),
                ToolParameter(
                    name="data_emissione",
                    type=ToolParameterType.STRING,
                    description="Issue date in ISO format YYYY-MM-DD; defaults to today",
                    required=False,
                ),
                ToolParameter(
                    name="tipo_documento",
                    type=ToolParameterType.STRING,
                    description="FatturaPA document type: TD01 invoice (default), TD04 credit note, TD06 parcella",
                    required=False,
                    enum=["TD01", "TD04", "TD06"],
                    default="TD01",
                ),
                ToolParameter(
                    name="note",
                    type=ToolParameterType.STRING,
                    description="Free-text notes stored on the invoice",
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
            name="update_invoice",
            risk=ToolRisk.MUTATE,
            description=(
                "Change the issue date, document type or notes of an invoice in BOZZA status; "
                "only the fields passed are changed. Returns invoice_id, numero and the list of "
                "changed fields. Fails when the invoice is not found, is not BOZZA, no field is "
                "given, or the date is not ISO. Number, year and client cannot be changed; lines "
                "are edited with update_riga and the status with update_invoice_status."
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
                    name="data_emissione",
                    type=ToolParameterType.STRING,
                    description="New issue date in ISO format YYYY-MM-DD; omit to keep it",
                    required=False,
                ),
                ToolParameter(
                    name="tipo_documento",
                    type=ToolParameterType.STRING,
                    description="New FatturaPA document type (TD01 invoice, TD04 credit note, TD06 parcella); omit to keep it",
                    required=False,
                    enum=["TD01", "TD04", "TD06"],
                ),
                ToolParameter(
                    name="note",
                    type=ToolParameterType.STRING,
                    description="New notes, replacing the current ones; omit to keep them",
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
            risk=ToolRisk.MUTATE,
            description=(
                "Delete an invoice in BOZZA status from the database together with its lines. "
                "Irreversible. Returns invoice_id, numero, cliente and righe_deleted. Fails when "
                "the invoice is not found or is not BOZZA; an invoice with lines is refused "
                "(the error reports righe_count) unless force is true. An invoice already sent "
                "is never deleted: correct it with create_nota_credito_from_fattura."
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
                    name="force",
                    type=ToolParameterType.BOOLEAN,
                    description="Also delete the invoice when it has lines; default false refuses it",
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
            risk=ToolRisk.MUTATE,
            description=(
                "Move an invoice between bozza and da_inviare, the only manual status change; "
                "later statuses come from SDI receipts. Moving to da_inviare requires a client "
                "and at least one line and validates the FatturaPA XML against the schema, "
                "returning the validation error when it fails. Returns old_status and "
                "new_status (unchanged status succeeds without changes). Refused for invoices "
                "issued elsewhere and for invoices already past da_inviare; error_code "
                "state_conflict means the invoice changed meanwhile and must be reloaded."
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
                    name="new_status",
                    type=ToolParameterType.STRING,
                    description="Target status: da_inviare (ready to send) or bozza (back to draft)",
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
    ]
