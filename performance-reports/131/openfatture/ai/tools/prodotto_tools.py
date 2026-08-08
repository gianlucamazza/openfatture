"""AI tool adapters over `openfatture.billing.application.prodotto_ops`."""

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
from openfatture.billing.application.prodotto_ops import (
    create_prodotto,
    delete_prodotto,
    get_prodotto_details,
    search_prodotti,
    update_prodotto,
)


def get_prodotto_tools() -> list[Tool]:
    """
    Get all product/service catalog tools.

    Returns:
        List of Tool instances
    """
    return [
        Tool(
            name="search_prodotti",
            description="Search products/services in catalog with optional filters (category, type, code, description)",
            category="prodotti",
            parameters=[
                ToolParameter(
                    name="categoria",
                    type=ToolParameterType.STRING,
                    description="Filter by category",
                    required=False,
                ),
                ToolParameter(
                    name="is_servizio",
                    type=ToolParameterType.BOOLEAN,
                    description="Filter by type (True=service, False=product)",
                    required=False,
                ),
                ToolParameter(
                    name="codice_contains",
                    type=ToolParameterType.STRING,
                    description="Filter by product code (partial match)",
                    required=False,
                ),
                ToolParameter(
                    name="descrizione_contains",
                    type=ToolParameterType.STRING,
                    description="Filter by description (partial match)",
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
            func=search_prodotti,
            examples=[
                "search_prodotti()",
                "search_prodotti(categoria='Consulting', is_servizio=True)",
                "search_prodotti(codice_contains='WEB', limit=10)",
            ],
            tags=["search", "prodotto", "catalog"],
        ),
        Tool(
            name="get_prodotto_details",
            description="Get detailed information about a specific product/service including usage statistics",
            category="prodotti",
            parameters=[
                ToolParameter(
                    name="prodotto_id",
                    type=ToolParameterType.INTEGER,
                    description="Product ID",
                    required=True,
                ),
            ],
            func=get_prodotto_details,
            examples=["get_prodotto_details(prodotto_id=1)"],
            tags=["prodotto", "details", "catalog"],
        ),
        Tool(
            name="create_prodotto",
            description="Create a new product/service in catalog with pricing and VAT information",
            category="prodotti",
            parameters=[
                ToolParameter(
                    name="codice",
                    type=ToolParameterType.STRING,
                    description="Unique product code (max 50 chars)",
                    required=True,
                ),
                ToolParameter(
                    name="descrizione",
                    type=ToolParameterType.STRING,
                    description="Product description (max 500 chars)",
                    required=True,
                ),
                ToolParameter(
                    name="prezzo_unitario",
                    type=ToolParameterType.NUMBER,
                    description="Unit price (must be positive)",
                    required=True,
                ),
                ToolParameter(
                    name="aliquota_iva",
                    type=ToolParameterType.NUMBER,
                    description="VAT rate (default 22%)",
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
                ToolParameter(
                    name="categoria",
                    type=ToolParameterType.STRING,
                    description="Optional category",
                    required=False,
                ),
                ToolParameter(
                    name="is_servizio",
                    type=ToolParameterType.BOOLEAN,
                    description="True for service, False for product (default True)",
                    required=False,
                    default=True,
                ),
                ToolParameter(
                    name="note",
                    type=ToolParameterType.STRING,
                    description="Optional notes",
                    required=False,
                ),
            ],
            func=create_prodotto,
            requires_confirmation=True,
            examples=[
                'create_prodotto(codice="WEB-CONS", descrizione="Web consulting hourly rate", prezzo_unitario=80.0)',
                'create_prodotto(codice="GDPR-AUD", descrizione="GDPR audit service", prezzo_unitario=150.0, categoria="Compliance", aliquota_iva=22.0)',
            ],
            tags=["create", "prodotto", "catalog", "write"],
        ),
        Tool(
            name="update_prodotto",
            description="Update product/service information (selective field updates)",
            category="prodotti",
            parameters=[
                ToolParameter(
                    name="prodotto_id",
                    type=ToolParameterType.INTEGER,
                    description="Product ID to update",
                    required=True,
                ),
                ToolParameter(
                    name="descrizione",
                    type=ToolParameterType.STRING,
                    description="New description",
                    required=False,
                ),
                ToolParameter(
                    name="prezzo_unitario",
                    type=ToolParameterType.NUMBER,
                    description="New unit price",
                    required=False,
                ),
                ToolParameter(
                    name="aliquota_iva",
                    type=ToolParameterType.NUMBER,
                    description="New VAT rate",
                    required=False,
                ),
                ToolParameter(
                    name="unita_misura",
                    type=ToolParameterType.STRING,
                    description="New unit of measure",
                    required=False,
                ),
                ToolParameter(
                    name="categoria",
                    type=ToolParameterType.STRING,
                    description="New category",
                    required=False,
                ),
                ToolParameter(
                    name="is_servizio",
                    type=ToolParameterType.BOOLEAN,
                    description="New product type",
                    required=False,
                ),
                ToolParameter(
                    name="note",
                    type=ToolParameterType.STRING,
                    description="New notes",
                    required=False,
                ),
            ],
            func=update_prodotto,
            requires_confirmation=True,
            examples=[
                "update_prodotto(prodotto_id=1, prezzo_unitario=90.0)",
                'update_prodotto(prodotto_id=2, descrizione="Updated description", categoria="New Category")',
            ],
            tags=["update", "prodotto", "catalog", "write"],
        ),
        Tool(
            name="delete_prodotto",
            description="CRITICAL: Delete product/service from catalog (irreversible operation)",
            category="prodotti",
            parameters=[
                ToolParameter(
                    name="prodotto_id",
                    type=ToolParameterType.INTEGER,
                    description="Product ID to delete",
                    required=True,
                ),
                ToolParameter(
                    name="force",
                    type=ToolParameterType.BOOLEAN,
                    description="Force deletion even if used in invoices (default False)",
                    required=False,
                    default=False,
                ),
            ],
            func=delete_prodotto,
            requires_confirmation=True,
            examples=[
                "delete_prodotto(prodotto_id=5)",
                "delete_prodotto(prodotto_id=10, force=True)",
            ],
            tags=["delete", "prodotto", "catalog", "write", "critical"],
        ),
    ]
