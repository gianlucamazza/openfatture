"""Preventivo (quote/estimate) read use-cases (application layer)."""

from typing import Any

from pydantic import validate_call

from openfatture.billing.preventivi.service import PreventivoService
from openfatture.platform.config import get_settings
from openfatture.platform.errors import describe_error
from openfatture.platform.logging import get_logger
from openfatture.platform.security import validate_integer_input
from openfatture.storage.database.models import Preventivo, StatoPreventivo
from openfatture.storage.session import db_session

logger = get_logger(__name__)


@validate_call
def search_preventivi(
    stato: str | None = None,
    cliente_id: int | None = None,
    anno: int | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Search preventivi with filters.

    Args:
        stato: Filter by status (bozza, inviato, accettato, rifiutato, scaduto, convertito)
        cliente_id: Filter by client ID
        anno: Filter by year
        limit: Maximum results (default 20, max 100)

    Returns:
        Dictionary with search results
    """
    # Validate inputs
    if cliente_id is not None:
        cliente_id = validate_integer_input(cliente_id, min_value=1)
    if anno is not None:
        anno = validate_integer_input(anno, min_value=2000, max_value=2100)
    limit = validate_integer_input(limit, min_value=1, max_value=100)

    with db_session() as db:
        try:
            # Parse status if provided
            stato_enum = None
            if stato:
                try:
                    stato_enum = StatoPreventivo(stato.lower())
                except ValueError:
                    return {
                        "error": f"Invalid status: {stato}. Valid: bozza, inviato, accettato, rifiutato, scaduto, convertito",
                        "count": 0,
                        "preventivi": [],
                    }

            # Use service to list preventivi
            settings = get_settings()
            service = PreventivoService(settings=settings)

            preventivi = service.list_preventivi(
                db=db,
                stato=stato_enum,
                cliente_id=cliente_id,
                anno=anno,
                limit=limit,
            )

            # Format results
            results = []
            for p in preventivi:
                results.append(
                    {
                        "preventivo_id": p.id,
                        "numero": f"{p.numero}/{p.anno}",
                        "data_emissione": p.data_emissione.isoformat(),
                        "data_scadenza": p.data_scadenza.isoformat(),
                        "cliente": p.cliente.denominazione if p.cliente else None,
                        "cliente_id": p.cliente_id,
                        "imponibile": float(p.imponibile),
                        "iva": float(p.iva),
                        "totale": float(p.totale),
                        "stato": p.stato.value,
                        "validita_giorni": p.validita_giorni,
                        "righe_count": len(p.righe) if p.righe else 0,
                    }
                )

            return {
                "count": len(results),
                "preventivi": results,
                "has_more": len(preventivi) == limit,
            }

        except Exception as e:
            logger.error("search_preventivi_failed", error=str(e))
            return {"error": describe_error(e), "count": 0, "preventivi": []}


@validate_call
def get_preventivo_details(preventivo_id: int) -> dict[str, Any]:
    """
    Get detailed information about a preventivo.

    Args:
        preventivo_id: Preventivo ID

    Returns:
        Dictionary with preventivo details
    """
    # Validate input
    preventivo_id = validate_integer_input(preventivo_id, min_value=1)

    with db_session() as db:
        try:
            preventivo = db.query(Preventivo).filter(Preventivo.id == preventivo_id).first()

            if not preventivo:
                return {"error": f"Preventivo {preventivo_id} not found"}

            # Format righe
            righe = []
            for riga in preventivo.righe:
                righe.append(
                    {
                        "numero_riga": riga.numero_riga,
                        "descrizione": riga.descrizione,
                        "quantita": float(riga.quantita),
                        "prezzo_unitario": float(riga.prezzo_unitario),
                        "unita_misura": riga.unita_misura,
                        "aliquota_iva": float(riga.aliquota_iva),
                        "natura": riga.natura,
                        "imponibile": float(riga.imponibile),
                        "iva": float(riga.iva),
                        "totale": float(riga.totale),
                    }
                )

            return {
                "preventivo_id": preventivo.id,
                "numero": f"{preventivo.numero}/{preventivo.anno}",
                "anno": preventivo.anno,
                "data_emissione": preventivo.data_emissione.isoformat(),
                "data_scadenza": preventivo.data_scadenza.isoformat(),
                "cliente_id": preventivo.cliente_id,
                "cliente": (
                    {
                        "id": preventivo.cliente.id,
                        "denominazione": preventivo.cliente.denominazione,
                        "partita_iva": preventivo.cliente.partita_iva,
                        "email": preventivo.cliente.email,
                    }
                    if preventivo.cliente
                    else None
                ),
                "imponibile": float(preventivo.imponibile),
                "iva": float(preventivo.iva),
                "totale": float(preventivo.totale),
                "stato": preventivo.stato.value,
                "validita_giorni": preventivo.validita_giorni,
                "note": preventivo.note,
                "condizioni": preventivo.condizioni,
                "righe": righe,
                "fattura_id": preventivo.fattura.id if preventivo.fattura else None,
            }

        except Exception as e:
            logger.error("get_preventivo_details_failed", preventivo_id=preventivo_id, error=str(e))
            return {"error": describe_error(e)}
