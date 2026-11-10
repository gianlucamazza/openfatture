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
            name="update_invoice",
            risk=ToolRisk.MUTATE,
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
            risk=ToolRisk.MUTATE,
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
            risk=ToolRisk.MUTATE,
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
    ]
