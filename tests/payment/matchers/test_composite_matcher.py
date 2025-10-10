"""Tests for CompositeMatcher with property-based testing.

The CompositeMatcher is the most complex matcher, combining multiple strategies
with weighted scoring. Uses Hypothesis for property-based testing.
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pytest
from hypothesis import given
from hypothesis import strategies as st

from openfatture.payment.domain.enums import MatchType
from openfatture.payment.domain.value_objects import MatchResult
from openfatture.payment.matchers.composite import CompositeMatcher

pytestmark = pytest.mark.unit


class TestCompositeMatcherBasic:
    """Basic tests for CompositeMatcher."""

    @pytest.mark.asyncio
    async def test_composite_combines_all_strategies(self):
        """Test that composite matcher uses all configured strategies."""
        # Mock strategies
        strategy1 = AsyncMock()
        strategy1.match.return_value = [
            MatchResult(
                payment=Mock(id=1),
                confidence=Decimal("0.80"),
                match_type=MatchType.EXACT,
                match_reason="Exact amount",
            )
        ]

        strategy2 = AsyncMock()
        strategy2.match.return_value = [
            MatchResult(
                payment=Mock(id=1),
                confidence=Decimal("0.70"),
                match_type=MatchType.FUZZY,
                match_reason="Fuzzy description",
            )
        ]

        composite = CompositeMatcher(strategies=[strategy1, strategy2])

        # Mock transaction and candidates
        transaction = Mock()
        transaction.amount = Decimal("100.00")
        transaction.description = "Test payment"
        transaction.date = date.today()

        candidates = [Mock(id=1)]

        results = await composite.match(transaction, candidates)

        # Both strategies should have been called
        strategy1.match.assert_called_once()
        strategy2.match.assert_called_once()

        # Should return combined/deduplicated results
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_composite_weighted_average_calculation(self):
        """Test that confidence is calculated as weighted average."""
        # Mock two strategies with known confidences
        strategy1 = AsyncMock()
        strategy1.match.return_value = [
            MatchResult(
                payment=Mock(id=1),
                confidence=Decimal("1.00"),  # Perfect match
                match_type=MatchType.EXACT,
                match_reason="Exact",
            )
        ]

        strategy2 = AsyncMock()
        strategy2.match.return_value = [
            MatchResult(
                payment=Mock(id=1),
                confidence=Decimal("0.50"),  # Medium match
                match_type=MatchType.FUZZY,
                match_reason="Fuzzy",
            )
        ]

        # Equal weights → average should be 0.75
        composite = CompositeMatcher(
            strategies=[strategy1, strategy2],
            weights=[Decimal("0.5"), Decimal("0.5")],
        )

        transaction = Mock(amount=Decimal("100.00"), description="Test", date=date.today())
        candidates = [Mock(id=1)]

        results = await composite.match(transaction, candidates)

        # Final confidence should be weighted average
        assert len(results) == 1
        # (1.00 * 0.5) + (0.50 * 0.5) = 0.75
        assert results[0].confidence == Decimal("0.75")

    @pytest.mark.asyncio
    async def test_composite_strategy_weights_customizable(self):
        """Test that strategy weights can be customized."""
        strategy1 = AsyncMock()
        strategy1.match.return_value = [
            MatchResult(
                payment=Mock(id=1),
                confidence=Decimal("1.00"),
                match_type=MatchType.EXACT,
                match_reason="Exact",
            )
        ]

        strategy2 = AsyncMock()
        strategy2.match.return_value = [
            MatchResult(
                payment=Mock(id=1),
                confidence=Decimal("0.60"),
                match_type=MatchType.FUZZY,
                match_reason="Fuzzy",
            )
        ]

        # Custom weights: 80% exact, 20% fuzzy
        composite = CompositeMatcher(
            strategies=[strategy1, strategy2],
            weights=[Decimal("0.8"), Decimal("0.2")],
        )

        transaction = Mock(amount=Decimal("100.00"), description="Test", date=date.today())
        candidates = [Mock(id=1)]

        results = await composite.match(transaction, candidates)

        # Weighted average: (1.00 * 0.8) + (0.60 * 0.2) = 0.92
        assert results[0].confidence == Decimal("0.92")

    @pytest.mark.asyncio
    async def test_composite_confidence_normalization(self):
        """Test that final confidence is always normalized to [0.0, 1.0]."""
        strategy = AsyncMock()
        strategy.match.return_value = [
            MatchResult(
                payment=Mock(id=1),
                confidence=Decimal("1.0"),
                match_type=MatchType.EXACT,
                match_reason="Max",
            )
        ]

        composite = CompositeMatcher(strategies=[strategy])

        transaction = Mock(amount=Decimal("100.00"), description="Test", date=date.today())
        candidates = [Mock(id=1)]

        results = await composite.match(transaction, candidates)

        assert Decimal("0.0") <= results[0].confidence <= Decimal("1.0")

    @pytest.mark.asyncio
    async def test_composite_empty_strategies_returns_empty(self):
        """Test that composite with no strategies returns empty list."""
        composite = CompositeMatcher(strategies=[])

        transaction = Mock(amount=Decimal("100.00"), description="Test", date=date.today())
        candidates = [Mock(id=1)]

        results = await composite.match(transaction, candidates)

        assert results == []

    @pytest.mark.asyncio
    async def test_composite_deduplication_same_payment(self):
        """Test that composite deduplicates results for same payment."""
        # Both strategies match the same payment
        strategy1 = AsyncMock()
        strategy1.match.return_value = [
            MatchResult(
                payment=Mock(id=1),
                confidence=Decimal("0.80"),
                match_type=MatchType.EXACT,
                match_reason="Exact",
            )
        ]

        strategy2 = AsyncMock()
        strategy2.match.return_value = [
            MatchResult(
                payment=Mock(id=1),  # Same payment ID
                confidence=Decimal("0.70"),
                match_type=MatchType.FUZZY,
                match_reason="Fuzzy",
            )
        ]

        composite = CompositeMatcher(strategies=[strategy1, strategy2])

        transaction = Mock(amount=Decimal("100.00"), description="Test", date=date.today())
        candidates = [Mock(id=1)]

        results = await composite.match(transaction, candidates)

        # Should only return ONE result (deduplicated by payment ID)
        assert len(results) == 1


class TestCompositeMatcherPropertyBased:
    """Property-based tests for CompositeMatcher using Hypothesis."""

    @given(
        confidences=st.lists(
            st.decimals(min_value=Decimal("0.0"), max_value=Decimal("1.0"), places=2),
            min_size=2,
            max_size=5,
        ),
        weights=st.lists(
            st.decimals(min_value=Decimal("0.0"), max_value=Decimal("1.0"), places=2),
            min_size=2,
            max_size=5,
        ),
    )
    @pytest.mark.asyncio
    async def test_composite_confidence_always_bounded(self, confidences, weights):
        """Property: Final confidence is ALWAYS in [0.0, 1.0] regardless of inputs."""
        # Ensure same length
        if len(confidences) != len(weights):
            return

        # Normalize weights to sum to 1.0
        total_weight = sum(weights)
        if total_weight == 0:
            return
        normalized_weights = [w / total_weight for w in weights]

        # Create mock strategies
        strategies = []
        for conf in confidences:
            strategy = AsyncMock()
            strategy.match.return_value = [
                MatchResult(
                    payment=Mock(id=1),
                    confidence=conf,
                    match_type=MatchType.COMPOSITE,
                    match_reason="Test",
                )
            ]
            strategies.append(strategy)

        composite = CompositeMatcher(strategies=strategies, weights=normalized_weights)

        transaction = Mock(amount=Decimal("100.00"), description="Test", date=date.today())
        candidates = [Mock(id=1)]

        results = await composite.match(transaction, candidates)

        if results:
            # Property: confidence is bounded
            assert Decimal("0.0") <= results[0].confidence <= Decimal("1.0")

    @given(
        confidences=st.lists(
            st.decimals(min_value=0, max_value=1, places=2), min_size=1, max_size=5
        )
    )
    @pytest.mark.asyncio
    async def test_composite_deterministic(self, confidences):
        """Property: Same inputs should produce same outputs (determinism)."""
        # Create strategies with fixed confidences
        strategies = []
        for conf in confidences:
            strategy = AsyncMock()
            strategy.match.return_value = [
                MatchResult(
                    payment=Mock(id=1),
                    confidence=Decimal(str(conf)),
                    match_type=MatchType.COMPOSITE,
                    match_reason="Test",
                )
            ]
            strategies.append(strategy)

        composite = CompositeMatcher(strategies=strategies)

        transaction = Mock(amount=Decimal("100.00"), description="Test", date=date.today())
        candidates = [Mock(id=1)]

        # Run twice
        results1 = await composite.match(transaction, candidates)
        results2 = await composite.match(transaction, candidates)

        # Property: deterministic results
        if results1 and results2:
            assert results1[0].confidence == results2[0].confidence

    @given(st.lists(st.decimals(min_value=0, max_value=1, places=2), min_size=2, max_size=5))
    @pytest.mark.asyncio
    async def test_composite_average_properties(self, confidences):
        """Property: Weighted average should satisfy mathematical properties."""
        if not confidences:
            return

        # Equal weights
        weights = [Decimal("1.0") / len(confidences) for _ in confidences]

        strategies = []
        for conf in confidences:
            strategy = AsyncMock()
            strategy.match.return_value = [
                MatchResult(
                    payment=Mock(id=1),
                    confidence=Decimal(str(conf)),
                    match_type=MatchType.COMPOSITE,
                    match_reason="Test",
                )
            ]
            strategies.append(strategy)

        composite = CompositeMatcher(strategies=strategies, weights=weights)

        transaction = Mock(amount=Decimal("100.00"), description="Test", date=date.today())
        candidates = [Mock(id=1)]

        results = await composite.match(transaction, candidates)

        if results:
            avg = results[0].confidence

            # Property: average is between min and max
            min_conf = min(Decimal(str(c)) for c in confidences)
            max_conf = max(Decimal(str(c)) for c in confidences)

            assert min_conf <= avg <= max_conf


# Configure Hypothesis settings for CI
from hypothesis import Verbosity, settings
import os

settings.register_profile("ci", max_examples=200, verbosity=Verbosity.verbose)
settings.register_profile("dev", max_examples=50)
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "dev"))
