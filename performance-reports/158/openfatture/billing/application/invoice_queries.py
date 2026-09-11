"""Invoice read use-cases for the application layer.

AI tools and other adapters must call these functions instead of opening
SQLAlchemy sessions directly.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, TypedDict

from sqlalchemy.orm import Session, selectinload

from openfatture.platform.logging import get_logger
from openfatture.platform.security import sanitize_sql_like_input, validate_integer_input
from openfatture.storage.database.base import get_session
from openfatture.storage.database.models import Fattura, StatoFattura

logger = get_logger(__name__)


class InvoiceStats(TypedDict):
    anno: int
    totale_fatture: int
    per_stato: dict[str, int]
    importo_totale: float


def search_invoices(
    query: str | None = None,
    anno: int | None = None,
    stato: str | None = None,
    cliente_id: int | None = None,
    limit: int = 10,
    *,
    session: Session | None = None,
) -> dict[str, Any]:
    """Search invoices matching criteria."""
    if query is not None:
        query = sanitize_sql_like_input(query)
    if anno is not None:
        anno = validate_integer_input(anno, min_value=2000, max_value=2100)
    if cliente_id is not None:
        cliente_id = validate_integer_input(cliente_id, min_value=1)
    limit = validate_integer_input(limit, min_value=1, max_value=100)

    owns_session = session is None
    db = session or get_session()
    try:
        db_query = db.query(Fattura).options(selectinload(Fattura.cliente))

        if query:
            db_query = db_query.filter(
                (Fattura.numero.contains(query)) | (Fattura.note.contains(query))
            )
        if anno:
            db_query = db_query.filter(Fattura.anno == anno)
        if stato:
            try:
                db_query = db_query.filter(Fattura.stato == StatoFattura(stato))
            except ValueError:
                pass
        if cliente_id:
            db_query = db_query.filter(Fattura.cliente_id == cliente_id)

        db_query = db_query.order_by(Fattura.anno.desc(), Fattura.numero.desc())
        fatture = db_query.limit(limit).all()

        results = []
        for f in fatture:
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
        if owns_session:
            db.close()


def get_invoice_details(
    fattura_id: int,
    *,
    session: Session | None = None,
) -> dict[str, Any]:
    """Return detailed invoice information."""
    fattura_id = validate_integer_input(fattura_id, min_value=1)
    owns_session = session is None
    db = session or get_session()
    try:
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

        details: dict[str, Any] = {
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
        if owns_session:
            db.close()


def get_invoice_stats(
    anno: int | None = None,
    *,
    session: Session | None = None,
) -> dict[str, Any]:
    """Return aggregate invoice statistics for a year."""
    if anno is not None:
        anno = validate_integer_input(anno, min_value=2000, max_value=2100)

    owns_session = session is None
    db = session or get_session()
    try:
        year = anno or datetime.now().year
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
        fatture = db.query(Fattura).filter(Fattura.anno == year).all()
        stats["importo_totale"] = sum(float(f.totale) for f in fatture)
        return dict(stats)
    except Exception as e:
        logger.error("get_invoice_stats_failed", error=str(e))
        return {"error": str(e)}
    finally:
        if owns_session:
            db.close()
