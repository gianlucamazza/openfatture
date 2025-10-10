"""Composite matcher that merges results from multiple strategies.

The composite matcher coordinates a list of individual strategies (exact amount, date
window, fuzzy description, IBAN detection, etc.) and produces a single deduplicated
list of matches by weighting each strategy's confidence score.

Key features:
    • Strategies can be synchronous or asynchronous.
    • Weights are normalised automatically if not provided.
    • Results are deduplicated per payment and confidence is a weighted average.
    • Matched fields and reasons are merged to aid explainability.
"""

from __future__ import annotations

import inspect
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation

from ..domain.enums import MatchType
from ..domain.value_objects import MatchResult
from .base import IMatcherStrategy
from .date_window import DateWindowMatcher
from .exact import ExactAmountMatcher
from .fuzzy import FuzzyDescriptionMatcher
from .iban import IBANMatcher


class CompositeMatcher(IMatcherStrategy):
    """Combine multiple strategies using weighted averaging."""

    def __init__(
        self,
        strategies: Sequence[IMatcherStrategy] | None = None,
        weights: Sequence[Decimal | float] | None = None,
        min_confidence: Decimal | float = Decimal("0.60"),
    ) -> None:
        """Create a composite matcher.

        Args:
            strategies: Strategies to execute (defaults to the built-in ones).
            weights: Optional per-strategy weights (same length as strategies).
            min_confidence: Minimum aggregated confidence required to return a match.
        """
        if strategies is None:
            strategies = (
                ExactAmountMatcher(),
                DateWindowMatcher(),
                FuzzyDescriptionMatcher(),
                IBANMatcher(),
            )

        self.strategies: list[IMatcherStrategy] = list(strategies)
        self.weights: list[Decimal] = self._normalise_weights(weights)
        self.min_confidence = self._to_decimal(min_confidence)

    async def match(self, transaction, payments) -> list[MatchResult]:  # type: ignore[override]
        """Execute configured strategies and merge their outputs."""
        if not self.strategies:
            return []

        aggregated: dict[int, dict] = {}

        for weight, strategy in zip(self.weights, self.strategies, strict=True):
            raw_results = strategy.match(transaction, payments)
            if inspect.isawaitable(raw_results):
                raw_results = await raw_results

            for result in raw_results or []:
                payment = result.payment
                key = getattr(payment, "id", None)
                if key is None:
                    key = id(payment)

                entry = aggregated.setdefault(
                    key,
                    {
                        "payment": payment,
                        "transaction": result.transaction or transaction,
                        "weighted_confidence": Decimal("0"),
                        "total_weight": Decimal("0"),
                        "reasons": [],
                        "matched_fields": set(),
                        "types": [],
                        "amount_weighted": Decimal("0"),
                    },
                )

                confidence = self._to_decimal(result.confidence)
                entry["weighted_confidence"] += confidence * weight
                entry["total_weight"] += weight
                entry["reasons"].append(result.match_reason)
                entry["matched_fields"].update(result.matched_fields)
                entry["types"].append((weight, result.match_type))
                entry["amount_weighted"] += self._to_decimal(result.amount_diff) * weight

        merged_results: list[MatchResult] = []
        for entry in aggregated.values():
            total_weight: Decimal = entry["total_weight"]
            if total_weight <= 0:
                continue

            confidence = (entry["weighted_confidence"] / total_weight).quantize(Decimal("0.01"))
            if confidence < self.min_confidence:
                continue

            amount_diff = (entry["amount_weighted"] / total_weight).quantize(Decimal("0.01"))
            match_type = (
                max(entry["types"], key=lambda t: t[0])[1]
                if entry["types"]
                else MatchType.COMPOSITE
            )
            match_reason = "; ".join(dict.fromkeys(entry["reasons"]))

            merged_results.append(
                MatchResult(
                    transaction=entry["transaction"],
                    payment=entry["payment"],
                    confidence=confidence,
                    match_reason=match_reason,
                    match_type=match_type,
                    matched_fields=sorted(entry["matched_fields"]),
                    amount_diff=amount_diff,
                )
            )

        merged_results.sort(key=lambda r: r.confidence, reverse=True)
        return merged_results

    def _normalise_weights(self, weights: Sequence[Decimal | float] | None) -> list[Decimal]:
        """Normalise weights so they sum to 1."""
        count = len(self.strategies)
        if count == 0:
            return []

        if weights is None:
            base = Decimal("1") / Decimal(count)
            return [base] * count

        if len(weights) != count:
            raise ValueError("Weights must match the number of strategies.")

        decimals = [self._to_decimal(w) for w in weights]
        total = sum(decimals)
        if total <= 0:
            raise ValueError("Weights must sum to a positive value.")

        return [w / total for w in decimals]

    @staticmethod
    def _to_decimal(value: Decimal | float | int) -> Decimal:
        """Convert numeric input to Decimal."""
        if isinstance(value, Decimal):
            return value
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError) as exc:  # pragma: no cover - defensive
            raise ValueError(f"Cannot convert {value!r} to Decimal") from exc

    def __repr__(self) -> str:
        return f"<CompositeMatcher(strategies={len(self.strategies)}, min_confidence={self.min_confidence})>"
