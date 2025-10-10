"""Domain value objects for payment tracking system.

Value Objects in DDD:
- Immutable (frozen dataclasses)
- No identity (equality based on attributes)
- Describe characteristics, not entities
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING

from .enums import MatchType

if TYPE_CHECKING:
    from ...storage.database.models import Pagamento
    from .models import BankTransaction


@dataclass(frozen=True)
class MatchResult:
    """Result of matching a bank transaction to a payment.

    This is a value object representing the outcome of a matching algorithm.
    It's immutable and has no identity - two MatchResults with the same
    attributes are considered equal.

    Attributes:
        transaction: The bank transaction being matched
        payment: The payment record it matches to
        confidence: Match confidence score (0.0-1.0)
        match_reason: Human-readable explanation of why they match
        match_type: Type of matching algorithm used
        matched_fields: List of fields that contributed to the match
        amount_diff: Absolute difference between transaction and payment amounts
    """

    transaction: "BankTransaction"
    payment: "Pagamento"
    confidence: float
    match_reason: str
    match_type: MatchType
    matched_fields: list[str] = field(default_factory=list)
    amount_diff: Decimal = field(default=Decimal("0.00"))

    def __post_init__(self) -> None:
        """Validate match result constraints."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")

        if self.amount_diff < 0:
            raise ValueError(f"Amount diff must be non-negative, got {self.amount_diff}")

    @property
    def should_auto_apply(self) -> bool:
        """Whether this match should be automatically applied.

        Auto-apply rules:
        - Confidence >= 0.85
        - Amount difference <= 0.01 (1 cent tolerance for rounding)
        - MANUAL matches are always auto-applied
        """
        if self.match_type == MatchType.MANUAL:
            return True

        return self.confidence >= 0.85 and self.amount_diff <= Decimal("0.01")

    @property
    def is_high_confidence(self) -> bool:
        """Whether this is a high-confidence match (>= 0.80)."""
        return self.confidence >= 0.80

    @property
    def is_medium_confidence(self) -> bool:
        """Whether this is a medium-confidence match (0.60-0.79)."""
        return 0.60 <= self.confidence < 0.80

    @property
    def is_low_confidence(self) -> bool:
        """Whether this is a low-confidence match (< 0.60)."""
        return self.confidence < 0.60

    def to_dict(self) -> dict:
        """Convert match result to dictionary for serialization."""
        return {
            "transaction_id": str(self.transaction.id),
            "payment_id": self.payment.id,
            "confidence": float(self.confidence),
            "match_reason": self.match_reason,
            "match_type": self.match_type.value,
            "matched_fields": self.matched_fields,
            "amount_diff": float(self.amount_diff),
            "should_auto_apply": self.should_auto_apply,
        }

    def __str__(self) -> str:
        """Human-readable string representation."""
        return (
            f"MatchResult(confidence={self.confidence:.2f}, "
            f"type={self.match_type.value}, "
            f"reason='{self.match_reason}')"
        )


@dataclass(frozen=True)
class ReconciliationResult:
    """Result of a reconciliation operation.

    Represents the outcome of attempting to reconcile multiple transactions
    with multiple payments in a batch operation.

    Attributes:
        matched_count: Number of transactions successfully matched (high confidence)
        review_count: Number of transactions needing manual review (medium confidence)
        unmatched_count: Number of transactions that couldn't be matched (low confidence)
        total_count: Total number of transactions processed
        matches: List of (transaction, match_results) tuples for matched/review items
        total_amount_matched: Total amount of matched transactions
        errors: List of error messages encountered
    """

    matched_count: int
    review_count: int
    unmatched_count: int
    total_count: int
    matches: list[tuple["BankTransaction", list[MatchResult]]] = field(default_factory=list)
    total_amount_matched: Decimal = field(default=Decimal("0.00"))
    errors: list[str] = field(default_factory=list)

    @property
    def match_rate(self) -> float:
        """Percentage of transactions successfully matched (0.0-1.0)."""
        if self.total_count == 0:
            return 0.0
        return self.matched_count / self.total_count

    @property
    def has_errors(self) -> bool:
        """Whether any errors occurred during reconciliation."""
        return len(self.errors) > 0

    def to_dict(self) -> dict:
        """Convert reconciliation result to dictionary for serialization."""
        return {
            "matched_count": self.matched_count,
            "review_count": self.review_count,
            "unmatched_count": self.unmatched_count,
            "total_count": self.total_count,
            "match_rate": float(self.match_rate),
            "total_amount_matched": float(self.total_amount_matched),
            "errors": self.errors,
            "matches_count": len(self.matches),
        }

    def __str__(self) -> str:
        """Human-readable string representation."""
        return (
            f"ReconciliationResult("
            f"matched={self.matched_count}, "
            f"review={self.review_count}, "
            f"unmatched={self.unmatched_count}/{self.total_count}, "
            f"rate={self.match_rate:.1%})"
        )


@dataclass(frozen=True)
class ImportResult:
    """Result of importing bank transactions from external file.

    Represents the outcome of importing transactions from CSV/OFX/QIF files.
    Tracks success, failures, and duplicates for reporting and debugging.

    Attributes:
        success_count: Number of transactions successfully imported
        error_count: Number of transactions that failed to import
        duplicate_count: Number of duplicate transactions skipped
        errors: List of error messages encountered during import
    """

    success_count: int
    error_count: int
    duplicate_count: int
    errors: list[str] = field(default_factory=list)

    @property
    def total_count(self) -> int:
        """Total number of transactions processed (success + error + duplicate)."""
        return self.success_count + self.error_count + self.duplicate_count

    @property
    def success_rate(self) -> float:
        """Percentage of transactions successfully imported (0.0-1.0)."""
        if self.total_count == 0:
            return 0.0
        return self.success_count / self.total_count

    @property
    def has_errors(self) -> bool:
        """Whether any errors occurred during import."""
        return self.error_count > 0

    def to_dict(self) -> dict:
        """Convert import result to dictionary for serialization."""
        return {
            "success_count": self.success_count,
            "error_count": self.error_count,
            "duplicate_count": self.duplicate_count,
            "total_count": self.total_count,
            "success_rate": float(self.success_rate),
            "errors": self.errors,
        }

    def __str__(self) -> str:
        """Human-readable string representation."""
        return (
            f"ImportResult("
            f"success={self.success_count}, "
            f"errors={self.error_count}, "
            f"duplicates={self.duplicate_count})"
        )
