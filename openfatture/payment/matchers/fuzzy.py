"""Fuzzy description matcher strategy using Levenshtein distance.

Matches bank transactions to payments based on fuzzy similarity between
descriptions, counterparty names, and references. Uses rapidfuzz for efficient
Levenshtein distance calculations.

Performance Optimizations (v2.0):
- Early termination for high-confidence matches (≥95% similarity)
- Mock object handling for test compatibility
- Short-circuit evaluation for partial matching
"""

import re
from collections.abc import Callable
from datetime import timedelta
from typing import TYPE_CHECKING

from rapidfuzz import fuzz

from ..domain.enums import MatchType
from ..domain.value_objects import MatchResult
from .base import IMatcherStrategy, as_match_results, payment_amount_for_matching

if TYPE_CHECKING:
    from ...storage.database.models import Pagamento
    from ..domain.models import BankTransaction


class FuzzyDescriptionMatcher(IMatcherStrategy):
    """Match transactions using fuzzy text similarity (Levenshtein distance).

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
        >>> matcher = FuzzyDescriptionMatcher(min_similarity=90)
        >>> results = matcher.match(transaction, payments)
        >>> for result in results:
        ...     print(f"Match: {result.confidence:.2f} - {result.match_reason}")
    """

    def __init__(
        self,
        min_similarity: float = 85.0,
        date_tolerance_days: int = 14,
        amount_tolerance_pct: float = 5.0,
        early_stop_threshold: float = 95.0,
    ) -> None:
        """Initialize fuzzy string matcher with performance optimizations.

        Args:
            min_similarity: Minimum similarity percentage (0-100) to consider a match
            date_tolerance_days: Number of days ± from due date to consider
            amount_tolerance_pct: Percentage difference in amount to tolerate (e.g., 5.0 = 5%)
            early_stop_threshold: Similarity threshold for early termination (default 95.0)
                                 Set to 100.0 to disable early stopping
        """
        if not 0 <= min_similarity <= 100:
            raise ValueError(f"min_similarity must be between 0-100, got {min_similarity}")

        self.min_similarity = min_similarity
        self.date_tolerance_days = date_tolerance_days
        self.amount_tolerance_pct = amount_tolerance_pct
        self.early_stop_threshold = early_stop_threshold

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

            if not similarity_scores:
                continue

            # Take maximum similarity as primary score
            max_similarity = max(similarity_scores.values())

            # Check if meets minimum threshold
            if max_similarity < self.min_similarity:
                continue

            # Convert similarity (0-100) to confidence (0.0-1.0)
            confidence = self._validate_confidence(self._similarity_to_confidence(max_similarity))

            # Calculate amount difference
            transaction_amount = abs(transaction.amount)
            payment_amount = payment_amount_for_matching(payment)
            amount_diff = abs(transaction_amount - payment_amount)

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
                    confidence=confidence,
                    match_reason=match_reason,
                    match_type=MatchType.FUZZY,
                    matched_fields=matched_fields,
                    amount_diff=amount_diff,
                )
            )

        # Sort by confidence descending
        results.sort(key=lambda r: r.confidence, reverse=True)

        return as_match_results(results)

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

        from decimal import Decimal as Dec

        transaction_amount = abs(transaction.amount)
        tolerance_factor = Dec(str(self.amount_tolerance_pct)) / Dec("100")
        amount_min = transaction_amount * (Dec("1") - tolerance_factor)
        amount_max = transaction_amount * (Dec("1") + tolerance_factor)

        candidates = []
        for payment in payments:
            # Check date range
            if not (date_min <= payment.data_scadenza <= date_max):
                continue

            # Check amount range
            payment_amount = payment_amount_for_matching(payment)
            if not (amount_min <= payment_amount <= amount_max):
                continue

            candidates.append(payment)

        return candidates

    def _calculate_similarities(
        self, transaction: "BankTransaction", payment: "Pagamento"
    ) -> dict[str, float]:
        """Calculate similarity scores for different text fields.

        Implements early termination when high-confidence match is found.

        Args:
            transaction: Bank transaction
            payment: Payment record

        Returns:
            Dictionary of field name → similarity percentage (0-100)
        """
        scores: dict[str, float] = {}

        # Safely extract transaction attributes (handle Mock objects in tests)
        def safe_get_text(obj, attr: str) -> str:
            val = getattr(obj, attr, None)
            if val and not hasattr(val, "_mock_name"):
                return self._normalize_text(str(val))
            return ""

        trans_desc = safe_get_text(transaction, "description")
        trans_ref = safe_get_text(transaction, "reference")
        trans_counterparty = safe_get_text(transaction, "counterparty")

        payment_targets = self._collect_payment_texts(payment)
        if not payment_targets:
            payment_targets = [self._normalize_text(str(payment_amount_for_matching(payment)))]
        # Keep all payment texts
        payment_targets = [t for t in payment_targets if t]
        targets = payment_targets.copy()
        combined_payment_text = " ".join(payment_targets).strip()
        if combined_payment_text:
            targets.append(combined_payment_text)

        if not targets:
            return scores

        def best_similarity(source: str, scorer: Callable[[str, str], float] = fuzz.ratio) -> float:
            """Get best similarity score across all targets."""
            if not source or not targets:
                return 0.0

            max_score = 0.0
            for target in targets:
                score = scorer(source, target)
                max_score = max(max_score, score)

                # Early termination: if we found a near-perfect match, stop
                if score >= self.early_stop_threshold:
                    return score

            return max_score

        # Calculate description similarity
        if trans_desc:
            desc_score = best_similarity(trans_desc)
            scores["description"] = desc_score

            # Only compute partial ratio if exact ratio isn't already excellent
            if desc_score < 90.0:
                partial_description = best_similarity(trans_desc, scorer=fuzz.partial_ratio)
                scores["description_partial"] = partial_description * 0.85

        # Calculate reference similarity
        if trans_ref:
            ref_score = best_similarity(trans_ref)
            scores["reference"] = ref_score

            if ref_score < 90.0:
                partial_reference = best_similarity(trans_ref, scorer=fuzz.partial_ratio)
                scores["reference_partial"] = partial_reference * 0.85

        # Calculate counterparty similarity
        if trans_counterparty:
            scores["counterparty"] = best_similarity(trans_counterparty)

        # Combined similarity (only if not already found excellent match)
        if trans_desc and combined_payment_text and max(scores.values(), default=0.0) < 90.0:
            combined_score = fuzz.ratio(trans_desc, combined_payment_text)
            scores.setdefault("combined", combined_score)

        return scores

    def _collect_payment_texts(self, payment: "Pagamento") -> list[str]:
        """Collect normalized textual representations from payment and related entities."""
        texts: list[str] = []

        def add_text(value: str | None) -> None:
            # Skip None and Mock objects (tests may have MagicMock as unset attributes)
            if value and not hasattr(value, "_mock_name"):
                normalized = self._normalize_text(str(value))
                if normalized:
                    texts.append(normalized)

        add_text(getattr(payment, "description", None))
        add_text(getattr(payment, "descrizione", None))
        add_text(getattr(payment, "reference", None))
        add_text(getattr(payment, "riferimento", None))
        add_text(getattr(payment, "memo", None))
        add_text(getattr(payment, "note", None))

        fattura = getattr(payment, "fattura", None)
        if fattura:
            add_text(getattr(fattura, "numero", None))
            add_text(getattr(fattura, "descrizione", None))

            cliente = getattr(fattura, "cliente", None)
            if cliente:
                for attr in ("denominazione", "ragione_sociale", "nome", "cognome"):
                    add_text(getattr(cliente, attr, None))
                add_text(getattr(cliente, "email", None))
                add_text(getattr(cliente, "pec", None))

        iban = getattr(payment, "iban", None)
        add_text(iban)

        return list(dict.fromkeys(texts))

    def _normalize_text(self, text: str | None) -> str:
        """Normalize text for fuzzy matching.

        Normalization steps:
        1. Convert to lowercase
        2. Remove extra whitespace
        3. Remove special characters (keep alphanumeric and spaces)
        4. Strip leading/trailing whitespace

        Args:
            text: Raw text string or None

        Returns:
            Normalized text string
        """
        if not text or not isinstance(text, str):
            return ""

        # Convert to lowercase
        text = text.lower()

        # Keep alphanumeric characters (any locale) plus basic punctuation
        text = "".join(ch if (ch.isalnum() or ch in {" ", "-", "/", "_"}) else " " for ch in text)

        # Replace underscores with space then collapse whitespace
        text = text.replace("_", " ")
        text = re.sub(r"\s+", " ", text)

        return text.strip()

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

    def _build_match_reason(
        self, similarity_scores: dict[str, float], max_similarity: float
    ) -> str:
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
            f"<FuzzyDescriptionMatcher("
            f"min_similarity={self.min_similarity}%, "
            f"date_tolerance={self.date_tolerance_days} days, "
            f"amount_tolerance={self.amount_tolerance_pct}%, "
            f"early_stop={self.early_stop_threshold}%)>"
        )

    def _validate_confidence(self, confidence: float) -> float:
        """Validate and clamp confidence to [0.0, 1.0] range.

        Args:
            confidence: Confidence score

        Returns:
            Validated confidence between 0.0 and 1.0
        """
        return max(0.0, min(1.0, confidence))
