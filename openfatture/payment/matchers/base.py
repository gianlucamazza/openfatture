"""Base interface for payment matching strategies.

Implements the Strategy pattern to allow different matching algorithms
to be used interchangeably.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...storage.database.models import Pagamento
    from ..domain.models import BankTransaction
    from ..domain.value_objects import MatchResult


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
    def match(
        self, transaction: "BankTransaction", payments: list["Pagamento"]
    ) -> list["MatchResult"]:
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
