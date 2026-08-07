"""Tools for payment tracking and reconciliation operations."""

from typing import Any

from pydantic import validate_call

from openfatture.payment.domain.enums import TransactionStatus
from openfatture.platform.logging import get_logger
from openfatture.platform.security import validate_integer_input
from openfatture.storage.database.base import get_session
from openfatture.storage.database.models import Pagamento, StatoPagamento

logger = get_logger(__name__)


# =============================================================================
# Payment Query Tools
# =============================================================================


@validate_call
def get_payment_status(fattura_id: int) -> dict[str, Any]:
    """
    Get payment status for an invoice.

    Args:
        fattura_id: Invoice ID

    Returns:
        Dictionary with payment status and details
    """
    from openfatture.storage.database.models import Fattura

    # Validate input
    fattura_id = validate_integer_input(fattura_id, min_value=1)

    db = get_session()
    try:
        # Get invoice with payments
        fattura = db.query(Fattura).filter(Fattura.id == fattura_id).first()
        if not fattura:
            return {"error": f"Invoice {fattura_id} not found"}

        # Get all payments for this invoice
        pagamenti = db.query(Pagamento).filter(Pagamento.fattura_id == fattura_id).all()

        if not pagamenti:
            return {
                "invoice_id": fattura_id,
                "invoice_number": f"{fattura.numero}/{fattura.anno}",
                "total_amount": float(fattura.totale),
                "payment_status": "no_payment_record",
                "amount_paid": 0.0,
                "amount_due": float(fattura.totale),
                "payments": [],
                "message": "No payment records found for this invoice",
            }

        # Aggregate payment info
        total_paid = sum(float(p.importo_pagato) for p in pagamenti)
        total_due = sum(float(p.importo) for p in pagamenti)
        outstanding = total_due - total_paid

        payments_info = []
        for p in pagamenti:
            payments_info.append(
                {
                    "payment_id": p.id,
                    "importo": float(p.importo),
                    "importo_pagato": float(p.importo_pagato),
                    "saldo_residuo": float(p.saldo_residuo),
                    "stato": p.stato.value,
                    "data_scadenza": p.data_scadenza.isoformat(),
                    "data_pagamento": p.data_pagamento.isoformat() if p.data_pagamento else None,
                    "modalita": p.modalita,
                }
            )

        # Determine overall status
        if total_paid >= total_due:
            overall_status = "fully_paid"
        elif total_paid > 0:
            overall_status = "partially_paid"
        else:
            overall_status = "unpaid"

        return {
            "invoice_id": fattura_id,
            "invoice_number": f"{fattura.numero}/{fattura.anno}",
            "total_amount": float(fattura.totale),
            "payment_status": overall_status,
            "amount_paid": total_paid,
            "amount_due": total_due,
            "outstanding": outstanding,
            "payments_count": len(pagamenti),
            "payments": payments_info,
        }

    except Exception as e:
        logger.error("get_payment_status_failed", fattura_id=fattura_id, error=str(e))
        return {"error": str(e)}
    finally:
        db.close()


