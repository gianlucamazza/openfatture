"""Tests for ExactAmountMatcher.

The ExactAmountMatcher provides 100% confidence matches when transaction
amount exactly equals payment amount.
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock

import pytest

from openfatture.payment.domain.enums import MatchType
from openfatture.payment.matchers.exact import ExactAmountMatcher

pytestmark = pytest.mark.unit


class TestExactAmountMatcher:
    """Tests for ExactAmountMatcher."""

    @pytest.mark.asyncio
    async def test_exact_amount_match_100_percent_confidence(self):
        """Test exact amount match returns 100% confidence."""
        matcher = ExactAmountMatcher()

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.date = date(2025, 1, 15)

        # Create candidate payment with exact amount
        payment = Mock()
        payment.id = 1
        payment.importo_da_pagare = Decimal("1000.00")
        payment.data_scadenza = date(2025, 1, 20)

        candidates = [payment]

        results = await matcher.match(transaction, candidates)

        assert len(results) == 1
        assert results[0].confidence == Decimal("1.0")
        assert results[0].match_type == MatchType.EXACT
        assert results[0].payment.id == 1

    @pytest.mark.asyncio
    async def test_exact_amount_no_match_returns_empty(self):
        """Test no match when amounts differ."""
        matcher = ExactAmountMatcher()

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.date = date.today()

        # Candidate with different amount
        payment = Mock()
        payment.id = 1
        payment.importo_da_pagare = Decimal("1500.00")  # Different
        payment.data_scadenza = date.today()

        candidates = [payment]

        results = await matcher.match(transaction, candidates)

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_exact_amount_multiple_candidates_all_returned(self):
        """Test that all candidates with exact amount are returned."""
        matcher = ExactAmountMatcher()

        transaction = Mock()
        transaction.amount = Decimal("500.00")
        transaction.date = date.today()

        # Multiple payments with same amount
        payment1 = Mock()
        payment1.id = 1
        payment1.importo_da_pagare = Decimal("500.00")
        payment1.data_scadenza = date.today()

        payment2 = Mock()
        payment2.id = 2
        payment2.importo_da_pagare = Decimal("500.00")
        payment2.data_scadenza = date.today() + timedelta(days=10)

        payment3 = Mock()
        payment3.id = 3
        payment3.importo_da_pagare = Decimal("600.00")  # Different

        candidates = [payment1, payment2, payment3]

        results = await matcher.match(transaction, candidates)

        # Should return 2 matches (payment1 and payment2)
        assert len(results) == 2
        assert all(r.confidence == Decimal("1.0") for r in results)

    @pytest.mark.asyncio
    async def test_exact_amount_date_window_filtering(self):
        """Test that date_window parameter filters candidates."""
        matcher = ExactAmountMatcher()

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.date = date(2025, 1, 15)

        # Payment within date window
        payment_in_window = Mock()
        payment_in_window.id = 1
        payment_in_window.importo_da_pagare = Decimal("1000.00")
        payment_in_window.data_scadenza = date(2025, 1, 20)  # 5 days later

        # Payment outside date window
        payment_out_window = Mock()
        payment_out_window.id = 2
        payment_out_window.importo_da_pagare = Decimal("1000.00")
        payment_out_window.data_scadenza = date(2025, 3, 15)  # 60 days later

        candidates = [payment_in_window, payment_out_window]

        # With 30-day window, only first payment should match
        results = await matcher.match(transaction, candidates, date_window_days=30)

        assert len(results) == 1
        assert results[0].payment.id == 1

    @pytest.mark.asyncio
    async def test_decimal_precision_matching(self):
        """Test that Decimal precision is handled correctly."""
        matcher = ExactAmountMatcher()

        transaction = Mock()
        transaction.amount = Decimal("100.00")
        transaction.date = date.today()

        # Payment with same value but different precision representation
        payment1 = Mock()
        payment1.id = 1
        payment1.importo_da_pagare = Decimal("100.0")  # One decimal place
        payment1.data_scadenza = date.today()

        payment2 = Mock()
        payment2.id = 2
        payment2.importo_da_pagare = Decimal("100.000")  # Three decimal places
        payment2.data_scadenza = date.today()

        candidates = [payment1, payment2]

        results = await matcher.match(transaction, candidates)

        # Both should match (Decimal equality)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_exact_amount_empty_candidates(self):
        """Test behavior with empty candidates list."""
        matcher = ExactAmountMatcher()

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.date = date.today()

        results = await matcher.match(transaction, [])

        assert results == []

    @pytest.mark.asyncio
    async def test_exact_amount_negative_amounts(self):
        """Test matching with negative amounts (debits)."""
        matcher = ExactAmountMatcher()

        transaction = Mock()
        transaction.amount = Decimal("-500.00")  # Debit
        transaction.date = date.today()

        payment = Mock()
        payment.id = 1
        payment.importo_da_pagare = Decimal("-500.00")
        payment.data_scadenza = date.today()

        candidates = [payment]

        results = await matcher.match(transaction, candidates)

        assert len(results) == 1
        assert results[0].confidence == Decimal("1.0")

    @pytest.mark.asyncio
    async def test_exact_amount_match_reason_descriptive(self):
        """Test that match reason is descriptive."""
        matcher = ExactAmountMatcher()

        transaction = Mock()
        transaction.amount = Decimal("1234.56")
        transaction.date = date.today()

        payment = Mock()
        payment.id = 1
        payment.importo_da_pagare = Decimal("1234.56")
        payment.data_scadenza = date.today()

        candidates = [payment]

        results = await matcher.match(transaction, candidates)

        assert "Exact amount" in results[0].match_reason
        assert "1234.56" in results[0].match_reason or "exact" in results[0].match_reason.lower()
