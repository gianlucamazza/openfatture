"""Tools for invoice operations."""

from typing import Any, TypedDict

from pydantic import validate_call
from sqlalchemy.orm import selectinload

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
from openfatture.storage.database.base import get_session
from openfatture.storage.database.models import Fattura, StatoFattura
from openfatture.utils.logging import get_logger
from openfatture.utils.security import sanitize_sql_like_input, validate_integer_input

logger = get_logger(__name__)


class InvoiceStats(TypedDict):
    anno: int
    totale_fatture: int
    per_stato: dict[str, int]
    importo_totale: float


# =============================================================================
# Invoice Query Tools
# =============================================================================


@validate_call
def search_invoices(
    query: str | None = None,
    anno: int | None = None,
    stato: str | None = None,
    cliente_id: int | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    # Sanitize and validate inputs
    if query is not None:
        query = sanitize_sql_like_input(query)

    if anno is not None:
        anno = validate_integer_input(anno, min_value=2000, max_value=2100)

    if cliente_id is not None:
        cliente_id = validate_integer_input(cliente_id, min_value=1)

    limit = validate_integer_input(limit, min_value=1, max_value=100)
    """
    Search for invoices matching criteria.

    Args:
        query: Search in invoice number or notes
        anno: Filter by year
        stato: Filter by status
        cliente_id: Filter by client ID
        limit: Maximum results

    Returns:
        Dictionary with search results
    """
    db = get_session()
    try:
        # Build query with eager loading to avoid N+1 queries
        db_query = db.query(Fattura).options(selectinload(Fattura.cliente))

        if query:
            db_query = db_query.filter(
                (Fattura.numero.contains(query)) | (Fattura.note.contains(query))
            )

        if anno:
            db_query = db_query.filter(Fattura.anno == anno)

        if stato:
            try:
                stato_enum = StatoFattura(stato)
                db_query = db_query.filter(Fattura.stato == stato_enum)
            except ValueError:
                pass  # Invalid status, ignore

        if cliente_id:
            db_query = db_query.filter(Fattura.cliente_id == cliente_id)

        # Order by most recent
        db_query = db_query.order_by(Fattura.anno.desc(), Fattura.numero.desc())

        # Get results
        fatture = db_query.limit(limit).all()

        # Format results
        results = []
        for f in fatture:
            # Skip if cliente is None
            if f.cliente is None:
                continue

            results.append(
                {
                    "id": f.id,
                    "numero": f.numero,
                    "anno": f.anno,
                    "data": f.data_emissione.isoformat(),
                    "cliente": f.cliente.denominazione,
                    "importo": float(f.totale),
                    "stato": f.stato.value,
                }
            )

        return {
            "count": len(results),
            "fatture": results,
            "has_more": len(fatture) == limit,
        }

    except Exception as e:
        logger.error("search_invoices_failed", error=str(e))
        return {"error": str(e), "count": 0, "fatture": []}

    finally:
        db.close()


@validate_call
def get_invoice_details(fattura_id: int) -> dict[str, Any]:
    # Validate input
    fattura_id = validate_integer_input(fattura_id, min_value=1)
    """
    Get detailed information about an invoice.

    Args:
        fattura_id: Invoice ID

    Returns:
        Dictionary with invoice details
    """
    db = get_session()
    try:
        # Use selectinload to avoid N+1 queries when accessing relationships
        fattura = (
            db.query(Fattura)
            .options(selectinload(Fattura.cliente), selectinload(Fattura.righe))
            .filter(Fattura.id == fattura_id)
            .first()
        )

        if fattura is None:
            return {"error": f"Fattura {fattura_id} non trovata"}

        if fattura.cliente is None:
            return {"error": f"Fattura {fattura_id} has no associated cliente"}

        # Format details
        details = {
            "id": fattura.id,
            "numero": fattura.numero,
            "anno": fattura.anno,
            "data_emissione": fattura.data_emissione.isoformat(),
            "cliente": {
                "id": fattura.cliente.id,
                "denominazione": fattura.cliente.denominazione,
                "partita_iva": fattura.cliente.partita_iva,
            },
            "importi": {
                "imponibile": float(fattura.imponibile),
                "iva": float(fattura.iva),
                "totale": float(fattura.totale),
            },
            "stato": fattura.stato.value,
            "note": fattura.note or "",
            "righe_count": len(fattura.righe),
        }

        # Add lines if present
        if fattura.righe:
            details["righe"] = [
                {
                    "descrizione": r.descrizione,
                    "quantita": float(r.quantita),
                    "prezzo_unitario": float(r.prezzo_unitario),
                    "aliquota_iva": float(r.aliquota_iva),
                }
                for r in fattura.righe
            ]

        return details

    except Exception as e:
        logger.error("get_invoice_details_failed", fattura_id=fattura_id, error=str(e))
        return {"error": str(e)}

    finally:
        db.close()


@validate_call
def get_invoice_stats(anno: int | None = None) -> dict[str, Any]:
    """
    Get statistics about invoices.

    Args:
        anno: Filter by year (current year if None)

    Returns:
        Dictionary with stats
    """
    # Validate input after parameter validation
    if anno is not None:
        anno = validate_integer_input(anno, min_value=2000, max_value=2100)
    from datetime import datetime

    db = get_session()
    try:
        year = anno or datetime.now().year

        # Count by status
        per_stato: dict[str, int] = {}
        stats: InvoiceStats = {
            "anno": year,
            "totale_fatture": 0,
            "per_stato": per_stato,
            "importo_totale": 0.0,
        }

        for stato in StatoFattura:
            count = db.query(Fattura).filter(Fattura.anno == year, Fattura.stato == stato).count()
            per_stato[stato.value] = count
            stats["totale_fatture"] += count

        # Total amount
        fatture = db.query(Fattura).filter(Fattura.anno == year).all()
        stats["importo_totale"] = sum(float(f.totale) for f in fatture)

        return dict(stats)

    except Exception as e:
        logger.error("get_invoice_stats_failed", error=str(e))
        return {"error": str(e)}

    finally:
        db.close()


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
    ]
