"""AI tool adapters over `openfatture.billing.application.preventivo_ops`."""

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
from openfatture.billing.application.preventivo_ops import (
    convert_preventivo_to_invoice,
    create_preventivo,
    delete_preventivo,
    get_preventivo_details,
    search_preventivi,
    update_preventivo,
    update_preventivo_status,
)


def get_preventivo_tools() -> list[Tool]:
    """
    Get all preventivo-related tools.

    Returns:
        List of Tool instances
    """
    return [
        Tool(
            name="search_preventivi",
            description="Search preventivi (quotes) with optional filters (status, client, year)",
            category="preventivi",
            parameters=[
                ToolParameter(
                    name="stato",
                    type=ToolParameterType.STRING,
                    description="Filter by status",
                    required=False,
                    enum=["bozza", "inviato", "accettato", "rifiutato", "scaduto", "convertito"],
                ),
                ToolParameter(
                    name="cliente_id",
                    type=ToolParameterType.INTEGER,
                    description="Filter by client ID",
                    required=False,
                ),
                ToolParameter(
                    name="anno",
                    type=ToolParameterType.INTEGER,
                    description="Filter by year",
                    required=False,
                ),
                ToolParameter(
                    name="limit",
                    type=ToolParameterType.INTEGER,
                    description="Maximum results (default 20)",
                    required=False,
                    default=20,
                ),
            ],
            func=search_preventivi,
            examples=[
                "search_preventivi()",
                "search_preventivi(stato='inviato', anno=2025)",
                "search_preventivi(cliente_id=5, limit=10)",
            ],
            tags=["search", "preventivo", "quote"],
        ),
        Tool(
            name="get_preventivo_details",
            description="Get detailed information about a specific preventivo including line items",
            category="preventivi",
            parameters=[
                ToolParameter(
                    name="preventivo_id",
                    type=ToolParameterType.INTEGER,
                    description="Preventivo ID",
                    required=True,
                ),
            ],
            func=get_preventivo_details,
            examples=["get_preventivo_details(preventivo_id=123)"],
            tags=["preventivo", "details", "quote"],
        ),
        Tool(
            name="create_preventivo",
            description="Create a new preventivo (quote/estimate) with line items",
            category="preventivi",
            parameters=[
                ToolParameter(
                    name="cliente_id",
                    type=ToolParameterType.INTEGER,
                    description="Client ID",
                    required=True,
                ),
                ToolParameter(
                    name="righe",
                    type=ToolParameterType.ARRAY,
                    description="List of line items (each with descrizione, quantita, prezzo_unitario, aliquota_iva, unita_misura)",
                    required=True,
                    items={
                        "type": "object",
                        "properties": {
                            "descrizione": {
                                "type": "string",
                                "description": "Line item description",
                            },
                            "quantita": {
                                "type": "number",
                                "description": "Quantity",
                            },
                            "prezzo_unitario": {
                                "type": "number",
                                "description": "Unit price",
                            },
                            "aliquota_iva": {
                                "type": "number",
                                "description": "VAT rate percentage (default 22.0)",
                            },
                            "unita_misura": {
                                "type": "string",
                                "description": "Unit of measure (default 'ore')",
                            },
                        },
                        "required": ["descrizione", "quantita", "prezzo_unitario"],
                    },
                ),
                ToolParameter(
                    name="validita_giorni",
                    type=ToolParameterType.INTEGER,
                    description="Validity period in days (default 30)",
                    required=False,
                    default=30,
                ),
                ToolParameter(
                    name="note",
                    type=ToolParameterType.STRING,
                    description="Optional notes",
                    required=False,
                ),
                ToolParameter(
                    name="condizioni",
                    type=ToolParameterType.STRING,
                    description="Optional terms and conditions",
                    required=False,
                ),
            ],
            func=create_preventivo,
            requires_confirmation=True,
            examples=[
                """create_preventivo(
                cliente_id=5,
                righe=[{"descrizione": "Web consulting", "quantita": 8, "prezzo_unitario": 80, "aliquota_iva": 22}],
                validita_giorni=30
            )"""
            ],
            tags=["create", "preventivo", "quote", "write"],
        ),
        Tool(
            name="update_preventivo_status",
            description="Update preventivo status (bozza, inviato, accettato, rifiutato, scaduto)",
            category="preventivi",
            parameters=[
                ToolParameter(
                    name="preventivo_id",
                    type=ToolParameterType.INTEGER,
                    description="Preventivo ID",
                    required=True,
                ),
                ToolParameter(
                    name="new_status",
                    type=ToolParameterType.STRING,
                    description="New status",
                    required=True,
                    enum=["bozza", "inviato", "accettato", "rifiutato", "scaduto"],
                ),
            ],
            func=update_preventivo_status,
            requires_confirmation=True,
            examples=[
                "update_preventivo_status(preventivo_id=123, new_status='inviato')",
                "update_preventivo_status(preventivo_id=456, new_status='accettato')",
            ],
            tags=["update", "preventivo", "status", "write"],
        ),
        Tool(
            name="update_preventivo",
            description="Update preventivo fields (note, condizioni, validita_giorni). Only BOZZA status can be edited.",
            category="preventivi",
            parameters=[
                ToolParameter(
                    name="preventivo_id",
                    type=ToolParameterType.INTEGER,
                    description="Preventivo ID",
                    required=True,
                ),
                ToolParameter(
                    name="note",
                    type=ToolParameterType.STRING,
                    description="Notes",
                    required=False,
                ),
                ToolParameter(
                    name="condizioni",
                    type=ToolParameterType.STRING,
                    description="Terms and conditions",
                    required=False,
                ),
                ToolParameter(
                    name="validita_giorni",
                    type=ToolParameterType.INTEGER,
                    description="Validity period in days (updates data_scadenza)",
                    required=False,
                ),
            ],
            func=update_preventivo,
            requires_confirmation=True,
            examples=[
                "update_preventivo(preventivo_id=123, note='Updated notes')",
                "update_preventivo(preventivo_id=456, validita_giorni=45)",
            ],
            tags=["update", "preventivo", "write"],
        ),
        Tool(
            name="delete_preventivo",
            description="CRITICAL: Delete preventivo from database. Only BOZZA status and non-converted preventivi can be deleted.",
            category="preventivi",
            parameters=[
                ToolParameter(
                    name="preventivo_id",
                    type=ToolParameterType.INTEGER,
                    description="Preventivo ID to delete",
                    required=True,
                ),
            ],
            func=delete_preventivo,
            requires_confirmation=True,
            examples=["delete_preventivo(preventivo_id=123)"],
            tags=["delete", "preventivo", "write", "critical"],
        ),
        Tool(
            name="convert_preventivo_to_invoice",
            description="CRITICAL: Convert preventivo to fattura (cannot be undone). Creates new invoice from quote.",
            category="preventivi",
            parameters=[
                ToolParameter(
                    name="preventivo_id",
                    type=ToolParameterType.INTEGER,
                    description="Preventivo ID to convert",
                    required=True,
                ),
            ],
            func=convert_preventivo_to_invoice,
            requires_confirmation=True,
            examples=["convert_preventivo_to_invoice(preventivo_id=123)"],
            tags=["convert", "preventivo", "invoice", "write", "critical"],
        ),
    ]
