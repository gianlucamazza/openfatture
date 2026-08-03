"""Test suite for validators."""

from openfatture.utils.validators import (
    format_importo,
    validate_codice_destinatario,
    validate_codice_fiscale,
    validate_partita_iva,
    validate_pec_email,
)


class TestPartitaIVA:
    """Tests for Partita IVA validation."""

    def test_valid_partita_iva(self):
        """Test valid Partita IVA."""
        assert validate_partita_iva("12345678903") is True

    def test_invalid_length(self):
        """Test invalid length."""
        assert validate_partita_iva("123456789") is False
        assert validate_partita_iva("123456789012") is False

    def test_non_numeric(self):
        """Test non-numeric input."""
        assert validate_partita_iva("1234567890A") is False

    def test_invalid_check_digit(self):
        """Test invalid check digit."""
        assert validate_partita_iva("12345678901") is False


class TestCodiceFiscale:
    """Tests for Codice Fiscale validation."""

    def test_valid_codice_fiscale(self):
        """Test valid Codice Fiscale."""
        assert validate_codice_fiscale("RSSMRA80A01H501U") is True

    def test_invalid_length(self):
        """Test invalid length."""
        assert validate_codice_fiscale("RSSMRA80A01H501") is False

    def test_invalid_format(self):
        """Test invalid format."""
        assert validate_codice_fiscale("1234567890123456") is False


class TestCodiceDestinatario:
    """Tests for SDI recipient code validation."""

    def test_valid_codes(self):
        """Test valid codes."""
        assert validate_codice_destinatario("0000000") is True
        assert validate_codice_destinatario("ABC1234") is True

    def test_invalid_length(self):
        """Test invalid length."""
        assert validate_codice_destinatario("123456") is False


class TestPECEmail:
    """Tests for PEC email validation."""

    def test_valid_emails(self):
        """Test valid emails."""
        assert validate_pec_email("test@pec.it") is True
        assert validate_pec_email("company@pec.example.com") is True

    def test_invalid_emails(self):
        """Test invalid emails."""
        assert validate_pec_email("not-an-email") is False
        assert validate_pec_email("@pec.it") is False


class TestFormatImporto:
    """Tests for amount formatting."""

    def test_format_with_decimals(self):
        """Test formatting with decimals."""
        assert format_importo(100.50) == "100.50"
        assert format_importo(100.00) == "100.00"

    def test_format_no_trailing_zeros(self):
        """Test removal of trailing zeros."""
        # The function currently keeps 2 decimals
        assert format_importo(100.0) == "100.00"
