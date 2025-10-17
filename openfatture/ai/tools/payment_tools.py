"""Tools for payment tracking and reconciliation operations."""

from typing import Any
from uuid import UUID

from pydantic import validate_call

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
from openfatture.payment.domain.enums import MatchType, TransactionStatus
from openfatture.storage.database.base import get_session
from openfatture.storage.database.models import Pagamento, StatoPagamento
from openfatture.utils.logging import get_logger
from openfatture.utils.security import validate_integer_input

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


# =============================================================================
# Payment WRITE Tools
# =============================================================================


@validate_call
def reconcile_payment(
    transaction_id: str,
    payment_id: int,
    match_type: str = "manual",
    confidence: float | None = None,
) -> dict[str, Any]:
    """
    Manually reconcile a bank transaction to a payment.

    Args:
        transaction_id: Bank transaction ID (UUID string)
        payment_id: Payment ID
        match_type: Type of match (manual, exact, fuzzy) - default manual
        confidence: Match confidence 0.0-1.0 (optional)

    Returns:
        Dictionary with reconciliation result
    """
    import asyncio

    from openfatture.cli.lifespan import get_event_bus
    from openfatture.payment.application.services.reconciliation_service import (
        ReconciliationService,
    )
    from openfatture.payment.infrastructure.repository import (
        BankTransactionRepository,
        PaymentRepository,
    )

    # Validate inputs
    payment_id = validate_integer_input(payment_id, min_value=1)

    try:
        tx_uuid = UUID(transaction_id)
    except ValueError:
        return {"error": f"Invalid transaction_id format: {transaction_id}. Must be a valid UUID"}

    try:
        match_type_enum = MatchType(match_type.lower())
    except ValueError:
        return {
            "error": f"Invalid match_type: {match_type}. Valid: manual, exact, fuzzy, iban, date_window"
        }

    if confidence is not None and not (0.0 <= confidence <= 1.0):
        return {"error": f"Confidence must be between 0.0 and 1.0, got {confidence}"}

    db = get_session()
    try:
        # Initialize repos and service
        tx_repo = BankTransactionRepository(db)
        payment_repo = PaymentRepository(db)
        event_bus = get_event_bus()

        # Create service with minimal matching service (not used for manual reconciliation)
        from openfatture.payment.application.services.matching_service import MatchingService
        from openfatture.payment.matchers import ExactAmountMatcher, FuzzyDescriptionMatcher

        matching_service = MatchingService(
            tx_repo=tx_repo,
            payment_repo=payment_repo,
            strategies=[ExactAmountMatcher(), FuzzyDescriptionMatcher()],
        )

        reconciliation_service = ReconciliationService(
            tx_repo=tx_repo,
            payment_repo=payment_repo,
            matching_service=matching_service,
            session=db,
            event_bus=event_bus,  # type: ignore[arg-type]
        )

        # Perform reconciliation
        transaction = asyncio.run(
            reconciliation_service.reconcile(
                transaction_id=tx_uuid,
                payment_id=payment_id,
                match_type=match_type_enum,
                confidence=confidence,
            )
        )

        db.commit()

        logger.info(
            "payment_reconciled",
            transaction_id=transaction_id,
            payment_id=payment_id,
            match_type=match_type,
        )

        return {
            "success": True,
            "transaction_id": str(transaction.id),
            "payment_id": payment_id,
            "status": transaction.status.value,
            "match_type": transaction.match_type.value if transaction.match_type else None,
            "match_confidence": transaction.match_confidence,
            "message": f"Transaction {transaction_id[:8]}... reconciled to payment {payment_id}",
        }

    except ValueError as e:
        return {"error": str(e)}
    except RuntimeError as e:
        return {"error": str(e)}
    except Exception as e:
        db.rollback()
        logger.error("reconcile_payment_failed", error=str(e))
        return {"error": str(e)}
    finally:
        db.close()


