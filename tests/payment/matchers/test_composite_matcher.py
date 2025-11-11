"""Tests for CompositeMatcher with property-based testing.

The CompositeMatcher is the most complex matcher, combining multiple strategies
with weighted scoring. Uses Hypothesis for property-based testing.
"""

from datetime import date
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
        assert results[0].confidence == pytest.approx(0.92)

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

        assert 0.0 <= results[0].confidence <= 1.0

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

    @pytest.mark.asyncio
    async def test_composite_exception_isolation(self):
        """Test that exception in one strategy doesn't fail other strategies.

        PHASE 1 Enhancement: Parallel execution with exception isolation.
        """
        # Strategy 1: Fails with exception
        strategy1 = AsyncMock()
        strategy1.match.side_effect = ValueError("Strategy 1 failed")
        strategy1.__class__.__name__ = "FailingStrategy"

        # Strategy 2: Succeeds normally
        strategy2 = AsyncMock()
        strategy2.match.return_value = [
            MatchResult(
                payment=Mock(id=1),
                confidence=Decimal("0.85"),
                match_type=MatchType.EXACT,
                match_reason="Exact match",
            )
        ]
        strategy2.__class__.__name__ = "SuccessfulStrategy"

        # Strategy 3: Also succeeds
        strategy3 = AsyncMock()
        strategy3.match.return_value = [
            MatchResult(
                payment=Mock(id=2),
                confidence=Decimal("0.75"),
                match_type=MatchType.FUZZY,
                match_reason="Fuzzy match",
            )
        ]
        strategy3.__class__.__name__ = "AnotherSuccessfulStrategy"

        composite = CompositeMatcher(strategies=[strategy1, strategy2, strategy3])

        transaction = Mock(
            id="test-tx-123",
            amount=Decimal("100.00"),
            description="Test payment",
            date=date.today(),
        )
        candidates = [Mock(id=1), Mock(id=2)]

        results = await composite.match(transaction, candidates)

        # Should return results from successful strategies only
        assert len(results) == 2
        assert results[0].confidence == 0.85  # From strategy2
        assert results[1].confidence == 0.75  # From strategy3

        # Verify all strategies were called (even the failing one)
        strategy1.match.assert_called_once()
        strategy2.match.assert_called_once()
        strategy3.match.assert_called_once()

    @pytest.mark.asyncio
    async def test_composite_parallel_execution_ordering(self):
        """Test that results from parallel execution maintain correct ordering.

        PHASE 1 Enhancement: Verify parallel execution produces same results as sequential.
        """
        # Create strategies that return predictable results
        strategy1 = AsyncMock()
        strategy1.match.return_value = [
            MatchResult(
                payment=Mock(id=1),
                confidence=Decimal("0.90"),
                match_type=MatchType.EXACT,
                match_reason="Exact",
            )
        ]

        strategy2 = AsyncMock()
        strategy2.match.return_value = [
            MatchResult(
                payment=Mock(id=2),
                confidence=Decimal("0.80"),
                match_type=MatchType.FUZZY,
                match_reason="Fuzzy",
            )
        ]

        strategy3 = AsyncMock()
        strategy3.match.return_value = [
            MatchResult(
                payment=Mock(id=3),
                confidence=Decimal("0.70"),
                match_type=MatchType.DATE_WINDOW,
                match_reason="Date window",
            )
        ]

        composite = CompositeMatcher(strategies=[strategy1, strategy2, strategy3])

        transaction = Mock(amount=Decimal("100.00"), description="Test", date=date.today())
        candidates = [Mock(id=1), Mock(id=2), Mock(id=3)]

        results = await composite.match(transaction, candidates)

        # Results should be sorted by confidence descending
        assert len(results) == 3
        assert results[0].confidence == 0.90  # Highest
        assert results[1].confidence == 0.80  # Medium
        assert results[2].confidence == 0.70  # Lowest

        # Verify ordering is stable across multiple calls
        results2 = await composite.match(transaction, candidates)
        assert [r.confidence for r in results] == [r.confidence for r in results2]

    @pytest.mark.asyncio
    async def test_composite_all_strategies_fail(self):
        """Test graceful handling when all strategies fail with exceptions."""
        # All strategies fail
        strategy1 = AsyncMock()
        strategy1.match.side_effect = ValueError("Failed 1")
        strategy1.__class__.__name__ = "FailingStrategy1"

        strategy2 = AsyncMock()
        strategy2.match.side_effect = RuntimeError("Failed 2")
        strategy2.__class__.__name__ = "FailingStrategy2"

        composite = CompositeMatcher(strategies=[strategy1, strategy2])

        transaction = Mock(
            id="test-tx-456",
            amount=Decimal("100.00"),
            description="Test",
            date=date.today(),
        )
        candidates = [Mock(id=1)]

        results = await composite.match(transaction, candidates)

        # Should return empty list, not raise exception
        assert results == []

    @pytest.mark.asyncio
    async def test_composite_mixed_sync_async_strategies(self):
        """Test CompositeMatcher works with both sync and async strategies.

        PHASE 1 Enhancement: Ensure backward compatibility with sync matchers.
        """
        # Async strategy
        async_strategy = AsyncMock()
        async_strategy.match.return_value = [
            MatchResult(
                payment=Mock(id=1),
                confidence=Decimal("0.85"),
                match_type=MatchType.EXACT,
                match_reason="Async match",
            )
        ]

        # Sync strategy (returns result immediately, not awaitable)
        sync_strategy = Mock()
        sync_strategy.match.return_value = [
            MatchResult(
                payment=Mock(id=1),
                confidence=Decimal("0.75"),
                match_type=MatchType.FUZZY,
                match_reason="Sync match",
            )
        ]

        composite = CompositeMatcher(strategies=[async_strategy, sync_strategy])

        transaction = Mock(amount=Decimal("100.00"), description="Test", date=date.today())
        candidates = [Mock(id=1)]

        results = await composite.match(transaction, candidates)

        # Both strategies should contribute to final result
        assert len(results) == 1
        # Average of 0.85 and 0.75 with equal weights = 0.80
        assert results[0].confidence == pytest.approx(0.80)


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
            avg_dec = Decimal(str(results[0].confidence))

            # Property: average is between min and max
            min_conf = min(Decimal(str(c)) for c in confidences)
            max_conf = max(Decimal(str(c)) for c in confidences)

            assert min_conf <= avg_dec <= max_conf


# Configure Hypothesis settings for CI
import os

from hypothesis import Verbosity, settings

settings.register_profile("ci", max_examples=200, verbosity=Verbosity.verbose)
settings.register_profile("dev", max_examples=50)
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "dev"))
