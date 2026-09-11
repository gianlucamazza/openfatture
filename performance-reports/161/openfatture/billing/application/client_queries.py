"""Client read use-cases for the application layer."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session, selectinload

from openfatture.platform.logging import get_logger
from openfatture.platform.security import sanitize_sql_like_input, validate_integer_input
from openfatture.storage.database.base import get_session
from openfatture.storage.database.models import Cliente

logger = get_logger(__name__)


def search_clients(
    query: str | None = None,
    limit: int = 10,
    *,
    session: Session | None = None,
) -> dict[str, Any]:
    """Search clients by name, VAT, or tax code."""
    if query is not None:
        query = sanitize_sql_like_input(query)
    limit = validate_integer_input(limit, min_value=1, max_value=100)

    owns_session = session is None
    db = session or get_session()
    try:
        db_query = db.query(Cliente)
        if query:
            query_lower = f"%{query.lower()}%"
            db_query = db_query.filter(
                (Cliente.denominazione.ilike(query_lower))
                | (Cliente.partita_iva.ilike(query_lower))
                | (Cliente.codice_fiscale.ilike(query_lower))
            )
        db_query = db_query.order_by(Cliente.denominazione)
        clienti = db_query.limit(limit).all()
        results = [
            {
                "id": c.id,
                "denominazione": c.denominazione,
                "partita_iva": c.partita_iva or "",
                "codice_fiscale": c.codice_fiscale or "",
                "email": c.email or "",
                "fatture_count": len(c.fatture),
            }
            for c in clienti
        ]
        return {
            "count": len(results),
            "clienti": results,
            "has_more": len(clienti) == limit,
        }
    except Exception as e:
        logger.error("search_clients_failed", error=str(e))
        return {"error": str(e), "count": 0, "clienti": []}
    finally:
        if owns_session:
            db.close()


def get_client_details(
    cliente_id: int,
    *,
    session: Session | None = None,
) -> dict[str, Any]:
    """Return detailed client information including recent invoices."""
    cliente_id = validate_integer_input(cliente_id, min_value=1)
    owns_session = session is None
    db = session or get_session()
    try:
        cliente = (
            db.query(Cliente)
            .options(selectinload(Cliente.fatture))
            .filter(Cliente.id == cliente_id)
            .first()
        )
        if cliente is None:
            return {"error": f"Cliente {cliente_id} non trovato"}

        details: dict[str, Any] = {
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
        if owns_session:
            db.close()


def get_client_stats(*, session: Session | None = None) -> dict[str, Any]:
    """Return aggregate client statistics."""
    owns_session = session is None
    db = session or get_session()
    try:
        return {
            "totale_clienti": db.query(Cliente).count(),
            "con_partita_iva": db.query(Cliente).filter(Cliente.partita_iva.isnot(None)).count(),
            "con_email": db.query(Cliente).filter(Cliente.email.isnot(None)).count(),
            "con_pec": db.query(Cliente).filter(Cliente.pec.isnot(None)).count(),
        }
    except Exception as e:
        logger.error("get_client_stats_failed", error=str(e))
        return {"error": str(e)}
    finally:
        if owns_session:
            db.close()