@validate_call
def create_manual_payment(
    fattura_id: int,
    importo: float,
    data_scadenza: str,
    importo_pagato: float = 0.0,
    data_pagamento: str | None = None,
    modalita: str = "bonifico",
) -> dict[str, Any]:
    """
    Manually create a payment record for an invoice.

    Args:
        fattura_id: Invoice ID
        importo: Total amount due
        data_scadenza: Due date (YYYY-MM-DD)
        importo_pagato: Amount already paid (default 0)
        data_pagamento: Payment date if already paid (YYYY-MM-DD, optional)
        modalita: Payment method (default "bonifico")

    Returns:
        Dictionary with payment creation result
    """
    from datetime import datetime
    from decimal import Decimal

    from openfatture.storage.database.models import Fattura

    # Validate inputs
    fattura_id = validate_integer_input(fattura_id, min_value=1)

    db = get_session()
    try:
        # Check invoice exists
        fattura = db.query(Fattura).filter(Fattura.id == fattura_id).first()
        if not fattura:
            return {"error": f"Invoice {fattura_id} not found"}

        # Parse dates
        try:
            data_scad = datetime.fromisoformat(data_scadenza).date()
        except ValueError:
            return {"error": f"Invalid data_scadenza format: {data_scadenza}. Use YYYY-MM-DD"}

        data_pag = None
        if data_pagamento:
            try:
                data_pag = datetime.fromisoformat(data_pagamento).date()
            except ValueError:
                return {"error": f"Invalid data_pagamento format: {data_pagamento}. Use YYYY-MM-DD"}

        # Convert to Decimal
        importo_dec = Decimal(str(importo))
        importo_pagato_dec = Decimal(str(importo_pagato))

        # Determine stato
        if importo_pagato_dec >= importo_dec:
            stato = StatoPagamento.PAGATO
        elif importo_pagato_dec > 0:
            stato = StatoPagamento.PAGATO_PARZIALE
        else:
            # Check if overdue
            today = datetime.now().date()
            if data_scad < today:
                stato = StatoPagamento.SCADUTO
            else:
                stato = StatoPagamento.DA_PAGARE

        # Create payment (saldo_residuo is computed automatically)
        pagamento = Pagamento(
            fattura_id=fattura_id,
            importo=importo_dec,
            importo_pagato=importo_pagato_dec,
            data_scadenza=data_scad,
            data_pagamento=data_pag,
            modalita=modalita,
            stato=stato,
        )

        db.add(pagamento)
        db.commit()
        db.refresh(pagamento)

        logger.info(
            "manual_payment_created",
            payment_id=pagamento.id,
            fattura_id=fattura_id,
            importo=float(importo),
            stato=stato.value,
        )

        return {
            "success": True,
            "payment_id": pagamento.id,
            "fattura_id": fattura_id,
            "invoice_number": f"{fattura.numero}/{fattura.anno}",
            "importo": float(importo),
            "importo_pagato": float(importo_pagato),
            "saldo_residuo": float(importo_dec - importo_pagato_dec),
            "stato": stato.value,
            "data_scadenza": data_scad.isoformat(),
            "data_pagamento": data_pag.isoformat() if data_pag else None,
            "modalita": modalita,
            "message": f"Payment record created for invoice {fattura.numero}/{fattura.anno}",
        }

    except Exception as e:
        db.rollback()
        logger.error("create_manual_payment_failed", error=str(e))
        return {"error": str(e)}
    finally:
        db.close()


@validate_call
def update_payment(
    payment_id: int,
    importo: float | None = None,
    importo_pagato: float | None = None,
    data_scadenza: str | None = None,
    data_pagamento: str | None = None,
    modalita: str | None = None,
) -> dict[str, Any]:
    """
    Update payment record details.

    Args:
        payment_id: Payment ID
        importo: Total amount due
        importo_pagato: Amount paid
        data_scadenza: Due date (YYYY-MM-DD)
        data_pagamento: Payment date (YYYY-MM-DD)
        modalita: Payment method

    Returns:
        Dictionary with update result
    """
    from datetime import datetime
    from decimal import Decimal

    # Validate input
    payment_id = validate_integer_input(payment_id, min_value=1)

    db = get_session()
    try:
        # Get payment
        pagamento = db.query(Pagamento).filter(Pagamento.id == payment_id).first()
        if not pagamento:
            return {"error": f"Payment {payment_id} not found"}

        # Track changes
        changes = []

        # Update importo
        if importo is not None:
            pagamento.importo = Decimal(str(importo))
            changes.append("importo")

        # Update importo_pagato
        if importo_pagato is not None:
            pagamento.importo_pagato = Decimal(str(importo_pagato))
            changes.append("importo_pagato")

        # Update dates
        if data_scadenza is not None:
            try:
                pagamento.data_scadenza = datetime.fromisoformat(data_scadenza).date()
                changes.append("data_scadenza")
            except ValueError:
                return {"error": f"Invalid data_scadenza format: {data_scadenza}. Use YYYY-MM-DD"}

        if data_pagamento is not None:
            try:
                pagamento.data_pagamento = datetime.fromisoformat(data_pagamento).date()
                changes.append("data_pagamento")
            except ValueError:
                return {"error": f"Invalid data_pagamento format: {data_pagamento}. Use YYYY-MM-DD"}

        # Update modalita
        if modalita is not None:
            pagamento.modalita = modalita
            changes.append("modalita")

        if not changes:
            return {
                "success": True,
                "payment_id": payment_id,
                "message": "No changes made (all fields same as current values)",
            }

        # Recalculate stato (saldo_residuo is computed automatically)
        if pagamento.importo_pagato >= pagamento.importo:
            pagamento.stato = StatoPagamento.PAGATO
        elif pagamento.importo_pagato > 0:
            pagamento.stato = StatoPagamento.PAGATO_PARZIALE
        else:
            # Check if overdue
            today = datetime.now().date()
            if pagamento.data_scadenza < today:
                pagamento.stato = StatoPagamento.SCADUTO
            else:
                pagamento.stato = StatoPagamento.DA_PAGARE

        db.commit()
        db.refresh(pagamento)

        logger.info("payment_updated", payment_id=payment_id, changes=changes)

        return {
            "success": True,
            "payment_id": pagamento.id,
            "fattura_id": pagamento.fattura_id,
            "changes": changes,
            "importo": float(pagamento.importo),
            "importo_pagato": float(pagamento.importo_pagato),
            "saldo_residuo": float(pagamento.saldo_residuo),
            "stato": pagamento.stato.value,
            "message": f"Payment {payment_id} updated. Changed fields: {', '.join(changes)}",
        }

    except Exception as e:
        db.rollback()
        logger.error("update_payment_failed", payment_id=payment_id, error=str(e))
        return {"error": str(e)}
    finally:
        db.close()


