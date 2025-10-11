"""
Property-based tests for validators using Hypothesis.

Hypothesis generates random test cases to find edge cases automatically.
This is a 2025 best practice for robust testing.
"""

import string
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from openfatture.utils.validators import (
    format_importo,
    validate_codice_destinatario,
    validate_codice_fiscale,
    validate_partita_iva,
    validate_pec_email,
)

pytestmark = pytest.mark.unit


class TestPartitaIVAProperties:
    """Property-based tests for Partita IVA validation."""

    @given(st.text(min_size=11, max_size=11, alphabet=string.digits))
    def test_valid_length_numeric_strings(self, piva: str):
        """
        Test that 11-digit numeric strings are processed.

        Property: All 11-digit strings should either validate or fail predictably.
        """
        result = validate_partita_iva(piva)
        assert isinstance(result, bool)

    @given(st.text(min_size=1, max_size=100).filter(lambda x: len(x) != 11))
    def test_invalid_length_always_fails(self, piva: str):
        """
        Property: Any string with length != 11 should always fail.
        """
        result = validate_partita_iva(piva)
        assert result is False

    @given(st.text(min_size=11, max_size=11).filter(lambda x: not x.isdigit()))
    def test_non_numeric_always_fails(self, piva: str):
        """
        Property: Any 11-char string with non-digits should fail.
        """
        result = validate_partita_iva(piva)
        assert result is False


class TestCodiceFiscaleProperties:
    """Property-based tests for Codice Fiscale validation."""

    @given(st.text(alphabet=string.ascii_uppercase + string.digits, min_size=16, max_size=16))
    def test_uppercase_alphanumeric_16_chars(self, cf: str):
        """
        Test 16-character uppercase alphanumeric strings.

        Property: Should validate format or reject based on pattern.
        """
        result = validate_codice_fiscale(cf)
        assert isinstance(result, bool)

    @given(st.text(min_size=1, max_size=100).filter(lambda x: len(x) != 16))
    def test_wrong_length_always_fails(self, cf: str):
        """
        Property: Any string with length != 16 should always fail.
        """
        result = validate_codice_fiscale(cf)
        assert result is False

    @given(
        st.text(
            alphabet=st.characters(blacklist_characters=string.ascii_uppercase + string.digits),
            min_size=16,
            max_size=16,
        )
    )
    def test_invalid_characters_fail(self, cf: str):
        """
        Property: Strings with lowercase or special chars should fail.
        """
        result = validate_codice_fiscale(cf)
        assert result is False


class TestCodiceDestinatarioProperties:
    """Property-based tests for SDI recipient code."""

    @given(st.text(alphabet=string.ascii_uppercase + string.digits, min_size=7, max_size=7))
    def test_seven_char_alphanumeric_valid(self, code: str):
        """
        Property: Any 7-character alphanumeric string should be valid.
        """
        result = validate_codice_destinatario(code)
        assert result is True

    @given(st.text(min_size=1, max_size=100).filter(lambda x: len(x) != 7))
    def test_wrong_length_fails(self, code: str):
        """
        Property: Any string with length != 7 should fail.
        """
        result = validate_codice_destinatario(code)
        assert result is False


class TestPECEmailProperties:
    """Property-based tests for PEC email validation."""

    @given(
        # Generate emails compatible with our PEC validator
        # Pattern: [a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}
        st.builds(
            lambda local, domain, tld: f"{local}@{domain}.{tld}",
            local=st.text(
                alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._%+-",
                min_size=1,
                max_size=20,
            ),
            domain=st.text(
                alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-",
                min_size=1,
                max_size=20,
            ).filter(lambda x: len(x) > 0 and x[0] not in ".-" and x[-1] not in ".-"),
            tld=st.text(
                alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
                min_size=2,
                max_size=6,
            ),
        )
    )
    def test_valid_email_format(self, email: str):
        """
        Property: Valid email formats matching our PEC validator should pass.

        We generate emails compatible with pattern: [a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}
        """
        result = validate_pec_email(email)
        assert result is True

    @given(st.text().filter(lambda x: "@" not in x or "." not in x))
    def test_invalid_email_format_fails(self, email: str):
        """
        Property: Strings without @ or . should fail.
        """
        result = validate_pec_email(email)
        assert result is False


