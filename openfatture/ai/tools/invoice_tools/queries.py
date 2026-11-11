"""Invoice query tools — thin adapters over billing application services."""

from typing import Any

from pydantic import validate_call

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType, ToolRisk
from openfatture.billing.application import invoice_queries


@validate_call
def search_invoices(
    query: str | None = None,
    anno: int | None = None,
    stato: str | None = None,
    cliente_id: int | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Search for invoices matching criteria."""
    return invoice_queries.search_invoices(
        query=query,
        anno=anno,
        stato=stato,
        cliente_id=cliente_id,
        limit=limit,
    )


@validate_call
def get_invoice_details(fattura_id: int) -> dict[str, Any]:
    """Get detailed information about an invoice."""
    return invoice_queries.get_invoice_details(fattura_id)


@validate_call
def get_invoice_stats(anno: int | None = None) -> dict[str, Any]:
    """Get statistics about invoices."""
    return invoice_queries.get_invoice_stats(anno)


def tools() -> list[Tool]:
    """Assistant tool definitions for invoice queries."""
    return [
        Tool(
            name="search_invoices",
            risk=ToolRisk.READ,
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
            risk=ToolRisk.READ,
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
            risk=ToolRisk.READ,
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
    ]
