"""Composite matcher strategy combining multiple matching signals.

Implements a weighted scoring algorithm that combines:
- Amount similarity (40% weight)
- Date proximity (30% weight)
- Description similarity (30% weight)

This is the recommended default matcher for production use.
"""

from datetime import timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from rapidfuzz import fuzz

from ..domain.enums import MatchType
from ..domain.value_objects import MatchResult
from .base import IMatcherStrategy, payment_amount_for_matching

if TYPE_CHECKING:
    from ...storage.database.models import Pagamento
    from ..domain.models import BankTransaction


class CompositeMatcher(IMatcherStrategy):
    """Match transactions using weighted combination of multiple signals.

    This matcher combines:
    1. **Amount similarity (40% weight)**:
       - Exact match (within 1 cent) → 1.0
       - Within 1% → 0.95
       - Within 5% → 0.85
       - Within 10% → 0.70
       - > 10% → 0.0

    2. **Date proximity (30% weight)**:
       - Same date → 1.0
       - ±1 day → 0.95
       - ±3 days → 0.85
       - ±7 days → 0.70
       - ±14 days → 0.50
       - > 14 days → 0.0

    3. **Description similarity (30% weight)**:
       - Fuzzy string matching using Levenshtein distance
       - >= 95% → 1.0
       - >= 85% → 0.85
       - >= 75% → 0.70
       - >= 60% → 0.50
       - < 60% → 0.0

    Final confidence = (amount_score * 0.4) + (date_score * 0.3) + (desc_score * 0.3)

    Attributes:
        amount_weight: Weight for amount similarity (default 0.4)
        date_weight: Weight for date proximity (default 0.3)
        description_weight: Weight for description similarity (default 0.3)
        min_confidence: Minimum confidence threshold to return (default 0.6)
        date_tolerance_days: Maximum date difference to consider (default 30 days)

    Example:
        >>> matcher = CompositeMatcher()
        >>> results = matcher.match(transaction, payments)
        >>> best_match = max(results, key=lambda r: r.confidence)
        >>> print(f"Confidence: {best_match.confidence:.2f}")
    """

    def __init__(
        self,
        amount_weight: float = 0.4,
        date_weight: float = 0.3,
        description_weight: float = 0.3,
        min_confidence: float = 0.6,
        date_tolerance_days: int = 30,
    ) -> None:
        """Initialize composite matcher.

        Args:
            amount_weight: Weight for amount similarity (0.0-1.0)
            date_weight: Weight for date proximity (0.0-1.0)
            description_weight: Weight for description similarity (0.0-1.0)
            min_confidence: Minimum confidence to return a match
            date_tolerance_days: Maximum days difference to consider

        Raises:
            ValueError: If weights don't sum to 1.0
        """
        if abs((amount_weight + date_weight + description_weight) - 1.0) > 0.01:
            raise ValueError(
                f"Weights must sum to 1.0, got {amount_weight + date_weight + description_weight}"
            )

        self.amount_weight = amount_weight
        self.date_weight = date_weight
        self.description_weight = description_weight
        self.min_confidence = min_confidence
        self.date_tolerance_days = date_tolerance_days

    def match(
        self, transaction: "BankTransaction", payments: list["Pagamento"]
    ) -> list["MatchResult"]:
        """Match transaction using weighted composite scoring.

        Algorithm:
        1. Pre-filter by date (within tolerance)
        2. For each payment:
           a. Calculate amount score (0.0-1.0)
           b. Calculate date score (0.0-1.0)
           c. Calculate description score (0.0-1.0)
           d. Calculate weighted final score
        3. Filter by min_confidence
        4. Sort by confidence descending

        Args:
            transaction: Bank transaction to match
            payments: List of candidate payments

        Returns:
            List of matches with confidence >= min_confidence,
            sorted by confidence descending
        """
        results: list[MatchResult] = []

        # Pre-filter by date
        date_min = transaction.date - timedelta(days=self.date_tolerance_days)
        date_max = transaction.date + timedelta(days=self.date_tolerance_days)

        candidates = [p for p in payments if date_min <= p.data_scadenza <= date_max]

        for payment in candidates:
            # Calculate individual scores
            amount_score = self._calculate_amount_score(transaction, payment)
            date_score = self._calculate_date_score(transaction, payment)
            description_score = self._calculate_description_score(transaction, payment)

            # Calculate weighted confidence
            confidence = (
                (amount_score * self.amount_weight)
                + (date_score * self.date_weight)
                + (description_score * self.description_weight)
            )

            # Filter by minimum confidence
            if confidence < self.min_confidence:
                continue

            # Build match reason
            match_reason = self._build_match_reason(
                amount_score, date_score, description_score, confidence
            )

            # Identify matched fields
            matched_fields = []
            if amount_score >= 0.85:
                matched_fields.append("amount")
            if date_score >= 0.85:
                matched_fields.append("date")
            if description_score >= 0.85:
                matched_fields.append("description")

            # Calculate amount difference
            transaction_amount = abs(transaction.amount)
            payment_amount = payment_amount_for_matching(payment)
            amount_diff = abs(transaction_amount - payment_amount)

            results.append(
                MatchResult(
                    transaction=transaction,
                    payment=payment,
                    confidence=self._validate_confidence(confidence),
                    match_reason=match_reason,
                    match_type=MatchType.COMPOSITE,
                    matched_fields=matched_fields,
                    amount_diff=amount_diff,
                )
            )

        # Sort by confidence descending
        results.sort(key=lambda r: r.confidence, reverse=True)

        return results

    def _calculate_amount_score(
        self, transaction: "BankTransaction", payment: "Pagamento"
    ) -> float:
        """Calculate amount similarity score (0.0-1.0).

        Scoring:
        - Exact match (within 1 cent) → 1.0
        - Within 1% → 0.95
        - Within 5% → 0.85
        - Within 10% → 0.70
        - > 10% → 0.0

        Args:
            transaction: Bank transaction
            payment: Payment record

        Returns:
            Amount score (0.0-1.0)
        """
        transaction_amount = abs(transaction.amount)
        payment_amount = payment_amount_for_matching(payment)
        amount_diff = abs(transaction_amount - payment_amount)

        if payment_amount == 0:
            return 0.0

        # Exact match (within 1 cent)
        if amount_diff <= Decimal("0.01"):
            return 1.0

        # Calculate percentage difference
        pct_diff = float(amount_diff / payment_amount * 100)

        if pct_diff <= 1.0:
            return 0.95
        elif pct_diff <= 5.0:
            return 0.85
        elif pct_diff <= 10.0:
            return 0.70
        else:
            return 0.0

    def _calculate_date_score(self, transaction: "BankTransaction", payment: "Pagamento") -> float:
        """Calculate date proximity score (0.0-1.0).

        Scoring:
        - Same date → 1.0
        - ±1 day → 0.95
        - ±3 days → 0.85
        - ±7 days → 0.70
        - ±14 days → 0.50
        - > 14 days → 0.0

        Args:
            transaction: Bank transaction
            payment: Payment record

        Returns:
            Date score (0.0-1.0)
        """
        date_diff_days = abs((payment.data_scadenza - transaction.date).days)

        if date_diff_days == 0:
            return 1.0
        elif date_diff_days <= 1:
            return 0.95
        elif date_diff_days <= 3:
            return 0.85
        elif date_diff_days <= 7:
            return 0.70
        elif date_diff_days <= 14:
            return 0.50
        else:
            return 0.0

    def _calculate_description_score(
        self, transaction: "BankTransaction", payment: "Pagamento"
    ) -> float:
        """Calculate description similarity score using fuzzy matching.

        Scoring:
        - >= 95% similarity → 1.0
        - >= 85% similarity → 0.85
        - >= 75% similarity → 0.70
        - >= 60% similarity → 0.50
        - < 60% similarity → 0.0

        Args:
            transaction: Bank transaction
            payment: Payment record

        Returns:
            Description score (0.0-1.0)
        """
        # Normalize descriptions
        trans_desc = self._normalize_text(transaction.description)
        trans_ref = self._normalize_text(transaction.reference or "")

        # For payment, we'd ideally join with Fattura to get description
        # Simplified: use payment amount as identifier
        payment_amount = payment_amount_for_matching(payment)
        payment_text = self._normalize_text(str(payment_amount))

        # Calculate similarity scores
        desc_similarity = fuzz.ratio(trans_desc, payment_text) if trans_desc else 0
        ref_similarity = fuzz.ratio(trans_ref, payment_text) if trans_ref else 0

        # Take best similarity
        max_similarity = max(desc_similarity, ref_similarity)

        # Convert to score
        if max_similarity >= 95:
            return 1.0
        elif max_similarity >= 85:
            return 0.85
        elif max_similarity >= 75:
            return 0.70
        elif max_similarity >= 60:
            return 0.50
        else:
            return 0.0

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison (lowercase, strip whitespace).

        Args:
            text: Raw text

        Returns:
            Normalized text
        """
        if not text:
            return ""
        return text.lower().strip()

    def _build_match_reason(
        self,
        amount_score: float,
        date_score: float,
        description_score: float,
        confidence: float,
    ) -> str:
        """Build human-readable match reason.

        Args:
            amount_score: Amount similarity score
            date_score: Date proximity score
            description_score: Description similarity score
            confidence: Final weighted confidence

        Returns:
            Match reason string
        """
        components = []

        if amount_score >= 0.85:
            components.append(f"amount {amount_score:.0%}")
        if date_score >= 0.85:
            components.append(f"date {date_score:.0%}")
        if description_score >= 0.85:
            components.append(f"desc {description_score:.0%}")

        if components:
            return f"Composite match ({', '.join(components)}) → {confidence:.0%}"
        else:
            return f"Composite match: {confidence:.0%} weighted score"

    def __repr__(self) -> str:
        """Human-readable string representation."""
        return (
            f"<CompositeMatcher("
            f"weights=[amt:{self.amount_weight:.0%}, "
            f"date:{self.date_weight:.0%}, "
            f"desc:{self.description_weight:.0%}], "
            f"min_confidence={self.min_confidence:.0%})>"
        )
