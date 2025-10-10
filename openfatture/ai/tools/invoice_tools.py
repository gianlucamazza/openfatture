"""Tools for invoice operations."""

from typing import Any

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
from openfatture.storage.database.base import SessionLocal
from openfatture.storage.database.models import Fattura, StatoFattura
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# Invoice Query Tools
# =============================================================================


def search_invoices(
    query: str | None = None,
    anno: int | None = None,
    stato: str | None = None,
    cliente_id: int | None = None,
    limit: int = 10,
) -> dict[str, Any]:
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
    db = SessionLocal()
    try:
        # Build query
        db_query = db.query(Fattura)

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


def get_invoice_details(fattura_id: int) -> dict[str, Any]:
    """
    Get detailed information about an invoice.

    Args:
        fattura_id: Invoice ID

    Returns:
        Dictionary with invoice details
    """
    db = SessionLocal()
    try:
        fattura = db.query(Fattura).filter(Fattura.id == fattura_id).first()

        if not fattura:
            return {"error": f"Fattura {fattura_id} non trovata"}

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


def get_invoice_stats(anno: int | None = None) -> dict[str, Any]:
    """
    Get statistics about invoices.

    Args:
        anno: Filter by year (current year if None)

    Returns:
        Dictionary with stats
    """
    from datetime import datetime

    db = SessionLocal()
    try:
        year = anno or datetime.now().year

        # Count by status
        stats = {
            "anno": year,
            "totale_fatture": 0,
            "per_stato": {},
            "importo_totale": 0.0,
        }

        for stato in StatoFattura:
            count = db.query(Fattura).filter(Fattura.anno == year, Fattura.stato == stato).count()
            stats["per_stato"][stato.value] = count
            stats["totale_fatture"] += count

        # Total amount
        fatture = db.query(Fattura).filter(Fattura.anno == year).all()
        stats["importo_totale"] = sum(float(f.totale) for f in fatture)

        return stats

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
