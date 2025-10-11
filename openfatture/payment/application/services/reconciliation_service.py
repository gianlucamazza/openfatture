"""Reconciliation service for managing payment matching workflows.

Implements the Saga pattern to orchestrate complex, multi-step reconciliation processes
with proper state transitions and event handling.
"""

import asyncio
import inspect
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

import structlog
from sqlalchemy.orm import Session

from ...domain.enums import MatchType, TransactionStatus
from ...domain.models import BankTransaction
from ...domain.payment_allocation import PaymentAllocation
from ...domain.value_objects import MatchResult, ReconciliationResult
from ..events import EventBus, TransactionMatchedEvent, TransactionUnmatchedEvent

if TYPE_CHECKING:
    from ....storage.database.models import Pagamento
    from ...infrastructure.repository import (
        BankTransactionRepository,
        PaymentRepository,
    )
    from .matching_service import MatchingService

logger = structlog.get_logger()


class ReconciliationService:
    """Service for managing reconciliation workflows and state transitions.

    Design Pattern: Saga Pattern (orchestrates multi-step processes)
    SOLID Principle: Open/Closed (extensible reconciliation rules)

    This service manages the complete lifecycle of payment reconciliation:
    - Validation of reconciliation operations
    - State transitions (UNMATCHED → MATCHED → IGNORED)
    - Payment amount updates
    - Domain event emission
    - Rollback capabilities

    Example:
        >>> reconciliation_service = ReconciliationService(
        ...     tx_repo=BankTransactionRepository(session),
        ...     payment_repo=PaymentRepository(session),
        ...     matching_service=matching_service
        ... )
        >>> tx = await reconciliation_service.reconcile(
        ...     transaction_id=tx_id,
        ...     payment_id=payment_id,
        ...     match_type=MatchType.MANUAL
        ... )
        >>> print(f"Transaction {tx.id} matched to payment {tx.matched_payment_id}")
    """

    def __init__(
        self,
        tx_repo: "BankTransactionRepository",
        payment_repo: "PaymentRepository",
        matching_service: "MatchingService",
        session: Session | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize reconciliation service.

        Args:
            tx_repo: Repository for bank transactions
            payment_repo: Repository for payments
            matching_service: Service for matching operations
            session: Optional SQLAlchemy session for event emission
        """
        self.tx_repo = tx_repo
        self.payment_repo = payment_repo
        self.matching_service = matching_service
        self.session = session
        self.event_bus = event_bus

    async def reconcile(
        self,
        transaction_id: UUID,
        payment_id: int,
        match_type: MatchType = MatchType.MANUAL,
        confidence: float | None = None,
    ) -> BankTransaction:
        """Reconcile transaction to payment with validation.

        Workflow:
        1. Validate transaction exists and is UNMATCHED
        2. Validate payment exists and is not already fully paid
        3. Update transaction:
           - status = MATCHED
           - matched_payment_id, match_confidence, match_type
        4. Apply allocation to payment (supports partial payments)
        5. Persist allocation record for audit/rollback
        6. Emit domain event (TransactionMatched)
        7. Return updated transaction

        Args:
            transaction_id: Transaction UUID
            payment_id: Payment ID
            match_type: Type of match (MANUAL, EXACT, FUZZY, etc.)
            confidence: Optional confidence score (0.0-1.0)

        Returns:
            Updated BankTransaction

        Raises:
            ValueError: If validation fails
            RuntimeError: If reconciliation fails

        Example:
            >>> tx = await service.reconcile(
            ...     transaction_id=UUID("..."),
            ...     payment_id=123,
            ...     match_type=MatchType.MANUAL
            ... )
        """
        logger.info(
            "reconciliation_started",
            transaction_id=transaction_id,
            payment_id=payment_id,
            match_type=match_type.value,
        )

        # 1. Validate transaction
        transaction = self.tx_repo.get_by_id(transaction_id)
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")

        if transaction.status != TransactionStatus.UNMATCHED:
            raise ValueError(
                f"Transaction {transaction_id} cannot be reconciled. "
                f"Current status: {transaction.status.value}. "
                "Only UNMATCHED transactions can be reconciled."
            )

        # 2. Validate payment
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")

        # Determine outstanding amount
        outstanding = payment.saldo_residuo
        if outstanding <= Decimal("0.00"):
            raise ValueError(f"Payment {payment_id} is already fully paid.")

        transaction_amount = abs(transaction.amount)
        if transaction_amount <= Decimal("0.00"):
            raise ValueError(
                f"Transaction {transaction_id} has non-positive amount {transaction.amount}."
            )

        applied_amount = transaction_amount if transaction_amount <= outstanding else outstanding

        if transaction_amount > outstanding + Decimal("0.01"):
            logger.warning(
                "transaction_exceeds_outstanding",
                transaction_amount=float(transaction_amount),
                outstanding_amount=float(outstanding),
                applied_amount=float(applied_amount),
            )

        try:
            # 3. Update transaction
            transaction.status = TransactionStatus.MATCHED
            transaction.matched_payment_id = payment_id
            transaction.match_type = match_type
            transaction.match_confidence = confidence
            transaction.matched_at = datetime.now(UTC)

            # Persist partial payment state on payment entity
            payment.apply_payment(applied_amount, pagamento_effective_date=transaction.date)
            self.payment_repo.update(payment)

            # Track allocation for reversals/audit
            allocation = PaymentAllocation(
                payment_id=payment_id,
                transaction_id=transaction.id,
                amount=applied_amount,
                match_type=match_type,
                match_confidence=confidence,
            )
            self.payment_repo.add_allocation(allocation)

            # Update transaction metadata with allocation info
            if transaction.raw_data is None:
                transaction.raw_data = {}
            transaction.raw_data.setdefault("reconciliation", {})
            transaction.raw_data["reconciliation"].update(
                {
                    "applied_amount": float(applied_amount),
                    "payment_id": payment_id,
                    "outstanding_before": float(outstanding),
                }
            )

            self.tx_repo.update(transaction)

            # 5. Emit domain event (placeholder - implement event bus)
            self._emit_transaction_matched_event(transaction, payment, applied_amount)

            logger.info(
                "reconciliation_completed",
                transaction_id=transaction_id,
                payment_id=payment_id,
                amount=float(transaction.amount),
                applied_amount=float(applied_amount),
                payment_status=payment.stato.value,
                outstanding_after=float(payment.saldo_residuo),
            )

            return transaction

        except Exception as e:
            logger.error(
                "reconciliation_failed",
                transaction_id=transaction_id,
                payment_id=payment_id,
                error=str(e),
            )
            raise RuntimeError(f"Reconciliation failed: {e}") from e

    async def ignore_transaction(
        self,
        transaction_id: UUID,
        reason: str | None = None,
    ) -> BankTransaction:
        """Mark transaction as IGNORED (non-business transaction).

        Use cases:
        - Personal expenses
        - Bank fees
        - ATM withdrawals
        - Non-invoice-related transactions

        Args:
            transaction_id: Transaction UUID
            reason: Optional reason for ignoring

        Returns:
            Updated BankTransaction

        Raises:
            ValueError: If transaction not found or invalid state

        Example:
            >>> tx = await service.ignore_transaction(
            ...     transaction_id=UUID("..."),
            ...     reason="Personal expense"
            ... )
        """
        logger.info(
            "ignoring_transaction",
            transaction_id=transaction_id,
            reason=reason,
        )

        transaction = self.tx_repo.get_by_id(transaction_id)
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")

        if transaction.status == TransactionStatus.MATCHED:
            raise ValueError(
                f"Cannot ignore transaction {transaction_id}: already matched. "
                "Reset it first using reset_transaction()."
            )

        transaction.status = TransactionStatus.IGNORED
        # Store reason in raw_data
        if reason:
            if transaction.raw_data is None:
                transaction.raw_data = {}
            transaction.raw_data["ignore_reason"] = reason
            transaction.raw_data["ignored_at"] = datetime.now(UTC).isoformat()

        self.tx_repo.update(transaction)

        logger.info("transaction_ignored", transaction_id=transaction_id)

        return transaction

    async def reset_transaction(
        self,
        transaction_id: UUID,
    ) -> BankTransaction:
        """Reset transaction to UNMATCHED (undo reconciliation).

        Workflow:
        1. Validate transaction exists and is MATCHED
        2. Get linked payment and revert amounts
        3. Update transaction: status = UNMATCHED, clear match metadata
        4. Emit domain event (TransactionUnmatched)

        Args:
            transaction_id: Transaction UUID

        Returns:
            Updated BankTransaction

        Raises:
            ValueError: If transaction not found or not matched

        Example:
            >>> tx = await service.reset_transaction(UUID("..."))
        """
        logger.info("resetting_transaction", transaction_id=transaction_id)

        transaction = self.tx_repo.get_by_id(transaction_id)
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")

        if transaction.status != TransactionStatus.MATCHED:
            raise ValueError(
                f"Transaction {transaction_id} is not matched. "
                f"Current status: {transaction.status.value}"
            )

        try:
            # Get payment to revert status
            allocation: PaymentAllocation | None = None
            payment: Pagamento | None = None
            original_payment_id = transaction.matched_payment_id

            if original_payment_id:
                payment = self.payment_repo.get_by_id(original_payment_id)
                if payment:
                    allocation = self.payment_repo.get_allocation(payment.id, transaction.id)
                    if allocation:
                        payment.revert_payment(allocation.amount)
                        self.payment_repo.update(payment)
                        self.payment_repo.delete_allocation(allocation)
                        logger.debug(
                            "payment_status_reverted",
                            payment_id=payment.id,
                            reverted_amount=float(allocation.amount),
                            new_status=payment.stato.value,
                        )
                    else:
                        logger.warning(
                            "allocation_missing_on_reset",
                            transaction_id=transaction_id,
                            payment_id=payment.id,
                        )

            # Reset transaction
            transaction.status = TransactionStatus.UNMATCHED
            transaction.matched_payment_id = None
            transaction.match_type = None
            transaction.match_confidence = None
            transaction.matched_at = None

            self.tx_repo.update(transaction)

            # Emit event
            reverted_amount = allocation.amount if allocation else None
            self._emit_transaction_unmatched_event(
                transaction,
                reverted_amount,
                original_payment_id,
            )

            logger.info("transaction_reset", transaction_id=transaction_id)

            return transaction

        except Exception as e:
            logger.error(
                "reset_failed",
                transaction_id=transaction_id,
                error=str(e),
            )
            raise RuntimeError(f"Reset failed: {e}") from e

    async def get_review_queue(
        self,
        account_id: int | None = None,
        confidence_range: tuple[float, float] = (0.60, 0.84),
        limit: int | None = None,
    ) -> list[tuple[BankTransaction, list[MatchResult]]]:
        """Get transactions with suggested matches for manual review.

        Returns transactions that have medium-confidence matches requiring
        human review before reconciliation.

        Args:
            account_id: Optional account filter
            confidence_range: Tuple of (min_confidence, max_confidence)
            limit: Optional maximum number of results

        Returns:
            List of (transaction, match_suggestions) tuples

        Example:
            >>> queue = await service.get_review_queue(
            ...     account_id=1,
            ...     confidence_range=(0.60, 0.84)
            ... )
            >>> for tx, matches in queue:
            ...     print(f"{tx.description}: {len(matches)} suggestions")
        """
        logger.info(
            "fetching_review_queue",
            account_id=account_id,
            confidence_range=confidence_range,
        )

        # Get unmatched transactions
        unmatched = self.tx_repo.get_by_status(
            TransactionStatus.UNMATCHED, account_id=account_id, limit=limit
        )

        review_queue = []
        min_conf, max_conf = confidence_range

        for tx in unmatched:
            # Get matches for this transaction
            matches = await self.matching_service.match_transaction(
                tx, confidence_threshold=min_conf
            )

            # Filter by confidence range
            filtered_matches = [m for m in matches if min_conf <= m.confidence <= max_conf]

            if filtered_matches:
                review_queue.append((tx, filtered_matches))

        logger.info(
            "review_queue_fetched",
            total_transactions=len(unmatched),
            review_needed=len(review_queue),
        )

        return review_queue

    async def reconcile_batch(
        self,
        account_id: int,
        auto_apply: bool = True,
        auto_apply_threshold: float = 0.85,
    ) -> ReconciliationResult:
        """Batch reconciliation with auto-apply option.

        Workflow:
        1. Use MatchingService.match_batch() to get matches
        2. If auto_apply=True, reconcile high-confidence matches
        3. Return result with statistics

        Args:
            account_id: Account ID to reconcile
            auto_apply: Whether to auto-apply high-confidence matches
            auto_apply_threshold: Confidence threshold for auto-apply

        Returns:
            ReconciliationResult with statistics and details

        Example:
            >>> result = await service.reconcile_batch(
            ...     account_id=1,
            ...     auto_apply=True,
            ...     auto_apply_threshold=0.85
            ... )
            >>> print(f"Auto-reconciled: {result.matched_count}")
        """
        logger.info(
            "batch_reconciliation_started",
            account_id=account_id,
            auto_apply=auto_apply,
        )

        # Get matches from matching service
        result = await self.matching_service.match_batch(
            account_id=account_id,
            auto_apply_threshold=auto_apply_threshold,
        )

        if auto_apply:
            # Auto-reconcile high-confidence matches
            reconciled_count = 0
            errors = []

            for tx, matches in result.matches:
                if matches and matches[0].confidence >= auto_apply_threshold:
                    try:
                        await self.reconcile(
                            transaction_id=tx.id,
                            payment_id=matches[0].payment.id,
                            match_type=matches[0].match_type,
                            confidence=matches[0].confidence,
                        )
                        reconciled_count += 1
                    except Exception as e:
                        logger.error(
                            "auto_reconcile_failed",
                            transaction_id=tx.id,
                            error=str(e),
                        )
                        errors.append(f"Transaction {tx.id}: {e}")

            logger.info(
                "batch_reconciliation_completed",
                account_id=account_id,
                reconciled=reconciled_count,
                errors=len(errors),
            )

        return result

    def _emit_transaction_matched_event(
        self,
        transaction: BankTransaction,
        payment: "Pagamento",
        applied_amount: Decimal,
    ) -> None:
        """Emit TransactionMatched domain event.

        Args:
            transaction: Matched transaction
            payment: Associated payment

        Note:
            This is a placeholder. Implement with proper event bus.
        """
        # Placeholder for domain event emission
        logger.debug(
            "domain_event_emitted",
            event_type="TransactionMatched",
            transaction_id=transaction.id,
            payment_id=payment.id,
        )

        event = TransactionMatchedEvent(
            transaction_id=transaction.id,
            payment_id=payment.id,
            matched_amount=applied_amount,
            match_type=transaction.match_type or MatchType.MANUAL,
            confidence=transaction.match_confidence,
        )
        self._publish_event(event)

    def _emit_transaction_unmatched_event(
        self,
        transaction: BankTransaction,
        reverted_amount: Decimal | None,
        payment_id: int | None,
    ) -> None:
        """Emit TransactionUnmatched domain event.

        Args:
            transaction: Unmatched transaction
            reverted_amount: Amount reverted from payment
            payment_id: Original payment identifier
        """
        logger.debug(
            "domain_event_emitted",
            event_type="TransactionUnmatched",
            transaction_id=transaction.id,
        )

        event = TransactionUnmatchedEvent(
            transaction_id=transaction.id,
            payment_id=payment_id,
            reverted_amount=reverted_amount,
        )
        self._publish_event(event)

    def _publish_event(self, event: TransactionMatchedEvent | TransactionUnmatchedEvent) -> None:
        """Publish event via configured event bus."""
        if not self.event_bus:
            return

        try:
            result = cast(Any, self.event_bus.publish(event))
            if inspect.isawaitable(result):
                asyncio.ensure_future(result)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error(
                "event_publish_failed",
                event_type=event.__class__.__name__,
                error=str(exc),
            )

    def __repr__(self) -> str:
        """Human-readable string representation."""
        return f"<ReconciliationService(" f"matching_service={self.matching_service})>"
