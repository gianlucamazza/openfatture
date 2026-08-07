"""Invoice query tools — thin adapters over billing application services."""

from typing import Any

from pydantic import validate_call

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