@validate_call
def delete_payment(
    payment_id: int,
) -> dict[str, Any]:
    """
    Delete payment record from database.

    CRITICAL: This operation is irreversible. Payment must not be linked to bank transactions.

    Args:
        payment_id: Payment ID to delete

    Returns:
        Dictionary with deletion result
    """
    from openfatture.payment.domain.models import BankTransaction

    # Validate input
    payment_id = validate_integer_input(payment_id, min_value=1)

    db = get_session()
    try:
        # Get payment
        pagamento = db.query(Pagamento).filter(Pagamento.id == payment_id).first()
        if not pagamento:
            return {"error": f"Payment {payment_id} not found"}

        # Check if linked to bank transactions
        linked_txs = (
            db.query(BankTransaction)
            .filter(BankTransaction.matched_payment_id == payment_id)
            .count()
        )

        if linked_txs > 0:
            return {
                "error": f"Cannot delete payment linked to {linked_txs} bank transactions. Unlink first.",
                "linked_transactions": linked_txs,
            }

        # Store info for response
        fattura_id = pagamento.fattura_id
        importo = pagamento.importo

        # Delete payment
        db.delete(pagamento)
        db.commit()

        logger.warning("payment_deleted", payment_id=payment_id, fattura_id=fattura_id)

        return {
            "success": True,
            "payment_id": payment_id,
            "fattura_id": fattura_id,
            "importo": float(importo),
            "message": f"Payment {payment_id} deleted successfully",
        }

    except Exception as e:
        db.rollback()
        logger.error("delete_payment_failed", payment_id=payment_id, error=str(e))
        return {"error": str(e)}
    finally:
        db.close()


@validate_call
def import_bank_transactions(
    file_path: str,
    account_name: str = "Main Account",
) -> dict[str, Any]:
    """
    Import bank transactions from OFX/QFX file.

    Args:
        file_path: Path to OFX/QFX bank statement file
        account_name: Bank account name (default "Main Account")

    Returns:
        Dictionary with import result
    """
    import asyncio
    from pathlib import Path

    # NOTE: These imports are for planned/future modules (bank import refactoring)
    # Current implementation uses: openfatture.payment.infrastructure.importers.ofx_importer.OFXImporter
    # See pyproject.toml [[tool.mypy.overrides]] for type checking configuration
    from openfatture.payment.application.services.bank_import_service import BankImportService
    from openfatture.payment.domain.models import BankAccount
    from openfatture.payment.infrastructure.ofx_parser import OFXParser
    from openfatture.payment.infrastructure.repository import BankTransactionRepository

    db = get_session()
    try:
        # Validate file exists
        file = Path(file_path)
        if not file.exists():
            return {"error": f"File not found: {file_path}"}

        # Check file extension
        if file.suffix.lower() not in [".ofx", ".qfx"]:
            return {"error": f"Invalid file type: {file.suffix}. Must be .ofx or .qfx"}

        # Get or create account
        account = db.query(BankAccount).filter(BankAccount.name == account_name).first()
        if not account:
            account = BankAccount(name=account_name, currency="EUR")
            db.add(account)
            db.flush()

        # Import transactions
        parser = OFXParser()
        tx_repo = BankTransactionRepository(db)
        import_service = BankImportService(parser=parser, tx_repo=tx_repo)

        result = asyncio.run(import_service.import_from_file(str(file), account.id))

        db.commit()

        logger.info(
            "bank_transactions_imported",
            file_path=file_path,
            account_id=account.id,
            imported=result["imported"],
            skipped=result["skipped"],
        )

        return {
            "success": True,
            "account_id": account.id,
            "account_name": account.name,
            "file_path": str(file),
            "imported": result["imported"],
            "skipped": result["skipped"],
            "total_transactions": result["imported"] + result["skipped"],
            "message": f"Imported {result['imported']} transactions ({result['skipped']} skipped as duplicates)",
        }

    except Exception as e:
        db.rollback()
        logger.error("import_bank_transactions_failed", error=str(e))
        return {"error": str(e)}
    finally:
        db.close()


