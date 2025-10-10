"""Tests for IBANMatcher.

The IBANMatcher extracts IBAN codes from transaction descriptions/memos
and matches them against payment beneficiary IBANs.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest

from openfatture.payment.domain.enums import MatchType
from openfatture.payment.matchers.iban import IBANMatcher

pytestmark = pytest.mark.unit


class TestIBANMatcher:
    """Tests for IBANMatcher."""

    @pytest.mark.asyncio
    async def test_iban_full_match_in_description(self):
        """Test full IBAN match in transaction description."""
        matcher = IBANMatcher()

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.description = "Bonifico a IT60X0542811101000000123456"
        transaction.memo = None
        transaction.date = date.today()

        payment = Mock()
        payment.id = 1
        payment.importo_da_pagare = Decimal("1000.00")
        payment.data_scadenza = date.today()
        payment.fattura = Mock()
        payment.fattura.cliente = Mock()
        payment.fattura.cliente.iban = "IT60X0542811101000000123456"

        candidates = [payment]

        results = await matcher.match(transaction, candidates)

        assert len(results) == 1
        assert results[0].confidence == Decimal("1.0")
        assert results[0].match_type == MatchType.IBAN

    @pytest.mark.asyncio
    async def test_iban_partial_match_last_4_digits(self):
        """Test partial IBAN match using last 4 digits."""
        matcher = IBANMatcher()

        transaction = Mock()
        transaction.amount = Decimal("500.00")
        transaction.description = "Pagamento conto ...3456"  # Last 4 digits
        transaction.memo = None
        transaction.date = date.today()

        payment = Mock()
        payment.id = 1
        payment.importo_da_pagare = Decimal("500.00")
        payment.data_scadenza = date.today()
        payment.fattura = Mock()
        payment.fattura.cliente = Mock()
        payment.fattura.cliente.iban = "IT60X0542811101000000123456"  # Ends with 3456

        candidates = [payment]

        results = await matcher.match(transaction, candidates)

        # Partial match should have lower confidence than full match
        assert len(results) == 1
        assert Decimal("0.7") <= results[0].confidence < Decimal("1.0")

    @pytest.mark.asyncio
    async def test_iban_normalization_spaces_removed(self):
        """Test that spaces in IBAN are normalized."""
        matcher = IBANMatcher()

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        # IBAN with spaces (common formatting)
        transaction.description = "Bonifico IT60 X054 2811 1010 0000 0012 3456"
        transaction.memo = None
        transaction.date = date.today()

        payment = Mock()
        payment.id = 1
        payment.importo_da_pagare = Decimal("1000.00")
        payment.data_scadenza = date.today()
        payment.fattura = Mock()
        payment.fattura.cliente = Mock()
        payment.fattura.cliente.iban = "IT60X0542811101000000123456"  # No spaces

        candidates = [payment]

        results = await matcher.match(transaction, candidates)

        # Should match despite space differences
        assert len(results) == 1
        assert results[0].confidence > Decimal("0.8")

    @pytest.mark.asyncio
    async def test_iban_case_insensitive(self):
        """Test that IBAN matching is case-insensitive."""
        matcher = IBANMatcher()

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.description = "bonifico it60x0542811101000000123456"  # Lowercase
        transaction.memo = None
        transaction.date = date.today()

        payment = Mock()
        payment.id = 1
        payment.importo_da_pagare = Decimal("1000.00")
        payment.data_scadenza = date.today()
        payment.fattura = Mock()
        payment.fattura.cliente = Mock()
        payment.fattura.cliente.iban = "IT60X0542811101000000123456"  # Uppercase

        candidates = [payment]

        results = await matcher.match(transaction, candidates)

        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_iban_invalid_format_no_match(self):
        """Test that invalid IBAN format doesn't match."""
        matcher = IBANMatcher()

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.description = "Bonifico 1234567890"  # Not an IBAN
        transaction.memo = None
        transaction.date = date.today()

        payment = Mock()
        payment.id = 1
        payment.importo_da_pagare = Decimal("1000.00")
        payment.data_scadenza = date.today()
        payment.fattura = Mock()
        payment.fattura.cliente = Mock()
        payment.fattura.cliente.iban = "IT60X0542811101000000123456"

        candidates = [payment]

        results = await matcher.match(transaction, candidates)

        # No valid IBAN in description
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_iban_multiple_ibans_in_description(self):
        """Test handling of multiple IBANs in description."""
        matcher = IBANMatcher()

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.description = "Transfer from IT11A1234567890123456789012 to IT60X0542811101000000123456"
        transaction.memo = None
        transaction.date = date.today()

        payment = Mock()
        payment.id = 1
        payment.importo_da_pagare = Decimal("1000.00")
        payment.data_scadenza = date.today()
        payment.fattura = Mock()
        payment.fattura.cliente = Mock()
        payment.fattura.cliente.iban = "IT60X0542811101000000123456"  # Second IBAN

        candidates = [payment]

        results = await matcher.match(transaction, candidates)

        # Should match the correct IBAN
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_iban_in_memo_field(self):
        """Test IBAN extraction from memo field if description empty."""
        matcher = IBANMatcher()

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.description = "Payment"
        transaction.memo = "IBAN: IT60X0542811101000000123456"  # IBAN in memo
        transaction.date = date.today()

        payment = Mock()
        payment.id = 1
        payment.importo_da_pagare = Decimal("1000.00")
        payment.data_scadenza = date.today()
        payment.fattura = Mock()
        payment.fattura.cliente = Mock()
        payment.fattura.cliente.iban = "IT60X0542811101000000123456"

        candidates = [payment]

        results = await matcher.match(transaction, candidates)

        # Should find IBAN in memo field
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_iban_no_iban_in_payment_cliente(self):
        """Test behavior when payment cliente has no IBAN."""
        matcher = IBANMatcher()

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.description = "Bonifico IT60X0542811101000000123456"
        transaction.memo = None
        transaction.date = date.today()

        payment = Mock()
        payment.id = 1
        payment.importo_da_pagare = Decimal("1000.00")
        payment.data_scadenza = date.today()
        payment.fattura = Mock()
        payment.fattura.cliente = Mock()
        payment.fattura.cliente.iban = None  # No IBAN

        candidates = [payment]

        results = await matcher.match(transaction, candidates)

        # Cannot match without IBAN
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_iban_match_reason_includes_iban(self):
        """Test that match reason includes the matched IBAN."""
        matcher = IBANMatcher()

        transaction = Mock()
        transaction.amount = Decimal("1000.00")
        transaction.description = "Bonifico IT60X0542811101000000123456"
        transaction.memo = None
        transaction.date = date.today()

        payment = Mock()
        payment.id = 1
        payment.importo_da_pagare = Decimal("1000.00")
        payment.data_scadenza = date.today()
        payment.fattura = Mock()
        payment.fattura.cliente = Mock()
        payment.fattura.cliente.iban = "IT60X0542811101000000123456"

        candidates = [payment]

        results = await matcher.match(transaction, candidates)

        # Match reason should mention IBAN
        assert "IBAN" in results[0].match_reason or "IT60" in results[0].match_reason
