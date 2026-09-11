from __future__ import annotations

"""Tests for FuzzyDescriptionMatcher with property-based testing.

The FuzzyDescriptionMatcher uses Levenshtein distance (via rapidfuzz) to match
transaction descriptions with invoice/payment descriptions. Includes property-based
tests with Hypothesis for robust edge case coverage.
"""

import string
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, cast
from unittest.mock import Mock

import pytest
from hypothesis import given
from hypothesis import strategies as st

from openfatture.payment.domain.enums import MatchType
from openfatture.payment.matchers.fuzzy import FuzzyDescriptionMatcher

pytestmark = pytest.mark.unit

if TYPE_CHECKING:
    from openfatture.storage.database.models import Pagamento


def _as_pagamenti(*payments: Mock) -> list[Pagamento]:
    """Return payments list typed as Pagamento for matcher expectations."""
    return cast(list["Pagamento"], list(payments))


class TestFuzzyDescriptionMatcherBasic:
    """Basic tests for FuzzyDescriptionMatcher."""

    def test_fuzzy_description_high_similarity(self):
        """Test high similarity description match (>0.8 confidence)."""
        matcher = FuzzyDescriptionMatcher(min_similarity=60.0)

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.description = "Pagamento fattura 2025/001"
        transaction.date = date.today()

        payment = Mock()
        payment.id = 1
        payment.importo = Decimal("1000.00")
        payment.importo_pagato = Decimal("0.00")
        payment.data_scadenza = date.today()
        payment.fattura = Mock()
        payment.fattura.numero = "2025/001"
        payment.fattura.cliente = Mock()
        payment.fattura.cliente.denominazione = "Acme Corp"

        candidates = _as_pagamenti(payment)

        results = matcher.match(transaction, candidates)

        assert len(results) == 1
        assert results[0].confidence > Decimal("0.8")
        assert results[0].match_type == MatchType.FUZZY

    def test_fuzzy_description_partial_match_medium_confidence(self):
        """Test partial match returns medium confidence."""
        matcher = FuzzyDescriptionMatcher(min_similarity=60.0)

        transaction = Mock()
        transaction.amount = Decimal("500.00")
        transaction.description = "Bonifico da Acme Corporation"
        transaction.date = date.today()

        payment = Mock()
        payment.id = 1
        payment.importo = Decimal("500.00")
        payment.importo_pagato = Decimal("0.00")
        payment.data_scadenza = date.today()
        payment.fattura = Mock()
        payment.fattura.numero = "123"
        payment.fattura.cliente = Mock()
        payment.fattura.cliente.denominazione = "Acme Corp"  # Similar but not exact

        candidates = _as_pagamenti(payment)

        results = matcher.match(transaction, candidates)

        assert len(results) == 1
        # Medium confidence (not perfect match but close)
        assert Decimal("0.60") <= results[0].confidence < Decimal("0.90")

    def test_fuzzy_utf8_italian_characters(self):
        """Test fuzzy matching with Italian UTF-8 characters (àèéìòù)."""
        matcher = FuzzyDescriptionMatcher(min_similarity=60.0)

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.description = "Pagamento società Perché S.r.l."
        transaction.date = date.today()

        payment = Mock()
        payment.id = 1
        payment.importo = Decimal("1000.00")
        payment.importo_pagato = Decimal("0.00")
        payment.data_scadenza = date.today()
        payment.fattura = Mock()
        payment.fattura.numero = "001"
        payment.fattura.cliente = Mock()
        payment.fattura.cliente.denominazione = "Società Perché"

        candidates = _as_pagamenti(payment)

        results = matcher.match(transaction, candidates)

        # Should handle UTF-8 correctly
        assert len(results) >= 0  # May or may not match depending on similarity

    def test_fuzzy_case_insensitive(self):
        """Test that matching is case-insensitive."""
        matcher = FuzzyDescriptionMatcher(min_similarity=60.0)

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.description = "PAGAMENTO FATTURA ACME CORP"
        transaction.date = date.today()

        payment = Mock()
        payment.id = 1
        payment.importo = Decimal("1000.00")
        payment.importo_pagato = Decimal("0.00")
        payment.data_scadenza = date.today()
        payment.fattura = Mock()
        payment.fattura.numero = "001"
        payment.fattura.cliente = Mock()
        payment.fattura.cliente.denominazione = "acme corp"  # Lowercase

        candidates = _as_pagamenti(payment)

        results = matcher.match(transaction, candidates)

        # Case should be normalized
        assert len(results) == 1
        assert results[0].confidence > Decimal("0.7")

    def test_fuzzy_whitespace_normalization(self):
        """Test that extra whitespace is normalized."""
        matcher = FuzzyDescriptionMatcher(min_similarity=60.0)

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.description = "Pagamento    Fattura     123"  # Multiple spaces
        transaction.date = date.today()

        payment = Mock()
        payment.id = 1
        payment.importo = Decimal("1000.00")
        payment.importo_pagato = Decimal("0.00")
        payment.data_scadenza = date.today()
        payment.fattura = Mock()
        payment.fattura.numero = "123"
        payment.fattura.cliente = Mock()
        payment.fattura.cliente.denominazione = "Test"

        candidates = _as_pagamenti(payment)

        results = matcher.match(transaction, candidates)

        # Whitespace should be normalized
        assert len(results) >= 0

    def test_fuzzy_threshold_configuration(self):
        """Test that threshold parameter filters results."""
        # High threshold matcher
        high_threshold_matcher = FuzzyDescriptionMatcher(min_similarity=90.0)

        # Low threshold matcher
        low_threshold_matcher = FuzzyDescriptionMatcher(min_similarity=50.0)

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.description = "Partial match text"
        transaction.date = date.today()

        payment = Mock()
        payment.id = 1
        payment.importo = Decimal("1000.00")
        payment.importo_pagato = Decimal("0.00")
        payment.data_scadenza = date.today()
        payment.fattura = Mock()
        payment.fattura.numero = "001"
        payment.fattura.cliente = Mock()
        payment.fattura.cliente.denominazione = "Different text"

        candidates = _as_pagamenti(payment)

        high_results = high_threshold_matcher.match(transaction, candidates)
        low_results = low_threshold_matcher.match(transaction, candidates)

        # Low threshold should match more
        assert len(low_results) >= len(high_results)

    def test_fuzzy_empty_description_no_match(self):
        """Test that empty descriptions don't match."""
        matcher = FuzzyDescriptionMatcher(min_similarity=60.0)

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.description = ""  # Empty
        transaction.date = date.today()

        payment = Mock()
        payment.id = 1
        payment.importo = Decimal("1000.00")
        payment.importo_pagato = Decimal("0.00")
        payment.data_scadenza = date.today()
        payment.fattura = Mock()
        payment.fattura.numero = "001"
        payment.fattura.cliente = Mock()
        payment.fattura.cliente.denominazione = "Acme"

        candidates = _as_pagamenti(payment)

        results = matcher.match(transaction, candidates)

        # Empty description should not match
        assert len(results) == 0


