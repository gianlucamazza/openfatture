"""Date window matcher strategy.

Matches bank transactions to payments based on amount match within a wider
date window (±7 days). Less strict than ExactAmountMatcher but more reliable
than pure fuzzy matching.
"""

from datetime import timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from ..domain.enums import MatchType
from ..domain.value_objects import MatchResult
from .base import IMatcherStrategy

if TYPE_CHECKING:
    from ...storage.database.models import Pagamento
    from ..domain.models import BankTransaction


class DateWindowMatcher(IMatcherStrategy):
    """Match transactions with amount match and date within wider window.

    This strategy is useful when:
    - Payments may be delayed by a few days
    - Bank processing time varies
    - Due dates are approximate

    Differs from ExactAmountMatcher:
    - Wider date window (default ±7 days vs ±3 days)
    - Variable confidence based on date proximity
    - More lenient amount tolerance

    Confidence Scoring:
    - Same date → confidence 0.85
    - ±1 day → confidence 0.80
    - ±2-3 days → confidence 0.75
    - ±4-5 days → confidence 0.70
    - ±6-7 days → confidence 0.65

    Attributes:
        date_tolerance_days: Date window size (default 7 days)
        amount_tolerance: Max amount difference (default 1.00 EUR)

    Example:
        >>> matcher = DateWindowMatcher(date_tolerance_days=10)
        >>> results = matcher.match(transaction, payments)
        >>> # Returns matches within ±10 days with graduated confidence
    """

    def __init__(
        self, date_tolerance_days: int = 7, amount_tolerance: Decimal = Decimal("1.00")
    ) -> None:
        """Initialize date window matcher.

        Args:
            date_tolerance_days: Number of days ± from due date to consider
            amount_tolerance: Maximum amount difference to tolerate
        """
        self.date_tolerance_days = date_tolerance_days
        self.amount_tolerance = amount_tolerance

    def match(
        self, transaction: "BankTransaction", payments: list["Pagamento"]
    ) -> list["MatchResult"]:
        """Match transaction to payments with amount + date window.

        Algorithm:
        1. Filter payments by amount (within tolerance)
        2. Filter by date (within ±date_tolerance_days)
        3. Calculate confidence based on date proximity
        4. Sort by confidence descending

        Args:
            transaction: Bank transaction to match
            payments: List of candidate payments

        Returns:
            List of matches sorted by confidence (best first)
        """
        results: list[MatchResult] = []

        # Calculate date range
        date_min = transaction.date - timedelta(days=self.date_tolerance_days)
        date_max = transaction.date + timedelta(days=self.date_tolerance_days)

        for payment in payments:
            # Check amount match (within tolerance)
            amount_diff = abs(transaction.amount - payment.importo)
            if amount_diff > self.amount_tolerance:
                continue

            # Check date range
            if not (date_min <= payment.data_scadenza <= date_max):
                continue

            # Calculate confidence based on date proximity
            date_diff_days = abs((payment.data_scadenza - transaction.date).days)
            confidence = self._calculate_confidence(date_diff_days, amount_diff)

            # Build match reason
            match_reason = self._build_match_reason(date_diff_days, amount_diff)

            results.append(
                MatchResult(
                    transaction=transaction,
                    payment=payment,
                    confidence=self._validate_confidence(confidence),
                    match_reason=match_reason,
                    match_type=MatchType.DATE_WINDOW,
                    matched_fields=["amount", "date"],
                    amount_diff=amount_diff,
                )
            )

        # Sort by confidence descending, then by date proximity
        results.sort(
            key=lambda r: (
                -r.confidence,  # Negative for descending
                abs((r.payment.data_scadenza - transaction.date).days),
            )
        )

        return results

    def _calculate_confidence(self, date_diff_days: int, amount_diff: Decimal) -> float:
        """Calculate confidence based on date proximity and amount accuracy.

        Base confidence from date proximity:
        - 0 days: 0.85
        - 1 day: 0.80
        - 2-3 days: 0.75
        - 4-5 days: 0.70
        - 6-7 days: 0.65
        - 8+ days: 0.60

        Bonus for exact amount match (+0.05)

        Args:
            date_diff_days: Absolute difference in days
            amount_diff: Absolute difference in amount

        Returns:
            Confidence score (0.60-0.90)
        """
        # Base confidence from date proximity
        if date_diff_days == 0:
            confidence = 0.85
        elif date_diff_days == 1:
            confidence = 0.80
        elif date_diff_days <= 3:
            confidence = 0.75
        elif date_diff_days <= 5:
            confidence = 0.70
        elif date_diff_days <= 7:
            confidence = 0.65
        else:
            confidence = 0.60

        # Bonus for exact amount (within 1 cent)
        if amount_diff <= Decimal("0.01"):
            confidence = min(1.0, confidence + 0.05)

        return confidence

    def _build_match_reason(self, date_diff_days: int, amount_diff: Decimal) -> str:
        """Build human-readable match reason.

        Args:
            date_diff_days: Days difference
            amount_diff: Amount difference

        Returns:
            Match reason string
        """
        if date_diff_days == 0 and amount_diff <= Decimal("0.01"):
            return "Perfect match: same date and exact amount"
        elif date_diff_days == 0:
            return f"Same date, amount diff €{amount_diff:.2f}"
        elif amount_diff <= Decimal("0.01"):
            return f"Exact amount, date within {date_diff_days} day(s)"
        else:
            return (
                f"Date window match: {date_diff_days} day(s) apart, "
                f"amount diff €{amount_diff:.2f}"
            )

    def __repr__(self) -> str:
        """Human-readable string representation."""
        return (
            f"<DateWindowMatcher("
            f"date_tolerance={self.date_tolerance_days} days, "
            f"amount_tolerance=€{self.amount_tolerance})>"
        )
