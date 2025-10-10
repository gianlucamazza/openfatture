"""Matching service for coordinating transaction-to-payment matching strategies.

Implements the Facade and Strategy patterns to provide a unified interface for matching
bank transactions to payments using multiple algorithms and optional AI enrichment.
"""

import asyncio
from datetime import date, timedelta
from dataclasses import replace
from typing import TYPE_CHECKING, Optional
from uuid import UUID

import structlog

from ...domain.enums import MatchType, TransactionStatus
from ...domain.models import BankTransaction
from ...domain.value_objects import MatchResult, PaymentInsight, ReconciliationResult
from ...matchers.base import IMatcherStrategy

if TYPE_CHECKING:
    from ...domain.models import BankAccount
    from ...infrastructure.repository import BankTransactionRepository, PaymentRepository
    from ....storage.database.models import Pagamento
    from .insight_service import TransactionInsightService

logger = structlog.get_logger()


class MatchingService:
    """Service for coordinating transaction matching strategies.

    Design Pattern: Facade + Strategy
    SOLID Principle: Single Responsibility (matching coordination only)

    This service orchestrates multiple matching strategies to find the best matches
    between bank transactions and payments. It provides both single transaction matching
    and batch matching with parallelization.

    Example:
        >>> matching_service = MatchingService(
        ...     tx_repo=BankTransactionRepository(session),
        ...     payment_repo=PaymentRepository(session),
        ...     strategies=[ExactAmountMatcher(), CompositeMatcher()]
        ... )
        >>> matches = await matching_service.match_transaction(transaction)
        >>> print(f"Found {len(matches)} matches")
    """

    def __init__(
        self,
        tx_repo: "BankTransactionRepository",
        payment_repo: "PaymentRepository",
        strategies: list[IMatcherStrategy],
        insight_service: Optional["TransactionInsightService"] = None,
    ) -> None:
        """Initialize matching service with repositories and strategies.

        Args:
            tx_repo: Repository for bank transactions
            payment_repo: Repository for payments
            strategies: List of matching strategies to apply (in order)
        """
        self.tx_repo = tx_repo
        self.payment_repo = payment_repo
        self.strategies = strategies
        self.insight_service = insight_service

    async def match_transaction(
        self,
        transaction: BankTransaction,
        confidence_threshold: float = 0.60,
        date_window_days: int = 30,
    ) -> list[MatchResult]:
        """Match single transaction using configured strategies.

        Algorithm:
        1. Get candidate payments (date window ±30 days)
        2. Apply each strategy sequentially
        3. Merge and deduplicate results (by payment_id)
        4. Filter by confidence threshold
        5. Sort by confidence DESC
        6. Return top matches

        Args:
            transaction: Bank transaction to match
            confidence_threshold: Minimum confidence score (0.0-1.0)
            date_window_days: Days to search before/after transaction date

        Returns:
            List of MatchResult sorted by confidence (highest first)

        Example:
            >>> matches = await service.match_transaction(tx, confidence_threshold=0.75)
            >>> if matches and matches[0].should_auto_apply:
            ...     # Auto-apply high confidence match
            ...     reconcile(tx.id, matches[0].payment.id)
        """
        logger.info(
            "matching_transaction",
            transaction_id=transaction.id,
            amount=float(transaction.amount),
            date=transaction.date.isoformat(),
        )

        # 1. Get candidate payments (date window)
        candidates = await self._get_candidate_payments(transaction, date_window_days)

        if not candidates:
            logger.debug(
                "no_candidate_payments",
                transaction_id=transaction.id,
                date_window_days=date_window_days,
            )
            return []

        # 2. Apply each strategy
        all_matches: dict[int, MatchResult] = {}  # payment_id → best match

        for strategy in self.strategies:
            try:
                strategy_matches = strategy.match(transaction, candidates)

                # Merge results (keep highest confidence per payment)
                for match in strategy_matches:
                    payment_id = match.payment.id
                    if (
                        payment_id not in all_matches
                        or match.confidence > all_matches[payment_id].confidence
                    ):
                        all_matches[payment_id] = match

            except Exception as e:
                logger.error(
                    "strategy_failed",
                    strategy=strategy.__class__.__name__,
                    error=str(e),
                    transaction_id=transaction.id,
                )
                continue

        # 3. Filter by threshold and sort
        filtered_matches = [m for m in all_matches.values() if m.confidence >= confidence_threshold]

        filtered_matches.sort(key=lambda m: m.confidence, reverse=True)

        # 4. Optionally enrich results with AI insight
        if self.insight_service and filtered_matches:
            try:
                insight = await self.insight_service.analyze(transaction, candidates)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning(
                    "matching_insight_failed",
                    transaction_id=transaction.id,
                    error=str(exc),
                )
                insight = None

            if insight:
                filtered_matches = self._apply_ai_insight(transaction, filtered_matches, insight)

                if transaction.raw_data is None:
                    transaction.raw_data = {}
                transaction.raw_data["ai_insight"] = insight.to_dict()

        logger.info(
            "matching_completed",
            transaction_id=transaction.id,
            total_matches=len(filtered_matches),
            top_confidence=filtered_matches[0].confidence if filtered_matches else 0.0,
        )

        return filtered_matches

    async def match_batch(
        self,
        account_id: int | None = None,
        auto_apply_threshold: float = 0.85,
        max_workers: int = 4,
    ) -> ReconciliationResult:
        """Batch match all unmatched transactions with parallelization.

        Algorithm:
        1. Get all UNMATCHED transactions (filtered by account if specified)
        2. Parallel matching using asyncio.gather (up to max_workers)
        3. Categorize results:
           - High confidence (>= auto_apply_threshold): Ready for auto-apply
           - Medium confidence (0.60-0.84): Needs review
           - Low confidence (< 0.60): Unmatched
        4. Return reconciliation result with statistics

        Args:
            account_id: Optional account filter (None = all accounts)
            auto_apply_threshold: Confidence threshold for auto-apply
            max_workers: Maximum parallel workers (default: 4)

        Returns:
            ReconciliationResult with match statistics and transactions

        Example:
            >>> result = await service.match_batch(account_id=1, auto_apply_threshold=0.85)
            >>> print(f"Auto-apply: {result.matched_count}")
            >>> print(f"Review needed: {result.review_count}")
        """
        logger.info(
            "batch_matching_started",
            account_id=account_id,
            auto_apply_threshold=auto_apply_threshold,
        )

        # 1. Get unmatched transactions
        unmatched = self.tx_repo.get_by_status(TransactionStatus.UNMATCHED, account_id=account_id)

        if not unmatched:
            logger.info("no_unmatched_transactions", account_id=account_id)
            return ReconciliationResult(
                matched_count=0,
                review_count=0,
                unmatched_count=0,
                total_count=0,
                matches=[],
            )

        # 2. Parallel matching with semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_workers)

        async def match_with_limit(
            tx: BankTransaction,
        ) -> tuple[BankTransaction, list[MatchResult]]:
            async with semaphore:
                matches = await self.match_transaction(tx)
                return tx, matches

        # Execute parallel matching
        results = await asyncio.gather(*[match_with_limit(tx) for tx in unmatched])

        # 3. Categorize results
        high_confidence = []  # >= auto_apply_threshold
        medium_confidence = []  # 0.60 - auto_apply_threshold
        low_confidence = []  # < 0.60

        for tx, matches in results:
            if not matches:
                low_confidence.append((tx, []))
            elif matches[0].confidence >= auto_apply_threshold:
                high_confidence.append((tx, matches))
            elif matches[0].confidence >= 0.60:
                medium_confidence.append((tx, matches))
            else:
                low_confidence.append((tx, matches))

        # 4. Build result
        result = ReconciliationResult(
            matched_count=len(high_confidence),
            review_count=len(medium_confidence),
            unmatched_count=len(low_confidence),
            total_count=len(unmatched),
            matches=high_confidence + medium_confidence,  # High confidence first
        )

        logger.info(
            "batch_matching_completed",
            total=result.total_count,
            matched=result.matched_count,
            review=result.review_count,
            unmatched=result.unmatched_count,
        )

        return result

    async def suggest_matches(
        self,
        transaction_id: UUID,
        limit: int = 5,
    ) -> list[MatchResult]:
        """Get top match suggestions for manual review.

        Args:
            transaction_id: Transaction UUID
            limit: Maximum number of suggestions (default: 5)

        Returns:
            List of top MatchResult suggestions

        Raises:
            ValueError: If transaction not found
        """
        transaction = self.tx_repo.get_by_id(transaction_id)
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")

        matches = await self.match_transaction(transaction, confidence_threshold=0.30)

        return matches[:limit]

    async def _get_candidate_payments(
        self,
        transaction: BankTransaction,
        date_window_days: int = 30,
    ) -> list["Pagamento"]:
        """Get candidate payments within date window.

        Args:
            transaction: Bank transaction
            date_window_days: Days before/after transaction date

        Returns:
            List of candidate payments (unpaid or partially paid)
        """
        date_from = transaction.date - timedelta(days=date_window_days)
        date_to = transaction.date + timedelta(days=date_window_days)

        # Get unpaid payments in date range
        candidates = self.payment_repo.get_unpaid(date_from=date_from, date_to=date_to)

        logger.debug(
            "candidate_payments_retrieved",
            transaction_id=transaction.id,
            count=len(candidates),
            date_from=date_from.isoformat(),
            date_to=date_to.isoformat(),
        )

        return candidates

    def add_strategy(self, strategy: IMatcherStrategy) -> None:
        """Add a new matching strategy to the pipeline.

        Args:
            strategy: Matcher strategy to add

        Example:
            >>> service.add_strategy(CustomInvoiceNumberMatcher())
        """
        self.strategies.append(strategy)
        logger.info("strategy_added", strategy=strategy.__class__.__name__)

    def remove_strategy(self, strategy_class: type[IMatcherStrategy]) -> bool:
        """Remove a strategy by class type.

        Args:
            strategy_class: Class of strategy to remove

        Returns:
            True if removed, False if not found
        """
        before_count = len(self.strategies)
        self.strategies = [s for s in self.strategies if not isinstance(s, strategy_class)]
        removed = len(self.strategies) < before_count

        if removed:
            logger.info("strategy_removed", strategy=strategy_class.__name__)

        return removed

    def _apply_ai_insight(
        self,
        transaction: BankTransaction,
        matches: list[MatchResult],
        insight: PaymentInsight,
    ) -> list[MatchResult]:
        """Boost or annotate matches with information coming from AI insight."""

        enriched: list[MatchResult] = []

        invoice_numbers = set(insight.probable_invoice_numbers)
        for match in matches:
            boost = 0.0
            reason_tags: list[str] = []

            invoice_number = None
            if hasattr(match.payment, "fattura") and match.payment.fattura is not None:
                invoice_number = getattr(match.payment.fattura, "numero", None)

            if invoice_numbers and invoice_number and invoice_number in invoice_numbers:
                boost += 0.05
                reason_tags.append(f"AI invoice match {invoice_number}")

            if insight.is_partial_payment:
                reason_tags.append("AI partial payment")

            if boost or reason_tags:
                new_confidence = min(1.0, match.confidence + boost)
                new_reason = match.match_reason
                if reason_tags:
                    new_reason = f"{new_reason} [{' | '.join(reason_tags)}]"
                enriched.append(
                    replace(
                        match,
                        confidence=self._clamp_confidence(new_confidence),
                        match_reason=new_reason,
                    )
                )
            else:
                enriched.append(match)

        enriched.sort(key=lambda m: m.confidence, reverse=True)
        return enriched

    def _clamp_confidence(self, confidence: float) -> float:
        """Ensure confidence remains within [0.0, 1.0]."""

        if confidence < 0.0:
            return 0.0
        if confidence > 1.0:
            return 1.0
        return confidence

    def __repr__(self) -> str:
        """Human-readable string representation."""
        strategy_names = [s.__class__.__name__ for s in self.strategies]
        return f"<MatchingService(strategies=[{', '.join(strategy_names)}])>"