# =============================================================================
# Tool Definitions
# =============================================================================


def get_payment_tools() -> list[Tool]:
    """
    Get all payment-related tools.

    Returns:
        List of Tool instances
    """
    return [
        Tool(
            name="get_payment_status",
            description="Get payment status and details for an invoice",
            category="payments",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID",
                    required=True,
                ),
            ],
            func=get_payment_status,
            examples=["get_payment_status(fattura_id=123)"],
            tags=["payment", "status"],
        ),
        Tool(
            name="search_payments",
            description="Search for payments with optional status filter",
            category="payments",
            parameters=[
                ToolParameter(
                    name="stato",
                    type=ToolParameterType.STRING,
                    description="Filter by status",
                    required=False,
                    enum=["da_pagare", "pagato_parziale", "pagato", "scaduto"],
                ),
                ToolParameter(
                    name="limit",
                    type=ToolParameterType.INTEGER,
                    description="Maximum number of results",
                    required=False,
                    default=20,
                ),
            ],
            func=search_payments,
            examples=[
                "search_payments()",
                "search_payments(stato='da_pagare', limit=10)",
            ],
            tags=["search", "payment"],
        ),
        Tool(
            name="search_bank_transactions",
            description="Search bank transactions by description or status",
            category="payments",
            parameters=[
                ToolParameter(
                    name="description",
                    type=ToolParameterType.STRING,
                    description="Search in transaction description",
                    required=False,
                ),
                ToolParameter(
                    name="status",
                    type=ToolParameterType.STRING,
                    description="Filter by status",
                    required=False,
                    enum=["unmatched", "matched", "ignored"],
                ),
                ToolParameter(
                    name="limit",
                    type=ToolParameterType.INTEGER,
                    description="Maximum number of results",
                    required=False,
                    default=20,
                ),
            ],
            func=search_bank_transactions,
            examples=[
                "search_bank_transactions(status='unmatched')",
                "search_bank_transactions(description='Bonifico', limit=10)",
            ],
            tags=["search", "bank", "transaction"],
        ),
        Tool(
            name="get_payment_stats",
            description="Get payment statistics (counts, amounts by status, overdue)",
            category="payments",
            parameters=[],
            func=get_payment_stats,
            examples=["get_payment_stats()"],
            tags=["stats", "analytics", "payment"],
        ),
        Tool(
            name="reconcile_payment",
            description="Manually reconcile a bank transaction to a payment. Requires transaction_id (UUID) and payment_id.",
            category="payments",
            parameters=[
                ToolParameter(
                    name="transaction_id",
                    type=ToolParameterType.STRING,
                    description="Bank transaction ID (UUID format)",
                    required=True,
                ),
                ToolParameter(
                    name="payment_id",
                    type=ToolParameterType.INTEGER,
                    description="Payment ID to match",
                    required=True,
                ),
                ToolParameter(
                    name="match_type",
                    type=ToolParameterType.STRING,
                    description="Type of match (default: manual)",
                    required=False,
                    enum=["manual", "exact", "fuzzy", "iban", "date_window"],
                    default="manual",
                ),
                ToolParameter(
                    name="confidence",
                    type=ToolParameterType.NUMBER,
                    description="Match confidence 0.0-1.0 (optional)",
                    required=False,
                ),
            ],
            func=reconcile_payment,
            requires_confirmation=True,
            examples=[
                "reconcile_payment(transaction_id='uuid-here', payment_id=123)",
                "reconcile_payment(transaction_id='uuid', payment_id=456, match_type='fuzzy', confidence=0.85)",
            ],
            tags=["write", "reconcile", "payment"],
        ),
        Tool(
            name="create_manual_payment",
            description="Manually create a payment record for an invoice. Used for manual payment tracking.",
            category="payments",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID",
                    required=True,
                ),
                ToolParameter(
                    name="importo",
                    type=ToolParameterType.NUMBER,
                    description="Total amount due",
                    required=True,
                ),
                ToolParameter(
                    name="data_scadenza",
                    type=ToolParameterType.STRING,
                    description="Due date (YYYY-MM-DD)",
                    required=True,
                ),
                ToolParameter(
                    name="importo_pagato",
                    type=ToolParameterType.NUMBER,
                    description="Amount already paid (default 0)",
                    required=False,
                    default=0.0,
                ),
                ToolParameter(
                    name="data_pagamento",
                    type=ToolParameterType.STRING,
                    description="Payment date if already paid (YYYY-MM-DD)",
                    required=False,
                ),
                ToolParameter(
                    name="modalita",
                    type=ToolParameterType.STRING,
                    description="Payment method (default 'bonifico')",
                    required=False,
                    default="bonifico",
                ),
            ],
            func=create_manual_payment,
            requires_confirmation=True,
            examples=[
                "create_manual_payment(fattura_id=123, importo=1000, data_scadenza='2025-02-15')",
                "create_manual_payment(fattura_id=456, importo=500, data_scadenza='2025-03-01', importo_pagato=500, data_pagamento='2025-01-20')",
            ],
            tags=["write", "create", "payment"],
        ),
        Tool(
            name="update_payment",
            description="Update payment record details (amount, dates, payment method). Automatically recalculates status.",
            category="payments",
            parameters=[
                ToolParameter(
                    name="payment_id",
                    type=ToolParameterType.INTEGER,
                    description="Payment ID",
                    required=True,
                ),
                ToolParameter(
                    name="importo",
                    type=ToolParameterType.NUMBER,
                    description="Total amount due",
                    required=False,
                ),
                ToolParameter(
                    name="importo_pagato",
                    type=ToolParameterType.NUMBER,
                    description="Amount paid",
                    required=False,
                ),
                ToolParameter(
                    name="data_scadenza",
                    type=ToolParameterType.STRING,
                    description="Due date (YYYY-MM-DD)",
                    required=False,
                ),
                ToolParameter(
                    name="data_pagamento",
                    type=ToolParameterType.STRING,
                    description="Payment date (YYYY-MM-DD)",
                    required=False,
                ),
                ToolParameter(
                    name="modalita",
                    type=ToolParameterType.STRING,
                    description="Payment method",
                    required=False,
                ),
            ],
            func=update_payment,
            requires_confirmation=True,
            examples=[
                "update_payment(payment_id=5, importo_pagato=500)",
                "update_payment(payment_id=10, data_pagamento='2025-01-25', modalita='contanti')",
            ],
            tags=["write", "update", "payment"],
        ),
        Tool(
            name="delete_payment",
            description="CRITICAL: Delete payment record from database. Cannot delete if linked to bank transactions.",
            category="payments",
            parameters=[
                ToolParameter(
                    name="payment_id",
                    type=ToolParameterType.INTEGER,
                    description="Payment ID to delete",
                    required=True,
                ),
            ],
            func=delete_payment,
            requires_confirmation=True,
            examples=["delete_payment(payment_id=5)"],
            tags=["write", "delete", "payment", "critical"],
        ),
        Tool(
            name="import_bank_transactions",
            description="Import bank transactions from OFX/QFX bank statement file for payment reconciliation.",
            category="payments",
            parameters=[
                ToolParameter(
                    name="file_path",
                    type=ToolParameterType.STRING,
                    description="Path to OFX/QFX bank statement file",
                    required=True,
                ),
                ToolParameter(
                    name="account_name",
                    type=ToolParameterType.STRING,
                    description="Bank account name (default 'Main Account')",
                    required=False,
                    default="Main Account",
                ),
            ],
            func=import_bank_transactions,
            requires_confirmation=True,
            examples=[
                "import_bank_transactions(file_path='/path/to/statement.ofx')",
                "import_bank_transactions(file_path='/path/to/statement.qfx', account_name='Business Account')",
            ],
            tags=["write", "import", "bank", "transaction"],
        ),
    ]
