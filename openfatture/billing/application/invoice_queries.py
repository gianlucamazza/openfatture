"""Invoice read use-cases for the application layer.

AI tools and other adapters must call these functions instead of opening
SQLAlchemy sessions directly.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, TypedDict

from sqlalchemy import Integer, cast
from sqlalchemy.orm import Session, selectinload

from openfatture.platform.logging import get_logger
from openfatture.platform.security import sanitize_sql_like_input, validate_integer_input
from openfatture.storage.database.models import Fattura, StatoFattura
from openfatture.storage.session import session_scope

logger = get_logger(__name__)


def payment_summary(invoice: Fattura, payments: Any = None) -> dict[str, Any]:
    """Summarize recorded collections against the full invoice total."""
    payments = invoice.pagamenti if payments is None else payments
    entries = list(getattr(invoice, "collection_entries", []))
    statements = list(getattr(invoice, "collection_statements", []))
    paid = sum((p.importo_pagato for p in payments), Decimal("0.00"))
    paid += sum(
        (e.amount for e in entries if e.payment_id is None),
        Decimal("0.00"),
    )
    status = (
        "no_payment_record"
        if not payments and not entries
        else "fully_paid"
        if paid >= invoice.totale
        else "partially_paid"
        if paid > 0
        else "unpaid"
    )
    return {
        "payment_status": status,
        "collection_statement": (
            {
                "value": max(statements, key=lambda st: st.id).value,
                "source": max(statements, key=lambda st: st.id).source,
            }
            if statements
            else None
        ),
        "amount_paid": float(paid),
        "outstanding": float(max(invoice.totale - paid, Decimal("0.00"))),
    }


def status_evidence(invoice: Fattura) -> dict[str, Any]:
    receipts = [r for r in invoice.sdi_receipts if r.outcome == "applied"]
    attempts = sorted(invoice.sdi_submissions, key=lambda a: a.id)
    latest = attempts[-1].outcome if attempts else None
    origin = (
        "sdi_receipt"
        if receipts
        else "submission_uncertain"
        if latest in {"pending", "uncertain"}
        else "transport_submission"
        if latest in {"sent", "confirmed_sent"}
        else "unverified"
        if invoice.issued_elsewhere
        else "local"
    )
    return {
        "status_origin": origin,
        "sdi_identifier": invoice.numero_sdi,
        "sdi_evidence": [{"id": r.id, "source": r.source, "outcome": r.outcome} for r in receipts],
        "submission_state": latest,
        "submission_evidence": [{"id": a.id, "outcome": a.outcome} for a in attempts],
    }


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

    with session_scope(session) as db:
        try:
            db_query = db.query(Fattura).options(
                selectinload(Fattura.cliente),
                selectinload(Fattura.pagamenti),
                selectinload(Fattura.sdi_receipts),
                selectinload(Fattura.sdi_submissions),
                selectinload(Fattura.collection_entries),
                selectinload(Fattura.collection_statements),
            )

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

            db_query = db_query.order_by(
                Fattura.anno.desc(), cast(Fattura.numero, Integer).desc(), Fattura.numero.desc()
            )
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
                        "issued_elsewhere": f.issued_elsewhere,
                        **payment_summary(f),
                        **status_evidence(f),
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


def get_invoice_details(
    fattura_id: int,
    *,
    session: Session | None = None,
) -> dict[str, Any]:
    """Return detailed invoice information."""
    fattura_id = validate_integer_input(fattura_id, min_value=1)
    with session_scope(session) as db:
        try:
            fattura = (
                db.query(Fattura)
                .options(
                    selectinload(Fattura.cliente),
                    selectinload(Fattura.righe),
                    selectinload(Fattura.sdi_receipts),
                    selectinload(Fattura.sdi_submissions),
                    selectinload(Fattura.collection_entries),
                    selectinload(Fattura.collection_statements),
                    selectinload(Fattura.pagamenti),
                )
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
                "issued_elsewhere": fattura.issued_elsewhere,
                **payment_summary(fattura),
                **status_evidence(fattura),
                "pagamenti": [
                    {
                        "id": p.id,
                        "importo": float(p.importo),
                        "incassato": float(p.importo_pagato),
                        "residuo": float(p.saldo_residuo),
                        "data_scadenza": p.data_scadenza.isoformat() if p.data_scadenza else None,
                        "data_pagamento": p.data_pagamento.isoformat()
                        if p.data_pagamento
                        else None,
                    }
                    for p in fattura.pagamenti
                ],
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


def get_invoice_stats(
    anno: int | None = None,
    *,
    session: Session | None = None,
) -> dict[str, Any]:
    """Return aggregate invoice statistics for a year."""
    if anno is not None:
        anno = validate_integer_input(anno, min_value=2000, max_value=2100)

    with session_scope(session) as db:
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
                count = (
                    db.query(Fattura).filter(Fattura.anno == year, Fattura.stato == stato).count()
                )
                per_stato[stato.value] = count
                stats["totale_fatture"] += count
            fatture = (
                db.query(Fattura)
                .options(
                    selectinload(Fattura.pagamenti),
                    selectinload(Fattura.sdi_submissions),
                    selectinload(Fattura.collection_entries),
                    selectinload(Fattura.collection_statements),
                )
                .filter(Fattura.anno == year)
                .all()
            )
            stats["importo_totale"] = float(sum((f.totale for f in fatture), Decimal("0.00")))
            result: dict[str, Any] = dict(stats)
            historical = [f for f in fatture if f.issued_elsewhere]
            result["fatture_storiche"] = len(historical)
            result["invii_da_verificare"] = [
                {"invoice_id": f.id, "attempt_id": a.id, "outcome": a.outcome}
                for f in fatture
                for a in f.sdi_submissions
                if a.outcome in {"pending", "uncertain"}
            ]

            result["per_documento"] = {
                "storica": len(historical),
                **{
                    status.value: sum(
                        1 for f in fatture if not f.issued_elsewhere and f.stato == status
                    )
                    for status in StatoFattura
                },
            }
            result["per_stato_incasso"] = {}
            collected = Decimal("0.00")
            outstanding = Decimal("0.00")
            for invoice in fatture:
                summary = payment_summary(invoice)
                status = summary["payment_status"]
                result["per_stato_incasso"][status] = result["per_stato_incasso"].get(status, 0) + 1
                paid = sum((p.importo_pagato for p in invoice.pagamenti), Decimal("0.00")) + sum(
                    (
                        e.amount
                        for e in getattr(invoice, "collection_entries", [])
                        if e.payment_id is None
                    ),
                    Decimal("0.00"),
                )
                collected += paid
                outstanding += max(invoice.totale - paid, Decimal("0.00"))
            result["incassato_totale"] = float(collected)
            result["residuo_totale"] = float(outstanding)
            result["avvertenza_stato"] = (
                "per_stato descrive soltanto lo stato tecnico locale. Usare per_documento per distinguere le storiche dalle bozze. Per documenti issued_elsewhere senza ricevute associate lo stato SDI non è verificato: non dedurre mancata trasmissione o emissione da bozza. Incassi e stato SDI sono indipendenti."
            )
            return result
        except Exception as e:
            logger.error("get_invoice_stats_failed", error=str(e))
            return {"error": str(e)}
