"""Base interface for payment matching strategies.

Implements the Strategy pattern to allow different matching algorithms
to be used interchangeably.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Generator, Iterable
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, Any

from ..domain.value_objects import MatchResult

if TYPE_CHECKING:
    from ...storage.database.models import Pagamento
    from ..domain.models import BankTransaction


MatchResultListType = list[MatchResult]
MatchResults = MatchResultListType | Awaitable[MatchResultListType]


class IMatcherStrategy(ABC):
    """Abstract base class for payment matching strategies.

    Each strategy implements a different algorithm for matching bank transactions
    to payment records. Strategies return confidence scores (0.0-1.0) indicating
    how confident they are in the match.

    Implementing a new strategy:
        1. Inherit from IMatcherStrategy
        2. Implement match() method
        3. Return list of MatchResult objects
        4. Ensure confidence is between 0.0 and 1.0
        5. Set appropriate match_type and match_reason

    Example:
        >>> class CustomMatcher(IMatcherStrategy):
        ...     def match(self, transaction, payments):
        ...         results = []
        ...         for payment in payments:
        ...             if self._custom_logic(transaction, payment):
        ...                 results.append(MatchResult(
        ...                     transaction=transaction,
        ...                     payment=payment,
        ...                     confidence=0.85,
        ...                     match_reason="Custom logic matched",
        ...                     match_type=MatchType.COMPOSITE,
        ...                     matched_fields=["custom_field"]
        ...                 ))
        ...         return results
    """

    @abstractmethod
    def match(self, transaction: BankTransaction, payments: list[Pagamento]) -> MatchResults:
        """Match a bank transaction to potential payments.

        Args:
            transaction: The bank transaction to match
            payments: List of candidate payment records to match against

        Returns:
            List of MatchResult objects, sorted by confidence (highest first).
            Empty list if no matches found.

        Note:
            - Implementations should filter out obviously impossible matches
              (e.g., amount mismatch, wrong date range)
            - Results should be sorted by confidence descending
            - Confidence must be between 0.0 and 1.0
        """
        pass

    def _validate_confidence(self, confidence: float) -> float:
        """Ensure confidence is within valid range [0.0, 1.0].

        Args:
            confidence: Raw confidence score

        Returns:
            Clamped confidence value between 0.0 and 1.0

        Raises:
            ValueError: If confidence is negative or greater than 1.0
        """
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {confidence}")
        return confidence

    def __repr__(self) -> str:
        """Human-readable string representation."""
        return f"<{self.__class__.__name__}>"


class MatchResultList(list[MatchResult]):
    """List-like container that can also be awaited."""

    def __await__(self) -> Generator[MatchResultListType, None, MatchResultListType]:
        async def _coro() -> MatchResultListType:
            return self

        return _coro().__await__()


def as_match_results(results: Iterable[MatchResult]) -> MatchResultList:
    """Wrap iterable of MatchResult into an awaitable list."""
    return MatchResultList(results)


def _to_decimal_or_none(value: Any) -> Decimal | None:
    """Convert arbitrary value to Decimal if possible, otherwise None."""
    try:
        return Decimal(str(value))
    except (TypeError, ValueError, InvalidOperation):
        return None


def payment_amount_for_matching(payment: Pagamento) -> Decimal:
    """Return the outstanding amount to use during matching comparisons."""

    # Prefer dedicated outstanding attribute if available
    saldo = getattr(payment, "saldo_residuo", None)
    saldo_decimal = _to_decimal_or_none(saldo)
    if saldo_decimal is not None and saldo_decimal >= Decimal("0.00"):
        return saldo_decimal

    # Fallback to total minus paid
    total = getattr(payment, "importo_da_pagare", None)
    total_decimal = _to_decimal_or_none(total)

    if total_decimal is None:
        total_decimal = _to_decimal_or_none(getattr(payment, "importo", Decimal("0.00")))

    if total_decimal is None:
        total_decimal = Decimal("0.00")

    paid = getattr(payment, "importo_pagato", Decimal("0.00"))
    paid_decimal = _to_decimal_or_none(paid) or Decimal("0.00")

    outstanding = total_decimal - paid_decimal
    if outstanding < Decimal("0.00"):
        outstanding = Decimal("0.00")

    return outstanding