@validate_call
def search_payments(
    stato: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Search for payments with filters.

    Args:
        stato: Filter by status (da_pagare, pagato_parziale, pagato, scaduto)
        limit: Maximum results

    Returns:
        Dictionary with search results
    """
    # Validate input
    limit = validate_integer_input(limit, min_value=1, max_value=100)

    db = get_session()
    try:
        query = db.query(Pagamento)

        if stato:
            try:
                stato_enum = StatoPagamento(stato.lower())
                query = query.filter(Pagamento.stato == stato_enum)
            except ValueError:
                return {
                    "error": f"Invalid status: {stato}. Valid: da_pagare, pagato_parziale, pagato, scaduto"
                }

        # Order by due date
        query = query.order_by(Pagamento.data_scadenza.desc())

        pagamenti = query.limit(limit).all()

        # Format results
        results = []
        for p in pagamenti:
            results.append(
                {
                    "payment_id": p.id,
                    "fattura_id": p.fattura_id,
                    "invoice_number": f"{p.fattura.numero}/{p.fattura.anno}" if p.fattura else None,
                    "cliente": (
                        p.fattura.cliente.denominazione if p.fattura and p.fattura.cliente else None
                    ),
                    "importo": float(p.importo),
                    "importo_pagato": float(p.importo_pagato),
                    "saldo_residuo": float(p.saldo_residuo),
                    "stato": p.stato.value,
                    "data_scadenza": p.data_scadenza.isoformat(),
                    "data_pagamento": p.data_pagamento.isoformat() if p.data_pagamento else None,
                    "modalita": p.modalita,
                }
            )

        return {
            "count": len(results),
            "payments": results,
            "has_more": len(pagamenti) == limit,
        }

    except Exception as e:
        logger.error("search_payments_failed", error=str(e))
        return {"error": str(e), "count": 0, "payments": []}
    finally:
        db.close()


@validate_call
def search_bank_transactions(
    description: str | None = None,
    status: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Search bank transactions.

    Args:
        description: Search in transaction description
        status: Filter by status (unmatched, matched, ignored)
        limit: Maximum results

    Returns:
        Dictionary with search results
    """
    from openfatture.payment.domain.models import BankTransaction

    # Validate input
    limit = validate_integer_input(limit, min_value=1, max_value=100)

    db = get_session()
    try:
        query = db.query(BankTransaction)

        if description:
            query = query.filter(BankTransaction.description.ilike(f"%{description}%"))

        if status:
            try:
                status_enum = TransactionStatus(status.lower())
                query = query.filter(BankTransaction.status == status_enum)
            except ValueError:
                return {"error": f"Invalid status: {status}. Valid: unmatched, matched, ignored"}

        # Order by date desc
        query = query.order_by(BankTransaction.date.desc())

        transactions = query.limit(limit).all()

        # Format results
        results = []
        for tx in transactions:
            results.append(
                {
                    "transaction_id": str(tx.id),
                    "account_id": tx.account_id,
                    "account_name": tx.account.name if tx.account else None,
                    "date": tx.date.isoformat(),
                    "amount": float(tx.amount),
                    "description": tx.description,
                    "reference": tx.reference,
                    "counterparty": tx.counterparty,
                    "status": tx.status.value,
                    "matched_payment_id": tx.matched_payment_id,
                    "match_confidence": tx.match_confidence,
                    "match_type": tx.match_type.value if tx.match_type else None,
                }
            )

        return {
            "count": len(results),
            "transactions": results,
            "has_more": len(transactions) == limit,
        }

    except Exception as e:
        logger.error("search_bank_transactions_failed", error=str(e))
        return {"error": str(e), "count": 0, "transactions": []}
    finally:
        db.close()


@validate_call
def get_payment_stats() -> dict[str, Any]:
    """
    Get payment statistics.

    Returns:
        Dictionary with payment stats
    """
    from datetime import datetime

    db = get_session()
    try:
        # Count by status
        stats: dict[str, Any] = {
            "by_status": {},
            "total_payments": 0,
            "total_amount_due": 0.0,
            "total_amount_paid": 0.0,
            "total_outstanding": 0.0,
        }

        for stato in StatoPagamento:
            count = db.query(Pagamento).filter(Pagamento.stato == stato).count()
            stats["by_status"][stato.value] = count
            stats["total_payments"] += count

        # Get amounts
        all_payments = db.query(Pagamento).all()
        stats["total_amount_due"] = sum(float(p.importo) for p in all_payments)
        stats["total_amount_paid"] = sum(float(p.importo_pagato) for p in all_payments)
        stats["total_outstanding"] = sum(float(p.saldo_residuo) for p in all_payments)

        # Overdue payments (past due date and not fully paid)
        today = datetime.now().date()
        overdue = (
            db.query(Pagamento)
            .filter(
                Pagamento.data_scadenza < today,
                Pagamento.stato != StatoPagamento.PAGATO,
            )
            .all()
        )
        stats["overdue_count"] = len(overdue)
        stats["overdue_amount"] = sum(float(p.saldo_residuo) for p in overdue)

        return stats

    except Exception as e:
        logger.error("get_payment_stats_failed", error=str(e))
        return {"error": str(e)}
    finally:
        db.close()
