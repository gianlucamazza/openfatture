"""Tests for DateWindowMatcher.

The DateWindowMatcher matches transactions within a configurable date window
of payment due dates, with confidence decay over time.
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock

import pytest

from openfatture.payment.domain.enums import MatchType
from openfatture.payment.matchers.date_window import DateWindowMatcher

pytestmark = pytest.mark.unit


class TestDateWindowMatcher:
    """Tests for DateWindowMatcher."""

    @pytest.mark.asyncio
    async def test_date_window_within_range_matches(self):
        """Test that payments within date window match."""
        matcher = DateWindowMatcher(window_days=30)

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.description = "Payment"
        transaction.date = date(2025, 1, 15)

        # Payment due 20 days after transaction (within 30-day window)
        payment = Mock()
        payment.id = 1
        payment.importo_da_pagare = Decimal("1000.00")
        payment.data_scadenza = date(2025, 2, 4)  # 20 days later
        payment.fattura = Mock()
        payment.fattura.numero = "001"

        candidates = [payment]

        results = await matcher.match(transaction, candidates)

        assert len(results) == 1
        assert results[0].match_type == MatchType.DATE_WINDOW
        assert results[0].confidence > Decimal("0.0")

    @pytest.mark.asyncio
    async def test_date_window_exact_boundary_dates(self):
        """Test matching at exact window boundaries."""
        matcher = DateWindowMatcher(window_days=30)

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.description = "Payment"
        transaction.date = date(2025, 1, 15)

        # Payment exactly 30 days after transaction (boundary)
        payment_at_boundary = Mock()
        payment_at_boundary.id = 1
        payment_at_boundary.importo_da_pagare = Decimal("1000.00")
        payment_at_boundary.data_scadenza = date(2025, 2, 14)  # Exactly 30 days
        payment_at_boundary.fattura = Mock()
        payment_at_boundary.fattura.numero = "001"

        # Payment before transaction (within window backwards)
        payment_before = Mock()
        payment_before.id = 2
        payment_before.importo_da_pagare = Decimal("1000.00")
        payment_before.data_scadenza = date(2024, 12, 16)  # 30 days before
        payment_before.fattura = Mock()
        payment_before.fattura.numero = "002"

        candidates = [payment_at_boundary, payment_before]

        results = await matcher.match(transaction, candidates)

        # Both boundary cases should match
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_date_window_outside_range_no_match(self):
        """Test that payments outside window don't match."""
        matcher = DateWindowMatcher(window_days=30)

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.description = "Payment"
        transaction.date = date(2025, 1, 15)

        # Payment 60 days after transaction (outside 30-day window)
        payment = Mock()
        payment.id = 1
        payment.importo_da_pagare = Decimal("1000.00")
        payment.data_scadenza = date(2025, 3, 16)  # 60 days later
        payment.fattura = Mock()
        payment.fattura.numero = "001"

        candidates = [payment]

        results = await matcher.match(transaction, candidates)

        # Outside window
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_date_window_custom_days_configuration(self):
        """Test that custom window_days parameter works."""
        # Narrow window
        narrow_matcher = DateWindowMatcher(window_days=7)

        # Wide window
        wide_matcher = DateWindowMatcher(window_days=60)

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.description = "Payment"
        transaction.date = date(2025, 1, 15)

        # Payment 10 days after transaction
        payment = Mock()
        payment.id = 1
        payment.importo_da_pagare = Decimal("1000.00")
        payment.data_scadenza = date(2025, 1, 25)  # 10 days later
        payment.fattura = Mock()
        payment.fattura.numero = "001"

        candidates = [payment]

        narrow_results = await narrow_matcher.match(transaction, candidates)
        wide_results = await wide_matcher.match(transaction, candidates)

        # Narrow window should not match (10 > 7)
        assert len(narrow_results) == 0

        # Wide window should match (10 < 60)
        assert len(wide_results) == 1

    @pytest.mark.asyncio
    async def test_date_window_confidence_decay_over_time(self):
        """Test that confidence decays as time distance increases."""
        matcher = DateWindowMatcher(window_days=30)

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.description = "Payment"
        transaction.date = date(2025, 1, 15)

        # Payment 5 days later (close)
        payment_close = Mock()
        payment_close.id = 1
        payment_close.importo_da_pagare = Decimal("1000.00")
        payment_close.data_scadenza = date(2025, 1, 20)  # 5 days
        payment_close.fattura = Mock()
        payment_close.fattura.numero = "001"

        # Payment 25 days later (far)
        payment_far = Mock()
        payment_far.id = 2
        payment_far.importo_da_pagare = Decimal("1000.00")
        payment_far.data_scadenza = date(2025, 2, 9)  # 25 days
        payment_far.fattura = Mock()
        payment_far.fattura.numero = "002"

        candidates = [payment_close, payment_far]

        results = await matcher.match(transaction, candidates)

        # Both should match, but closer date should have higher confidence
        assert len(results) == 2

        close_result = next(r for r in results if r.payment.id == 1)
        far_result = next(r for r in results if r.payment.id == 2)

        # Confidence decay property
        assert close_result.confidence > far_result.confidence

    @pytest.mark.asyncio
    async def test_date_window_leap_year_handling(self):
        """Test date window calculation handles leap years correctly."""
        matcher = DateWindowMatcher(window_days=30)

        # Transaction in February 2024 (leap year)
        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.description = "Payment"
        transaction.date = date(2024, 2, 15)

        # Payment due date crossing leap day
        payment = Mock()
        payment.id = 1
        payment.importo_da_pagare = Decimal("1000.00")
        payment.data_scadenza = date(2024, 3, 10)  # Crosses Feb 29
        payment.fattura = Mock()
        payment.fattura.numero = "001"

        candidates = [payment]

        results = await matcher.match(transaction, candidates)

        # Should handle leap year correctly
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_date_window_same_date_max_confidence(self):
        """Test that same transaction and due date gives maximum confidence."""
        matcher = DateWindowMatcher(window_days=30)

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.description = "Payment"
        transaction.date = date(2025, 1, 15)

        # Payment due on same date
        payment = Mock()
        payment.id = 1
        payment.importo_da_pagare = Decimal("1000.00")
        payment.data_scadenza = date(2025, 1, 15)  # Same date
        payment.fattura = Mock()
        payment.fattura.numero = "001"

        candidates = [payment]

        results = await matcher.match(transaction, candidates)

        # Same date should give high confidence
        assert len(results) == 1
        assert results[0].confidence > Decimal("0.9")

    @pytest.mark.asyncio
    async def test_date_window_multiple_payments_sorted_by_confidence(self):
        """Test that results are sorted by confidence (closest dates first)."""
        matcher = DateWindowMatcher(window_days=30)

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.description = "Payment"
        transaction.date = date(2025, 1, 15)

        # Create multiple payments at different distances
        payments = []
        for i, days_offset in enumerate([25, 5, 15, 2]):  # Various distances
            payment = Mock()
            payment.id = i + 1
            payment.importo_da_pagare = Decimal("1000.00")
            payment.data_scadenza = date(2025, 1, 15) + timedelta(days=days_offset)
            payment.fattura = Mock()
            payment.fattura.numero = f"00{i+1}"
            payments.append(payment)

        results = await matcher.match(transaction, payments)

        # All should match
        assert len(results) == 4

        # Results should be sorted by confidence (descending)
        for i in range(len(results) - 1):
            assert results[i].confidence >= results[i + 1].confidence

    @pytest.mark.asyncio
    async def test_date_window_match_reason_includes_days(self):
        """Test that match reason includes days difference."""
        matcher = DateWindowMatcher(window_days=30)

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.description = "Payment"
        transaction.date = date(2025, 1, 15)

        payment = Mock()
        payment.id = 1
        payment.importo_da_pagare = Decimal("1000.00")
        payment.data_scadenza = date(2025, 1, 25)  # 10 days later
        payment.fattura = Mock()
        payment.fattura.numero = "001"

        candidates = [payment]

        results = await matcher.match(transaction, candidates)

        # Match reason should mention days or date window
        assert "day" in results[0].match_reason.lower() or "date" in results[0].match_reason.lower()
