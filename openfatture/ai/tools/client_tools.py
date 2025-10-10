"""Tools for client operations."""

from typing import Any

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
from openfatture.storage.database.base import SessionLocal
from openfatture.storage.database.models import Cliente
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# Client Query Tools
# =============================================================================


def search_clients(
    query: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """
    Search for clients.

    Args:
        query: Search in client name, P.IVA, or CF
        limit: Maximum results

    Returns:
        Dictionary with search results
    """
    db = SessionLocal()
    try:
        # Build query
        db_query = db.query(Cliente)

        if query:
            query_lower = f"%{query.lower()}%"
            db_query = db_query.filter(
                (Cliente.denominazione.ilike(query_lower))
                | (Cliente.partita_iva.ilike(query_lower))
                | (Cliente.codice_fiscale.ilike(query_lower))
            )

        # Order by name
        db_query = db_query.order_by(Cliente.denominazione)

        # Get results
        clienti = db_query.limit(limit).all()

        # Format results
        results = []
        for c in clienti:
            results.append(
                {
                    "id": c.id,
                    "denominazione": c.denominazione,
                    "partita_iva": c.partita_iva or "",
                    "codice_fiscale": c.codice_fiscale or "",
                    "email": c.email or "",
                    "fatture_count": len(c.fatture),
                }
            )

        return {
            "count": len(results),
            "clienti": results,
            "has_more": len(clienti) == limit,
        }

    except Exception as e:
        logger.error("search_clients_failed", error=str(e))
        return {"error": str(e), "count": 0, "clienti": []}

    finally:
        db.close()


def get_client_details(cliente_id: int) -> dict[str, Any]:
    """
    Get detailed information about a client.

    Args:
        cliente_id: Client ID

    Returns:
        Dictionary with client details
    """
    db = SessionLocal()
    try:
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()

        if not cliente:
            return {"error": f"Cliente {cliente_id} non trovato"}

        # Format details
        details = {
            "id": cliente.id,
            "denominazione": cliente.denominazione,
            "partita_iva": cliente.partita_iva or "",
            "codice_fiscale": cliente.codice_fiscale or "",
            "indirizzo": {
                "via": cliente.indirizzo or "",
                "cap": cliente.cap or "",
                "comune": cliente.comune or "",
                "provincia": cliente.provincia or "",
                "nazione": cliente.nazione or "IT",
            },
            "contatti": {
                "email": cliente.email or "",
                "pec": cliente.pec or "",
                "telefono": cliente.telefono or "",
            },
            "fatture_count": len(cliente.fatture),
        }

        # Add recent invoices
        fatture_recenti = (
            sorted(cliente.fatture, key=lambda f: f.data_emissione, reverse=True)[:5]
            if cliente.fatture
            else []
        )

        details["fatture_recenti"] = [
            {
                "id": f.id,
                "numero": f.numero,
                "anno": f.anno,
                "data": f.data_emissione.isoformat(),
                "importo": float(f.totale),
                "stato": f.stato.value,
            }
            for f in fatture_recenti
        ]

        return details

    except Exception as e:
        logger.error("get_client_details_failed", cliente_id=cliente_id, error=str(e))
        return {"error": str(e)}

    finally:
        db.close()


def get_client_stats() -> dict[str, Any]:
    """
    Get statistics about clients.

    Returns:
        Dictionary with client stats
    """
    db = SessionLocal()
    try:
        stats = {
            "totale_clienti": db.query(Cliente).count(),
            "con_partita_iva": db.query(Cliente).filter(Cliente.partita_iva.isnot(None)).count(),
            "con_email": db.query(Cliente).filter(Cliente.email.isnot(None)).count(),
            "con_pec": db.query(Cliente).filter(Cliente.pec.isnot(None)).count(),
        }

        return stats

    except Exception as e:
        logger.error("get_client_stats_failed", error=str(e))
        return {"error": str(e)}

    finally:
        db.close()


# =============================================================================
# Tool Definitions
# =============================================================================


def get_client_tools() -> list[Tool]:
    """
    Get all client-related tools.

    Returns:
        List of Tool instances
    """
    return [
        Tool(
            name="search_clients",
            description="Search for clients by name, partita IVA, or codice fiscale",
            category="clients",
            parameters=[
                ToolParameter(
                    name="query",
                    type=ToolParameterType.STRING,
                    description="Search query (name, P.IVA, or CF)",
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
            func=search_clients,
            examples=[
                "search_clients(query='Rossi')",
                "search_clients(query='12345678901')",
                "search_clients(limit=5)",
            ],
            tags=["search", "query"],
        ),
        Tool(
            name="get_client_details",
            description="Get detailed information about a specific client",
            category="clients",
            parameters=[
                ToolParameter(
                    name="cliente_id",
                    type=ToolParameterType.INTEGER,
                    description="Client ID",
                    required=True,
                ),
            ],
            func=get_client_details,
            examples=["get_client_details(cliente_id=1)"],
            tags=["details", "view"],
        ),
        Tool(
            name="get_client_stats",
            description="Get statistics about all clients",
            category="clients",
            parameters=[],
            func=get_client_stats,
            examples=["get_client_stats()"],
            tags=["stats", "analytics"],
        ),
    ]
