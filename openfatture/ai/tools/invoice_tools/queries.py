"""Invoice query tools — thin adapters over billing application services."""

from typing import Any

from pydantic import validate_call

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType, ToolRisk
from openfatture.billing.application import invoice_queries
from openfatture.storage.database.models import StatoFattura


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
            description=(
                "List invoices filtered by number or note text, year, status and client, newest "
                "first (year, then number, descending). Each result has id, numero, anno, data, "
                "cliente name, importo (total), stato, the payment summary (payment_status, "
                "amount_paid, outstanding) and the SDI status evidence (status_origin, "
                "submission_state); has_more is true when the limit was reached. It does not "
                "search by client name: resolve the client with search_clients and pass "
                "cliente_id. Use get_invoice_details for the lines of one invoice and "
                "get_invoice_stats for yearly counts and totals."
            ),
            category="invoices",
            parameters=[
                ToolParameter(
                    name="query",
                    type=ToolParameterType.STRING,
                    description="Text contained in the invoice number or notes; client names are not matched",
                    required=False,
                ),
                ToolParameter(
                    name="anno",
                    type=ToolParameterType.INTEGER,
                    description="Invoice year (4 digits, 2000-2100); omit for all years",
                    required=False,
                ),
                ToolParameter(
                    name="stato",
                    type=ToolParameterType.STRING,
                    description="Local invoice status; omit for any status",
                    required=False,
                    enum=[stato.value for stato in StatoFattura],
                ),
                ToolParameter(
                    name="cliente_id",
                    type=ToolParameterType.INTEGER,
                    description="Client ID (from search_clients); omit for all clients",
                    required=False,
                ),
                ToolParameter(
                    name="limit",
                    type=ToolParameterType.INTEGER,
                    description="Maximum number of invoices returned, 1-100; default 10",
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
            description=(
                "Return one invoice in full: numero, anno, data_emissione, cliente (id, "
                "denominazione, partita_iva), importi (imponibile, iva, totale), stato, notes, "
                "the lines (descrizione, quantita, prezzo_unitario, aliquota_iva), the payment "
                "records with due dates and the collected and outstanding amounts, and the SDI "
                "status evidence. Returns an error when the invoice does not exist. Use "
                "search_invoices to find the ID and check_invoice_sdi_status for the full SDI "
                "notification timeline."
            ),
            category="invoices",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID (the id field from search_invoices)",
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
            description=(
                "Return aggregate figures for the invoices of one year: totale_fatture, counts "
                "per_stato (local technical status) and per_documento (separating historical "
                "invoices issued elsewhere), importo_totale, incassato_totale, residuo_totale, "
                "counts per_stato_incasso, and invii_da_verificare (submissions still pending or "
                "uncertain). Read avvertenza_stato before drawing conclusions about SDI "
                "transmission. Use it instead of adding up search_invoices results; use "
                "generate_vat_report for VAT by rate or quarter."
            ),
            category="invoices",
            parameters=[
                ToolParameter(
                    name="anno",
                    type=ToolParameterType.INTEGER,
                    description="Invoice year (4 digits, 2000-2100); defaults to the current year",
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
