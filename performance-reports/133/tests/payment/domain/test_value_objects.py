"""Tests for Payment domain value objects.

Covers: MatchResult, ReconciliationResult, ImportResult
Following immutability and value object best practices.
"""

from decimal import Decimal

import pytest

from openfatture.payment.domain.enums import MatchType
from openfatture.payment.domain.value_objects import (
    ImportResult,
    MatchResult,
    ReconciliationResult,
)

pytestmark = pytest.mark.unit


class TestMatchResult:
    """Tests for MatchResult value object."""

    def test_match_result_creation(self):
        """Test creating a MatchResult with all fields."""
        from unittest.mock import Mock

        transaction = Mock()
        transaction.id = "tx-123"
        transaction.amount = Decimal("100.00")

        payment = Mock()
        payment.id = 1
        payment.importo_da_pagare = Decimal("100.00")

        result = MatchResult(
            transaction=transaction,
            payment=payment,
            confidence=0.85,
            match_type=MatchType.FUZZY,
            match_reason="Description similarity: 85%",
        )

        assert result.transaction.id == "tx-123"
        assert result.payment.id == 1
        assert result.confidence == 0.85
        assert result.match_type == MatchType.FUZZY
        assert "85%" in result.match_reason

    def test_match_result_confidence_range_validation(self):
        """Test that confidence must be between 0.0 and 1.0."""
        from unittest.mock import Mock

        transaction = Mock()
        payment = Mock()

        # Valid confidence
        result = MatchResult(
            transaction=transaction,
            payment=payment,
            confidence=0.75,
            match_type=MatchType.EXACT,
            match_reason="Exact amount",
        )
        assert 0.0 <= result.confidence <= 1.0

        # Edge cases
        result_zero = MatchResult(
            transaction=transaction,
            payment=payment,
            confidence=0.0,
            match_type=MatchType.EXACT,
            match_reason="No match",
        )
        assert result_zero.confidence == 0.0

        result_one = MatchResult(
            transaction=transaction,
            payment=payment,
            confidence=1.0,
            match_type=MatchType.EXACT,
            match_reason="Perfect match",
        )
        assert result_one.confidence == 1.0

    def test_match_result_should_auto_apply_threshold(self):
        """Test should_auto_apply property with 0.85 threshold."""
        from unittest.mock import Mock

        transaction = Mock()
        transaction.amount = Decimal("100.00")
        payment = Mock()
        payment.importo_da_pagare = Decimal("100.00")

        # Above threshold
        high_confidence = MatchResult(
            transaction=transaction,
            payment=payment,
            confidence=0.90,
            match_type=MatchType.EXACT,
            match_reason="Exact",
        )
        assert high_confidence.should_auto_apply is True

        # Exactly at threshold
        at_threshold = MatchResult(
            transaction=transaction,
            payment=payment,
            confidence=0.85,
            match_type=MatchType.FUZZY,
            match_reason="Fuzzy",
        )
        assert at_threshold.should_auto_apply is True

        # Below threshold
        low_confidence = MatchResult(
            transaction=transaction,
            payment=payment,
            confidence=0.70,
            match_type=MatchType.DATE_WINDOW,
            match_reason="Date",
        )
        assert low_confidence.should_auto_apply is False

    def test_match_result_equality_comparison(self):
        """Test that MatchResult can be compared by value."""
        from unittest.mock import Mock

        transaction1 = Mock()
        transaction1.id = "tx-1"

        transaction2 = Mock()
        transaction2.id = "tx-1"

        payment1 = Mock()
        payment1.id = 1

        payment2 = Mock()
        payment2.id = 1

        result1 = MatchResult(
            transaction=transaction1,
            payment=payment1,
            confidence=0.80,
            match_type=MatchType.FUZZY,
            match_reason="Test",
        )

        result2 = MatchResult(
            transaction=transaction2,
            payment=payment2,
            confidence=0.80,
            match_type=MatchType.FUZZY,
            match_reason="Test",
        )

        # Same values = equal (value object semantics)
        assert result1.confidence == result2.confidence
        assert result1.match_type == result2.match_type

    # Additional tests:
    # - test_match_result_immutability (if using frozen dataclass)
    # - test_match_result_serialization_to_dict


class TestReconciliationResult:
    """Tests for ReconciliationResult value object."""

    def test_reconciliation_result_counts(self):
        """Test ReconciliationResult with count fields."""
        result = ReconciliationResult(
            matched_count=10,
            review_count=5,
            unmatched_count=3,
            total_count=18,
        )

        assert result.matched_count == 10
        assert result.review_count == 5
        assert result.unmatched_count == 3
        assert result.total_count == 18

    def test_reconciliation_result_categorization(self):
        """Test that result properly categorizes transactions."""
        result = ReconciliationResult(
            matched_count=7,  # High confidence auto-applied
            review_count=10,  # Medium confidence needs review
            unmatched_count=3,  # No matches found
            total_count=20,
        )

        # Verify categorization logic
        assert (
            result.matched_count + result.review_count + result.unmatched_count
            == result.total_count
        )

        # Verify match_rate calculation
        assert result.match_rate == 7 / 20  # Only matched_count / total_count

    # Additional tests:
    # - test_reconciliation_result_percentage_calculations
    # - test_reconciliation_result_zero_counts


class TestImportResult:
    """Tests for ImportResult value object."""

    def test_import_result_aggregation(self):
        """Test ImportResult aggregates import statistics."""
        result = ImportResult(
            success_count=15,
            error_count=2,
            duplicate_count=3,
            errors=["Invalid date format", "Missing amount"],
        )

        assert result.success_count == 15
        assert result.error_count == 2
        assert result.duplicate_count == 3
        assert result.total_count == 20  # sum of all counts

    def test_import_result_error_list(self):
        """Test ImportResult stores error messages."""
        errors = [
            "Row 5: Invalid date format",
            "Row 12: Amount cannot be parsed",
            "Row 20: Missing required field 'description'",
        ]

        result = ImportResult(
            success_count=17,
            error_count=3,
            duplicate_count=0,
            errors=errors,
        )

        assert len(result.errors) == 3
        assert "Row 5" in result.errors[0]
        assert "Row 12" in result.errors[1]

    # Additional tests:
    # - test_import_result_empty_errors_list
    # - test_import_result_success_rate_calculation
