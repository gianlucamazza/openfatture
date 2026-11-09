"""Tools for payment tracking and reconciliation operations."""

from typing import Any
from uuid import UUID

from pydantic import validate_call

from openfatture.payment.application.collection_api import (
    create_payment,
)
from openfatture.payment.application.collection_api import (
    delete_payment as delete_payment,
)
from openfatture.payment.application.collection_api import (
    update_payment as update_payment,
)
from openfatture.payment.domain.enums import MatchType
from openfatture.platform.logging import get_logger
from openfatture.platform.security import validate_integer_input
from openfatture.storage.database.base import get_session

create_manual_payment = create_payment

logger = get_logger(__name__)


# =============================================================================
# Payment Query Tools
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
    from openfatture.cli.lifespan import get_event_bus
    from openfatture.payment.application.services.reconciliation_service import (
        ReconciliationService,
    )
    from openfatture.payment.infrastructure.repository import (
        BankTransactionRepository,
        PaymentRepository,
    )
    from openfatture.platform.async_bridge import run_async

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

        # Note: GlobalEventBus and payment.EventBus have compatible interfaces at runtime
        # (both have publish() and subscribe() methods), but MyPy sees them as distinct
        # protocols due to different event type hierarchies (BaseEvent vs PaymentEvent).
        # This is safe because PaymentEvent inherits from BaseEvent.
        from typing import cast

        from openfatture.payment.application.events import EventBus as PaymentEventBus

        reconciliation_service = ReconciliationService(
            tx_repo=tx_repo,
            payment_repo=payment_repo,
            matching_service=matching_service,
            session=db,
            event_bus=cast(PaymentEventBus, event_bus) if event_bus else None,
        )

        # Perform reconciliation
        transaction = run_async(
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


# Backwards-compatible names route to the single collection application service.


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
    from pathlib import Path

    from openfatture.payment.domain.models import BankAccount, BankTransaction
    from openfatture.payment.infrastructure.importers.ofx_importer import OFXImporter
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

        # Parse the statement
        importer = OFXImporter(file)
        importer.validate_file()
        parsed = importer.parse(account)

        # Deduplicate against transactions already stored for this account,
        # using the bank reference (FITID) as the natural key.
        known_references = {
            reference
            for (reference,) in db.query(BankTransaction.reference)
            .filter(
                BankTransaction.account_id == account.id,
                BankTransaction.reference.is_not(None),
            )
            .all()
        }

        # OFXImporter builds every transaction against `account`, so they all
        # sit in account.transactions already. Drop the duplicates from that
        # collection and persist the rest in one batch: flushing per row while
        # later rows are still pending on the relationship makes SQLAlchemy
        # warn about cascading an append for an object not yet in the session.
        to_import = []
        skipped = 0
        for transaction in parsed:
            reference = transaction.reference
            if reference is not None and reference in known_references:
                skipped += 1
                account.transactions.remove(transaction)
                continue
            if reference is not None:
                known_references.add(reference)
            to_import.append(transaction)

        tx_repo = BankTransactionRepository(db)
        if to_import:
            tx_repo.add_batch(to_import)
        imported = len(to_import)

        db.commit()

        logger.info(
            "bank_transactions_imported",
            file_path=file_path,
            account_id=account.id,
            imported=imported,
            skipped=skipped,
        )

        return {
            "success": True,
            "account_id": account.id,
            "account_name": account.name,
            "file_path": str(file),
            "imported": imported,
            "skipped": skipped,
            "total_transactions": imported + skipped,
            "message": f"Imported {imported} transactions ({skipped} skipped as duplicates)",
        }

    except Exception as e:
        db.rollback()
        logger.error("import_bank_transactions_failed", error=str(e))
        return {"error": str(e)}
    finally:
        db.close()
