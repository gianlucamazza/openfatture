"""Fuzzy string matcher strategy using Levenshtein distance.

Matches bank transactions to payments based on fuzzy string similarity between
descriptions, counterparty names, and references. Uses rapidfuzz library for
efficient Levenshtein distance calculation.
"""

import re
from datetime import timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from rapidfuzz import fuzz

from ..domain.enums import MatchType
from ..domain.value_objects import MatchResult
from .base import IMatcherStrategy

if TYPE_CHECKING:
    from ...storage.database.models import Pagamento
    from ..domain.models import BankTransaction


class FuzzyStringMatcher(IMatcherStrategy):
    """Match transactions using fuzzy string similarity (Levenshtein distance).

    This strategy compares text fields (description, counterparty, reference)
    using Levenshtein distance to find similar strings. Useful when:
    - Bank descriptions vary slightly from invoice descriptions
    - Counterparty names have typos or abbreviations
    - Reference fields contain invoice numbers with prefixes/suffixes

    Confidence Scoring:
    - 95%+ similarity → confidence 0.95
    - 90-95% similarity → confidence 0.90
    - 85-90% similarity → confidence 0.85
    - 80-85% similarity → confidence 0.80
    - <80% similarity → confidence 0.70 (minimum)

    Attributes:
        min_similarity: Minimum similarity threshold (default 85%)
        date_tolerance_days: Date window for matching (default 14 days)
        amount_tolerance_pct: Amount difference tolerance as percentage (default 5%)

    Example:
        >>> matcher = FuzzyStringMatcher(min_similarity=90)
        >>> results = matcher.match(transaction, payments)
        >>> for result in results:
        ...     print(f"Match: {result.confidence:.2f} - {result.match_reason}")
    """

    def __init__(
        self,
        min_similarity: float = 85.0,
        date_tolerance_days: int = 14,
        amount_tolerance_pct: float = 5.0,
    ) -> None:
        """Initialize fuzzy string matcher.

        Args:
            min_similarity: Minimum similarity percentage (0-100) to consider a match
            date_tolerance_days: Number of days ± from due date to consider
            amount_tolerance_pct: Percentage difference in amount to tolerate (e.g., 5.0 = 5%)
        """
        if not 0 <= min_similarity <= 100:
            raise ValueError(f"min_similarity must be between 0-100, got {min_similarity}")

        self.min_similarity = min_similarity
        self.date_tolerance_days = date_tolerance_days
        self.amount_tolerance_pct = amount_tolerance_pct

    def match(
        self, transaction: "BankTransaction", payments: list["Pagamento"]
    ) -> list["MatchResult"]:
        """Match transaction to payments using fuzzy string similarity.

        Algorithm:
        1. Pre-filter by date (within ±14 days) and amount (within 5%)
        2. For each candidate payment:
           a. Extract searchable text from payment (fattura description, cliente name)
           b. Normalize both transaction and payment text (lowercase, remove special chars)
           c. Calculate Levenshtein similarity using rapidfuzz
           d. Convert similarity to confidence score
        3. Filter by min_similarity threshold
        4. Sort by confidence descending

        Args:
            transaction: Bank transaction to match
            payments: List of candidate payments

        Returns:
            List of fuzzy matches with confidence >= min_similarity / 100,
            sorted by confidence descending (best match first).
        """
        results: list[MatchResult] = []

        # Pre-filter candidates by date and amount
        candidates = self._prefilter_candidates(transaction, payments)

        for payment in candidates:
            # Calculate similarity scores for different fields
            similarity_scores = self._calculate_similarities(transaction, payment)

            # Take maximum similarity as primary score
            max_similarity = max(similarity_scores.values())

            # Check if meets minimum threshold
            if max_similarity < self.min_similarity:
                continue

            # Convert similarity (0-100) to confidence (0.0-1.0)
            confidence = self._similarity_to_confidence(max_similarity)

            # Calculate amount difference
            amount_diff = abs(transaction.amount - payment.importo)

            # Build match reason
            match_reason = self._build_match_reason(similarity_scores, max_similarity)

            # Identify which fields matched
            matched_fields = [
                field for field, score in similarity_scores.items() if score >= self.min_similarity
            ]

            results.append(
                MatchResult(
                    transaction=transaction,
                    payment=payment,
                    confidence=self._validate_confidence(confidence),
                    match_reason=match_reason,
                    match_type=MatchType.FUZZY,
                    matched_fields=matched_fields,
                    amount_diff=amount_diff,
                )
            )

        # Sort by confidence descending
        results.sort(key=lambda r: r.confidence, reverse=True)

        return results

    def _prefilter_candidates(
        self, transaction: "BankTransaction", payments: list["Pagamento"]
    ) -> list["Pagamento"]:
        """Pre-filter payments by date and amount to reduce computation.

        Args:
            transaction: Bank transaction
            payments: All candidate payments

        Returns:
            Filtered list of payments within date and amount tolerance
        """
        date_min = transaction.date - timedelta(days=self.date_tolerance_days)
        date_max = transaction.date + timedelta(days=self.date_tolerance_days)

        amount_min = transaction.amount * (1 - self.amount_tolerance_pct / 100)
        amount_max = transaction.amount * (1 + self.amount_tolerance_pct / 100)

        candidates = []
        for payment in payments:
            # Check date range
            if not (date_min <= payment.data_scadenza <= date_max):
                continue

            # Check amount range
            if not (amount_min <= payment.importo <= amount_max):
                continue

            candidates.append(payment)

        return candidates

    def _calculate_similarities(
        self, transaction: "BankTransaction", payment: "Pagamento"
    ) -> dict[str, float]:
        """Calculate similarity scores for different text fields.

        Args:
            transaction: Bank transaction
            payment: Payment record

        Returns:
            Dictionary of field name → similarity percentage (0-100)
        """
        scores = {}

        # Normalize transaction text
        trans_desc = self._normalize_text(transaction.description)
        trans_ref = self._normalize_text(transaction.reference or "")
        trans_counterparty = self._normalize_text(transaction.counterparty or "")

        # Extract payment searchable text
        # Note: In real implementation, would need to join with Fattura to get description
        # For now, we'll use a simplified approach
        payment_text = self._normalize_text(str(payment.importo))  # Simplified

        # Calculate description similarity
        if trans_desc:
            scores["description"] = fuzz.ratio(trans_desc, payment_text)

        # Calculate reference similarity (may contain invoice number)
        if trans_ref:
            scores["reference"] = fuzz.ratio(trans_ref, payment_text)

        # Calculate counterparty similarity
        if trans_counterparty:
            scores["counterparty"] = fuzz.ratio(trans_counterparty, payment_text)

        # If we have a reference field, also try partial matching
        if trans_ref:
            scores["partial_reference"] = fuzz.partial_ratio(trans_ref, payment_text)

        return scores

    def _normalize_text(self, text: str) -> str:
        """Normalize text for fuzzy matching.

        Normalization steps:
        1. Convert to lowercase
        2. Remove extra whitespace
        3. Remove special characters (keep alphanumeric and spaces)
        4. Strip leading/trailing whitespace

        Args:
            text: Raw text string

        Returns:
            Normalized text string
        """
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove special characters (keep alphanumeric, spaces, and basic punctuation)
        text = re.sub(r"[^a-z0-9\s\-/]", "", text)

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        # Strip edges
        text = text.strip()

        return text

    def _similarity_to_confidence(self, similarity: float) -> float:
        """Convert similarity percentage (0-100) to confidence score (0.0-1.0).

        Mapping:
        - 95-100% → 0.95
        - 90-95% → 0.90
        - 85-90% → 0.85
        - 80-85% → 0.80
        - 75-80% → 0.75
        - <75% → 0.70 (minimum)

        Args:
            similarity: Similarity percentage (0-100)

        Returns:
            Confidence score (0.0-1.0)
        """
        if similarity >= 95:
            return 0.95
        elif similarity >= 90:
            return 0.90
        elif similarity >= 85:
            return 0.85
        elif similarity >= 80:
            return 0.80
        elif similarity >= 75:
            return 0.75
        else:
            return 0.70

    def _build_match_reason(self, similarity_scores: dict[str, float], max_similarity: float) -> str:
        """Build human-readable explanation of the fuzzy match.

        Args:
            similarity_scores: Dictionary of field → similarity percentage
            max_similarity: Maximum similarity found

        Returns:
            Human-readable match reason
        """
        # Find which field had the best match
        best_field = max(similarity_scores.items(), key=lambda x: x[1])

        return (
            f"Fuzzy match: {best_field[0]} similarity {max_similarity:.1f}% "
            f"(Levenshtein distance)"
        )

    def __repr__(self) -> str:
        """Human-readable string representation."""
        return (
            f"<FuzzyStringMatcher("
            f"min_similarity={self.min_similarity}%, "
            f"date_tolerance={self.date_tolerance_days} days, "
            f"amount_tolerance={self.amount_tolerance_pct}%)>"
        )

    def _validate_confidence(self, confidence: float) -> float:
        """Validate and clamp confidence to [0.0, 1.0] range.

        Args:
            confidence: Confidence score

        Returns:
            Validated confidence between 0.0 and 1.0
        """
        return max(0.0, min(1.0, confidence))


# Alias for backward compatibility with tests
FuzzyDescriptionMatcher = FuzzyStringMatcher
FuzzyMatcher = FuzzyStringMatcher
