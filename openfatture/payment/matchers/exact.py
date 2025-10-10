"""Exact amount matcher strategy.

Matches bank transactions to payments based on exact amount and date within ±3 days.
This is the most conservative matching strategy with highest confidence (1.0).
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


class ExactAmountMatcher(IMatcherStrategy):
    """Match transactions with exact amount and date within tolerance.

    This strategy provides the highest confidence (1.0) for matches because:
    - Amount must match exactly (within 1 cent for rounding)
    - Date must be within ±3 days of payment due date
    - No fuzzy logic involved

    Perfect for:
    - Automated reconciliation without human review
    - High-volume transaction processing
    - When bank descriptions are unreliable

    Attributes:
        date_tolerance_days: Number of days before/after due date to consider (default 3)
        amount_tolerance: Decimal amount tolerance for rounding errors (default 0.01)

    Example:
        >>> matcher = ExactAmountMatcher(date_tolerance_days=5)
        >>> results = matcher.match(transaction, payments)
        >>> if results and results[0].confidence == 1.0:
        ...     # Auto-apply this match
        ...     transaction.match_to_payment(results[0].payment, 1.0, MatchType.EXACT)
    """

    def __init__(
        self, date_tolerance_days: int = 3, amount_tolerance: Decimal = Decimal("0.01")
    ) -> None:
        """Initialize exact amount matcher.

        Args:
            date_tolerance_days: Number of days ± from due date to consider a match
            amount_tolerance: Maximum amount difference to account for rounding (e.g., 0.01 = 1 cent)
        """
        self.date_tolerance_days = date_tolerance_days
        self.amount_tolerance = amount_tolerance

    def match(
        self, transaction: "BankTransaction", payments: list["Pagamento"]
    ) -> list["MatchResult"]:
        """Match transaction to payments with exact amount and close date.

        Algorithm:
        1. Filter payments by amount (within tolerance)
        2. Filter by date (within ±3 days of due date)
        3. Create MatchResult with confidence 1.0
        4. Sort by date proximity (closest date first)

        Args:
            transaction: Bank transaction to match
            payments: List of candidate payments

        Returns:
            List of exact matches, sorted by date proximity (best match first).
            Empty list if no exact matches found.

        Note:
            - All returned matches have confidence 1.0
            - Results are sorted by date proximity (closest first)
            - Amount difference must be <= amount_tolerance
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

            # Check date match (within tolerance window)
            if not (date_min <= payment.data_scadenza <= date_max):
                continue

            # Perfect match found!
            match_reason = self._build_match_reason(transaction, payment, amount_diff)

            results.append(
                MatchResult(
                    transaction=transaction,
                    payment=payment,
                    confidence=1.0,  # Perfect match
                    match_reason=match_reason,
                    match_type=MatchType.EXACT,
                    matched_fields=["amount", "date"],
                    amount_diff=amount_diff,
                )
            )

        # Sort by date proximity (closest date first) and amount difference
        results.sort(
            key=lambda r: (
                abs((r.payment.data_scadenza - transaction.date).days),
                r.amount_diff,
            )
        )

        return results

    def _build_match_reason(
        self, transaction: "BankTransaction", payment: "Pagamento", amount_diff: Decimal
    ) -> str:
        """Build human-readable explanation of why they matched.

        Args:
            transaction: The bank transaction
            payment: The matched payment
            amount_diff: Absolute difference in amounts

        Returns:
            Human-readable match reason string
        """
        date_diff_days = abs((payment.data_scadenza - transaction.date).days)

        if amount_diff == 0 and date_diff_days == 0:
            return "Perfect match: exact amount and same date"
        elif amount_diff == 0:
            return f"Exact amount match, date within {date_diff_days} day(s)"
        elif date_diff_days == 0:
            return f"Same date, amount difference: €{amount_diff:.2f}"
        else:
            return (
                f"Exact match: amount diff €{amount_diff:.2f}, "
                f"date within {date_diff_days} day(s)"
            )

    def __repr__(self) -> str:
        """Human-readable string representation."""
        return (
            f"<ExactAmountMatcher(date_tolerance={self.date_tolerance_days} days, "
            f"amount_tolerance=€{self.amount_tolerance})>"
        )
