"""Tests for IBAN Matcher with SEPA multi-country support.

This module tests the IBANMatcher enhancement to support all 27 SEPA countries,
including format validation, country detection, and end-to-end matching across
multiple European countries.

Phase 1 Task 1.2: IBAN Multi-SEPA Support
"""

import re
from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest

from openfatture.payment.domain.enums import MatchType
from openfatture.payment.matchers.iban import IBANMatcher
from openfatture.payment.matchers.iban_formats import SEPAIBANFormats

pytestmark = pytest.mark.unit


class TestSEPAIBANFormats:
    """Test SEPA IBAN format registry and utilities."""

    def test_all_sepa_countries_registered(self):
        """Verify all SEPA countries are in registry.

        SEPA includes 27 EU members + 3 EEA members (IS, LI, NO) = 30 countries.
        """
        assert len(SEPAIBANFormats.FORMATS) == 30

        # Verify expected SEPA countries present
        expected_sepa_countries = {
            "AT",  # Austria
            "BE",  # Belgium
            "BG",  # Bulgaria
            "HR",  # Croatia
            "CY",  # Cyprus
            "CZ",  # Czech Republic
            "DK",  # Denmark
            "EE",  # Estonia
            "FI",  # Finland
            "FR",  # France
            "DE",  # Germany
            "GR",  # Greece
            "HU",  # Hungary
            "IS",  # Iceland
            "IE",  # Ireland
            "IT",  # Italy
            "LV",  # Latvia
            "LI",  # Liechtenstein
            "LT",  # Lithuania
            "LU",  # Luxembourg
            "MT",  # Malta
            "NL",  # Netherlands
            "NO",  # Norway
            "PL",  # Poland
            "PT",  # Portugal
            "RO",  # Romania
            "SK",  # Slovakia
            "SI",  # Slovenia
            "ES",  # Spain
            "SE",  # Sweden
        }
        # Note: UK (GB), Switzerland (CH) have IBAN but are not SEPA
        assert set(SEPAIBANFormats.FORMATS.keys()) == expected_sepa_countries

    def test_iban_format_immutable(self):
        """Test IBANFormat is frozen (immutable)."""
        from dataclasses import FrozenInstanceError

        fmt = SEPAIBANFormats.FORMATS["IT"]

        with pytest.raises(
            FrozenInstanceError
        ):  # Pydantic V2 frozen model raises FrozenInstanceError
            fmt.country_code = "XX"  # type: ignore

    def test_combined_pattern_generation(self):
        """Test combined regex pattern creation for all SEPA IBANs."""
        pattern = SEPAIBANFormats.get_combined_pattern()

        # Should contain all major country codes
        assert "IT" in pattern
        assert "DE" in pattern
        assert "FR" in pattern
        assert "ES" in pattern
        assert "NL" in pattern

        # Should be valid regex (compiles without errors)
        compiled = re.compile(pattern, re.IGNORECASE)
        assert compiled is not None

        # Should match real IBANs from various countries
        italian_iban = "IT60X0542811101000000123456"
        german_iban = "DE89370400440532013000"
        assert compiled.search(italian_iban)
        assert compiled.search(german_iban)

    @pytest.mark.parametrize(
        "country,iban",
        [
            ("IT", "IT60X0542811101000000123456"),
            ("DE", "DE89370400440532013000"),
            ("FR", "FR1420041010050500013M02606"),
            ("ES", "ES9121000418450200051332"),
            ("NL", "NL91ABNA0417164300"),
            ("AT", "AT611904300234573201"),
            ("BE", "BE68539007547034"),
            ("PT", "PT50000201231234567890154"),
        ],
    )
    def test_detect_country_valid_ibans(self, country, iban):
        """Test country detection from valid SEPA IBANs."""
        detected = SEPAIBANFormats.detect_country(iban)
        assert detected == country

    def test_detect_country_invalid_iban(self):
        """Test country detection with invalid/unknown country code."""
        # Unknown country (XX not in SEPA)
        assert SEPAIBANFormats.detect_country("XX1234567890") is None

        # Too short
        assert SEPAIBANFormats.detect_country("I") is None
        assert SEPAIBANFormats.detect_country("") is None

        # Non-SEPA but valid IBAN country (UK)
        assert SEPAIBANFormats.detect_country("GB82WEST12345698765432") is None

    @pytest.mark.parametrize(
        "country,iban,expected_length",
        [
            ("IT", "IT60X0542811101000000123456", 27),
            ("DE", "DE89370400440532013000", 22),
            ("FR", "FR1420041010050500013M02606", 27),
            ("NO", "NO9386011117947", 15),  # Shortest SEPA IBAN
            ("MT", "MT84MALT011000012345MTLCAST001S", 31),  # Longest SEPA IBAN
        ],
    )
    def test_validate_length_correct(self, country, iban, expected_length):
        """Test IBAN length validation with correct lengths."""
        assert len(iban) == expected_length
        assert SEPAIBANFormats.validate_length(iban) is True

    def test_validate_length_wrong(self):
        """Test IBAN length validation with incorrect lengths."""
        # Italian IBAN too short (25 instead of 27)
        wrong_iban_short = "IT60X05428111010000001234"
        assert SEPAIBANFormats.validate_length(wrong_iban_short) is False

        # German IBAN too long (24 instead of 22)
        wrong_iban_long = "DE893704004405320130000000"
        assert SEPAIBANFormats.validate_length(wrong_iban_long) is False

    def test_get_country_name(self):
        """Test retrieving full country name from IBAN."""
        assert SEPAIBANFormats.get_country_name("IT60X0542811101000000123456") == "Italy"
        assert SEPAIBANFormats.get_country_name("DE89370400440532013000") == "Germany"
        assert SEPAIBANFormats.get_country_name("FR1420041010050500013M02606") == "France"
        assert SEPAIBANFormats.get_country_name("ES9121000418450200051332") == "Spain"

        # Unknown country
        assert SEPAIBANFormats.get_country_name("XX1234567890") is None

    def test_list_supported_countries(self):
        """Test listing all supported SEPA country codes."""
        countries = SEPAIBANFormats.list_supported_countries()

        assert len(countries) == 30  # 27 EU + 3 EEA (IS, LI, NO)
        assert countries == sorted(countries)  # Should be alphabetically sorted
        assert "IT" in countries
        assert "DE" in countries
        assert "FR" in countries

    def test_get_example_iban(self):
        """Test retrieving example IBAN for a country."""
        italian_example = SEPAIBANFormats.get_example_iban("IT")
        assert italian_example == "IT60X0542811101000000123456"
        assert SEPAIBANFormats.validate_length(italian_example)

        german_example = SEPAIBANFormats.get_example_iban("DE")
        assert german_example == "DE89370400440532013000"

        # Unknown country
        assert SEPAIBANFormats.get_example_iban("XX") is None

    def test_full_pattern_property(self):
        """Test IBANFormat.full_pattern property."""
        it_format = SEPAIBANFormats.FORMATS["IT"]
        assert it_format.full_pattern == "IT" + it_format.pattern
        assert it_format.full_pattern == r"IT\d{2}[A-Z]\d{10}[0-9A-Z]{12}"