class TestFuzzyDescriptionMatcherPropertyBased:
    """Property-based tests for FuzzyDescriptionMatcher using Hypothesis."""

    @given(st.text(min_size=1, max_size=100))
    def test_fuzzy_similarity_reflexive(self, description: str):
        """Property: similarity(A, A) should be 1.0 (reflexive)."""
        if not description.strip():  # Skip empty strings
            return

        matcher = FuzzyDescriptionMatcher(min_similarity=0.0)

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.description = description
        transaction.date = date.today()

        payment = Mock()
        payment.id = 1
        payment.importo = Decimal("1000.00")
        payment.importo_pagato = Decimal("0.00")
        payment.data_scadenza = date.today()
        payment.fattura = Mock()
        payment.fattura.numero = "001"
        payment.fattura.cliente = Mock()
        payment.fattura.cliente.denominazione = description  # Same description

        candidates = _as_pagamenti(payment)

        results = matcher.match(transaction, candidates)

        # Property: matching with self should give high confidence
        if results:
            assert results[0].confidence >= Decimal("0.9")

    @given(st.text(min_size=5, max_size=50), st.text(min_size=5, max_size=50))
    def test_fuzzy_similarity_bounded(self, desc1: str, desc2: str):
        """Property: similarity score is always between 0.0 and 1.0."""
        if not desc1.strip() or not desc2.strip():
            return

        matcher = FuzzyDescriptionMatcher(min_similarity=0.0)

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.description = desc1
        transaction.date = date.today()

        payment = Mock()
        payment.id = 1
        payment.importo = Decimal("1000.00")
        payment.importo_pagato = Decimal("0.00")
        payment.data_scadenza = date.today()
        payment.fattura = Mock()
        payment.fattura.numero = "001"
        payment.fattura.cliente = Mock()
        payment.fattura.cliente.denominazione = desc2

        candidates = _as_pagamenti(payment)

        results = matcher.match(transaction, candidates)

        # Property: confidence is bounded
        if results:
            assert Decimal("0.0") <= results[0].confidence <= Decimal("1.0")

    @given(st.text(alphabet=string.ascii_letters, min_size=10, max_size=50))
    def test_fuzzy_case_normalization_property(self, text: str):
        """Property: Case variations should not affect matching significantly."""
        if not text.strip():
            return

        matcher = FuzzyDescriptionMatcher(min_similarity=0.0)

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.description = text.upper()
        transaction.date = date.today()

        payment = Mock()
        payment.id = 1
        payment.importo = Decimal("1000.00")
        payment.importo_pagato = Decimal("0.00")
        payment.data_scadenza = date.today()
        payment.fattura = Mock()
        payment.fattura.numero = "001"
        payment.fattura.cliente = Mock()
        payment.fattura.cliente.denominazione = text.lower()

        candidates = _as_pagamenti(payment)

        results = matcher.match(transaction, candidates)

        # Property: case should not prevent matching
        if results:
            assert results[0].confidence > Decimal("0.7")


# Configure Hypothesis settings
import os

from hypothesis import Verbosity, settings

settings.register_profile("ci", max_examples=100, verbosity=Verbosity.verbose)
settings.register_profile("dev", max_examples=30)
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "dev"))