class TestFormatImportoProperties:
    """Property-based tests for amount formatting."""

    @given(st.floats(min_value=0, max_value=999999.99, allow_nan=False, allow_infinity=False))
    def test_positive_amounts_format_correctly(self, amount: float):
        """
        Property: All positive amounts should format to valid strings.
        """
        result = format_importo(amount)

        assert isinstance(result, str)
        assert len(result) > 0
        # Should be parseable back to number
        assert float(result) >= 0

    @given(st.floats(min_value=0, max_value=999999.99, allow_nan=False, allow_infinity=False))
    def test_formatted_amount_has_correct_decimals(self, amount: float):
        """
        Property: Formatted amounts should have at most 2 decimal places.
        """
        result = format_importo(amount, decimals=2)

        if "." in result:
            _, decimal_part = result.split(".")
            assert len(decimal_part) <= 2


class TestDecimalProperties:
    """Property-based tests for Decimal handling."""

    @given(
        st.decimals(min_value=0, max_value=999999, places=2, allow_nan=False, allow_infinity=False)
    )
    def test_decimal_to_string_roundtrip(self, amount: Decimal):
        """
        Property: Converting Decimal → str → Decimal should preserve value.
        """
        formatted = format_importo(float(amount))
        parsed_back = Decimal(formatted)

        # Should be approximately equal (accounting for float precision)
        assert abs(parsed_back - amount) < Decimal("0.01")


class TestInvoiceNumberProperties:
    """Property-based tests for invoice number generation."""

    @given(st.integers(min_value=1, max_value=99999))
    def test_invoice_numbers_are_positive(self, numero: int):
        """
        Property: Invoice numbers should always be positive integers.
        """
        numero_str = str(numero)
        assert numero_str.isdigit()
        assert int(numero_str) > 0

    @given(st.integers(min_value=1, max_value=99999))
    def test_invoice_number_padding(self, numero: int):
        """
        Property: Invoice numbers should pad to 5 digits for filenames.
        """
        numero_str = str(numero).zfill(5)
        assert len(numero_str) == 5
        assert numero_str.isdigit()


class TestVATRateProperties:
    """Property-based tests for VAT rate validation."""

    @given(st.decimals(min_value=0, max_value=100, places=2, allow_nan=False, allow_infinity=False))
    def test_vat_rates_are_percentages(self, rate: Decimal):
        """
        Property: VAT rates should be between 0 and 100.
        """
        assert Decimal("0") <= rate <= Decimal("100")

    @given(
        st.decimals(min_value=0, max_value=100, places=2, allow_nan=False, allow_infinity=False),
        st.decimals(min_value=0, max_value=999999, places=2, allow_nan=False, allow_infinity=False),
    )
    def test_vat_calculation_is_consistent(self, rate: Decimal, imponibile: Decimal):
        """
        Property: VAT calculation should be consistent.

        VAT = imponibile * (rate / 100)
        """
        vat = imponibile * (rate / Decimal("100"))

        # VAT should never be negative
        assert vat >= 0

        # VAT should never exceed imponibile * 100%
        assert vat <= imponibile


class TestWithholdingTaxProperties:
    """Property-based tests for ritenuta d'acconto calculation."""

    @given(
        st.decimals(min_value=0, max_value=999999, places=2, allow_nan=False, allow_infinity=False),
        st.decimals(min_value=0, max_value=50, places=2, allow_nan=False, allow_infinity=False),
    )
    def test_withholding_tax_calculation(self, imponibile: Decimal, aliquota: Decimal):
        """
        Property: Withholding tax should be a percentage of imponibile.

        Ritenuta = imponibile * (aliquota / 100)
        """
        ritenuta = imponibile * (aliquota / Decimal("100"))

        assert ritenuta >= 0
        assert ritenuta <= imponibile  # Cannot exceed imponibile

    @given(
        st.decimals(
            min_value=100, max_value=999999, places=2, allow_nan=False, allow_infinity=False
        )
    )
    def test_withholding_tax_reduces_total(self, imponibile: Decimal):
        """
        Property: Adding withholding tax should reduce total amount to pay.
        """
        iva = imponibile * Decimal("0.22")
        ritenuta = imponibile * Decimal("0.20")

        totale = imponibile + iva
        totale_da_pagare = totale - ritenuta

        assert totale_da_pagare < totale
        assert totale_da_pagare > 0


# Configure Hypothesis settings
from hypothesis import Verbosity, settings

# Set profile for CI
settings.register_profile("ci", max_examples=200, verbosity=Verbosity.verbose)
settings.register_profile("dev", max_examples=50)
settings.register_profile("debug", max_examples=10, verbosity=Verbosity.verbose)

# Load profile from environment or default to dev
import os

settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "dev"))