class TestIBANMatcherMultiCountry:
    """Test IBANMatcher with multiple SEPA countries."""

    @pytest.mark.parametrize(
        "country,iban,expected_country_name",
        [
            ("IT", "IT60X0542811101000000123456", "Italy"),
            ("DE", "DE89370400440532013000", "Germany"),
            ("FR", "FR1420041010050500013M02606", "France"),
            ("ES", "ES9121000418450200051332", "Spain"),
            ("NL", "NL91ABNA0417164300", "Netherlands"),
            ("AT", "AT611904300234573201", "Austria"),
            ("BE", "BE68539007547034", "Belgium"),
            ("PT", "PT50000201231234567890154", "Portugal"),
        ],
    )
    def test_match_various_countries(self, country, iban, expected_country_name):
        """Test matching works for various SEPA countries."""
        matcher = IBANMatcher()

        # Mock transaction with foreign IBAN in description
        transaction = Mock()
        transaction.id = f"tx-{country}-001"
        transaction.amount = Decimal("1000.00")
        transaction.description = f"Bank transfer to {iban}"
        transaction.date = date.today()
        transaction.reference = None
        transaction.memo = None
        transaction.note = None
        transaction.counterparty_iban = None

        # Mock payment with matching IBAN
        payment = Mock()
        payment.id = 1
        payment.iban = iban
        payment.beneficiary_iban = None
        payment.counterparty_iban = None
        payment.fattura = None
        payment.data_scadenza = date.today()
        payment.importo_totale = Decimal("1000.00")

        results = matcher.match(transaction, [payment])

        # Should find match
        assert len(results) == 1
        assert results[0].confidence >= 0.90
        assert expected_country_name in results[0].match_reason
        assert results[0].matched_fields == ["iban"]
        assert results[0].match_type == MatchType.IBAN

    def test_extract_mixed_country_ibans(self):
        """Test extraction of IBANs from multiple countries in same text."""
        matcher = IBANMatcher()

        transaction = Mock()
        transaction.id = "tx-multi-001"
        transaction.amount = Decimal("500.00")
        transaction.description = (
            "Transfer from IT60X0542811101000000123456 "
            "via DE89370400440532013000 "
            "to NL91ABNA0417164300"
        )
        transaction.date = date.today()
        transaction.reference = None
        transaction.memo = None
        transaction.note = None
        transaction.counterparty_iban = None

        ibans = matcher._extract_ibans(transaction)

        # Should extract all 3 IBANs (normalized)
        assert len(ibans) == 3
        assert "IT60X0542811101000000123456" in ibans
        assert "DE89370400440532013000" in ibans
        assert "NL91ABNA0417164300" in ibans

    def test_backward_compatibility_italian_iban(self):
        """Ensure Italian IBANs still work exactly as before (backward compatibility)."""
        matcher = IBANMatcher()

        # Same test as original implementation
        transaction = Mock()
        transaction.id = "tx-it-001"
        transaction.amount = Decimal("1000.00")
        transaction.description = "Bonifico a IT60X0542811101000000123456"
        transaction.date = date.today()
        transaction.reference = None
        transaction.memo = None
        transaction.note = None
        transaction.counterparty_iban = None

        payment = Mock()
        payment.id = 1
        payment.iban = "IT60X0542811101000000123456"
        payment.beneficiary_iban = None
        payment.counterparty_iban = None
        payment.fattura = None
        payment.data_scadenza = date.today()
        payment.importo_totale = Decimal("1000.00")

        results = matcher.match(transaction, [payment])

        # Should work exactly as before
        assert len(results) == 1
        assert results[0].confidence >= 0.90
        assert "Italy" in results[0].match_reason
        assert results[0].match_type == MatchType.IBAN

    def test_iban_with_spaces_normalized(self):
        """Test IBAN with spaces is normalized via counterparty_iban field.

        Note: Regex pattern doesn't match IBANs with spaces in free text,
        but normalization works for structured fields like counterparty_iban.
        """
        matcher = IBANMatcher()

        # Transaction has IBAN with spaces in counterparty field (structured data)
        transaction = Mock()
        transaction.id = "tx-spaces-001"
        transaction.amount = Decimal("2000.00")
        transaction.description = "Bank transfer"
        transaction.date = date.today()
        transaction.reference = None
        transaction.memo = None
        transaction.note = None
        transaction.counterparty_iban = "DE89 3704 0044 0532 0130 00"  # With spaces

        # Payment has normalized IBAN
        payment = Mock()
        payment.id = 1
        payment.iban = "DE89370400440532013000"  # Without spaces
        payment.beneficiary_iban = None
        payment.counterparty_iban = None
        payment.fattura = None
        payment.data_scadenza = date.today()
        payment.importo_totale = Decimal("2000.00")

        results = matcher.match(transaction, [payment])

        # Should match after normalization
        assert len(results) == 1
        assert "Germany" in results[0].match_reason

    def test_shortest_and_longest_sepa_ibans(self):
        """Test edge cases: shortest (Norway 15) and longest (Malta 31) IBANs."""
        matcher = IBANMatcher()

        # Norway: Shortest SEPA IBAN (15 characters)
        no_transaction = Mock()
        no_transaction.id = "tx-no-001"
        no_transaction.amount = Decimal("500.00")
        no_transaction.description = "Transfer to NO9386011117947"
        no_transaction.date = date.today()
        no_transaction.reference = None
        no_transaction.memo = None
        no_transaction.note = None
        no_transaction.counterparty_iban = None

        no_payment = Mock()
        no_payment.id = 1
        no_payment.iban = "NO9386011117947"
        no_payment.beneficiary_iban = None
        no_payment.counterparty_iban = None
        no_payment.fattura = None
        no_payment.data_scadenza = date.today()
        no_payment.importo_totale = Decimal("500.00")

        no_results = matcher.match(no_transaction, [no_payment])
        assert len(no_results) == 1
        assert "Norway" in no_results[0].match_reason

        # Malta: Longest SEPA IBAN (31 characters)
        mt_transaction = Mock()
        mt_transaction.id = "tx-mt-001"
        mt_transaction.amount = Decimal("1500.00")
        mt_transaction.description = "Transfer to MT84MALT011000012345MTLCAST001S"
        mt_transaction.date = date.today()
        mt_transaction.reference = None
        mt_transaction.memo = None
        mt_transaction.note = None
        mt_transaction.counterparty_iban = None

        mt_payment = Mock()
        mt_payment.id = 2
        mt_payment.iban = "MT84MALT011000012345MTLCAST001S"
        mt_payment.beneficiary_iban = None
        mt_payment.counterparty_iban = None
        mt_payment.fattura = None
        mt_payment.data_scadenza = date.today()
        mt_payment.importo_totale = Decimal("1500.00")

        mt_results = matcher.match(mt_transaction, [mt_payment])
        assert len(mt_results) == 1
        assert "Malta" in mt_results[0].match_reason

    def test_invalid_length_iban_rejected(self):
        """Test that IBANs with invalid length are not matched."""
        matcher = IBANMatcher()

        # Transaction with malformed IBAN (too short)
        transaction = Mock()
        transaction.id = "tx-invalid-001"
        transaction.amount = Decimal("1000.00")
        transaction.description = "Transfer to IT60X05428111010000001234"  # 25 chars (too short)
        transaction.date = date.today()
        transaction.reference = None
        transaction.memo = None
        transaction.note = None
        transaction.counterparty_iban = None

        # Payment with correct IBAN
        payment = Mock()
        payment.id = 1
        payment.iban = "IT60X0542811101000000123456"  # 27 chars (correct)
        payment.beneficiary_iban = None
        payment.counterparty_iban = None
        payment.fattura = None
        payment.data_scadenza = date.today()
        payment.importo_totale = Decimal("1000.00")

        # Extract IBANs should reject invalid length
        ibans = matcher._extract_ibans(transaction)
        assert len(ibans) == 0  # Invalid IBAN should be filtered out

    def test_match_confidence_with_amount_and_date(self):
        """Test confidence scoring with exact amount and date match."""
        matcher = IBANMatcher()

        transaction = Mock()
        transaction.id = "tx-confidence-001"
        transaction.amount = Decimal("-3456.78")  # Negative (outgoing payment)
        transaction.description = "Transfer from FR1420041010050500013M02606"
        transaction.date = date(2025, 10, 15)
        transaction.reference = None
        transaction.memo = None
        transaction.note = None
        transaction.counterparty_iban = None

        payment = Mock()
        payment.id = 1
        payment.iban = "FR1420041010050500013M02606"
        payment.beneficiary_iban = None
        payment.counterparty_iban = None
        payment.fattura = None
        payment.data_scadenza = date(2025, 10, 15)  # Same date
        payment.importo_da_pagare = Decimal("3456.78")  # Exact amount (positive)
        payment.importo_pagato = Decimal("0.00")  # Not yet paid
        payment.saldo_residuo = None  # Not set

        results = matcher.match(transaction, [payment])

        assert len(results) == 1
        # Base 0.90 + 0.05 (exact amount) + 0.05 (same date) = 1.00 (capped)
        assert results[0].confidence >= 0.95
        assert "France" in results[0].match_reason
        assert "exact amount" in results[0].match_reason
        assert "same date" in results[0].match_reason

    def test_repr_still_works(self):
        """Test IBANMatcher repr still works after modifications."""
        matcher = IBANMatcher(date_tolerance_days=45, amount_tolerance_pct=10.0)
        repr_str = repr(matcher)

        assert "IBANMatcher" in repr_str
        assert "45" in repr_str
        assert "10" in repr_str
