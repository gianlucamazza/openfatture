"""SEPA IBAN formats for all 27 member countries.

This module provides comprehensive IBAN format definitions for all Single Euro Payments
Area (SEPA) countries, enabling multi-country bank account matching and validation.

Source: SWIFT IBAN Registry (January 2025)
Reference: https://www.swift.com/standards/data-standards/iban-international-bank-account-number

SEPA Countries (27 total):
    Austria, Belgium, Bulgaria, Croatia, Cyprus, Czech Republic, Denmark, Estonia,
    Finland, France, Germany, Greece, Hungary, Iceland, Ireland, Italy, Latvia,
    Liechtenstein, Lithuania, Luxembourg, Malta, Netherlands, Norway, Poland,
    Portugal, Romania, Slovakia, Slovenia, Spain, Sweden

Note: UK (GB), Switzerland (CH), and San Marino (SM) have IBAN but are not SEPA members.
"""

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class IBANFormat:
    """IBAN format specification for a specific country.

    Attributes:
        country_code: ISO 3166-1 alpha-2 code (e.g., "IT", "DE")
        country_name: Full country name in English
        length: Total IBAN length including country code and check digits
        pattern: Regex pattern for validation (excluding country code)
        example: Real-world example IBAN for testing
    """

    country_code: str
    country_name: str
    length: int
    pattern: str  # Regex pattern (without country code prefix)
    example: str

    @property
    def full_pattern(self) -> str:
        """Get complete regex pattern including country code.

        Returns:
            Full regex pattern like "IT\\d{2}[A-Z]\\d{10}[0-9A-Z]{12}"
        """
        return f"{self.country_code}{self.pattern}"


class SEPAIBANFormats:
    """Registry of SEPA IBAN formats with validation utilities.

    This class provides a centralized registry of IBAN formats for all 27 SEPA
    member countries, along with helper methods for pattern generation, country
    detection, and length validation.

    Usage:
        >>> # Get combined regex pattern for all SEPA countries
        >>> pattern = SEPAIBANFormats.get_combined_pattern()
        >>> import re
        >>> iban_regex = re.compile(pattern, re.IGNORECASE)

        >>> # Detect country from IBAN
        >>> country = SEPAIBANFormats.detect_country("IT60X0542811101000000123456")
        >>> assert country == "IT"

        >>> # Validate IBAN length
        >>> is_valid = SEPAIBANFormats.validate_length("DE89370400440532013000")
        >>> assert is_valid is True
    """

    FORMATS: ClassVar[dict[str, IBANFormat]] = {
        # Southern Europe
        "IT": IBANFormat(
            "IT",
            "Italy",
            27,
            r"\d{2}[A-Z]\d{10}[0-9A-Z]{12}",
            "IT60X0542811101000000123456",
        ),
        "ES": IBANFormat("ES", "Spain", 24, r"\d{22}", "ES9121000418450200051332"),
        "PT": IBANFormat("PT", "Portugal", 25, r"\d{23}", "PT50000201231234567890154"),
        "GR": IBANFormat(
            "GR",
            "Greece",
            27,
            r"\d{2}\d{3}\d{4}[A-Z0-9]{16}",
            "GR1601101250000000012300695",
        ),
        "MT": IBANFormat(
            "MT",
            "Malta",
            31,
            r"\d{2}[A-Z]{4}\d{5}[A-Z0-9]{18}",
            "MT84MALT011000012345MTLCAST001S",
        ),
        "CY": IBANFormat(
            "CY",
            "Cyprus",
            28,
            r"\d{2}\d{3}\d{5}[A-Z0-9]{16}",
            "CY17002001280000001200527600",
        ),
        "SI": IBANFormat("SI", "Slovenia", 19, r"\d{2}\d{5}\d{8}\d{2}", "SI56263300012039086"),
        "HR": IBANFormat("HR", "Croatia", 21, r"\d{19}", "HR1210010051863000160"),
        # Western Europe
        "FR": IBANFormat(
            "FR",
            "France",
            27,
            r"\d{12}[A-Z0-9]{11}\d{2}",
            "FR1420041010050500013M02606",
        ),
        "DE": IBANFormat("DE", "Germany", 22, r"\d{20}", "DE89370400440532013000"),
        "NL": IBANFormat("NL", "Netherlands", 18, r"\d{2}[A-Z]{4}\d{10}", "NL91ABNA0417164300"),
        "BE": IBANFormat("BE", "Belgium", 16, r"\d{14}", "BE68539007547034"),
        "LU": IBANFormat("LU", "Luxembourg", 20, r"\d{2}\d{3}[A-Z0-9]{13}", "LU280019400644750000"),
        "AT": IBANFormat("AT", "Austria", 20, r"\d{18}", "AT611904300234573201"),
        "LI": IBANFormat(
            "LI",
            "Liechtenstein",
            21,
            r"\d{2}\d{5}[A-Z0-9]{12}",
            "LI21088100002324013AA",
        ),
        # Northern Europe
        "IE": IBANFormat("IE", "Ireland", 22, r"\d{2}[A-Z]{4}\d{14}", "IE29AIBK93115212345678"),
        "DK": IBANFormat("DK", "Denmark", 18, r"\d{16}", "DK5000400440116243"),
        "FI": IBANFormat("FI", "Finland", 18, r"\d{16}", "FI2112345600000785"),
        "SE": IBANFormat("SE", "Sweden", 24, r"\d{22}", "SE4550000000058398257466"),
        "NO": IBANFormat("NO", "Norway", 15, r"\d{13}", "NO9386011117947"),
        "IS": IBANFormat("IS", "Iceland", 26, r"\d{24}", "IS140159260076545510730339"),
        # Eastern Europe
        "PL": IBANFormat("PL", "Poland", 28, r"\d{26}", "PL61109010140000071219812874"),
        "CZ": IBANFormat("CZ", "Czech Republic", 24, r"\d{22}", "CZ6508000000192000145399"),
        "SK": IBANFormat("SK", "Slovakia", 24, r"\d{22}", "SK3112000000198742637541"),
        "HU": IBANFormat("HU", "Hungary", 28, r"\d{26}", "HU42117730161111101800000000"),
        "RO": IBANFormat(
            "RO",
            "Romania",
            24,
            r"\d{2}[A-Z]{4}[A-Z0-9]{16}",
            "RO49AAAA1B31007593840000",
        ),
        "BG": IBANFormat(
            "BG",
            "Bulgaria",
            22,
            r"\d{2}[A-Z]{4}\d{14}",
            "BG80BNBG96611020345678",
        ),
        # Baltic States
        "EE": IBANFormat("EE", "Estonia", 20, r"\d{18}", "EE382200221020145685"),
        "LV": IBANFormat("LV", "Latvia", 21, r"\d{2}[A-Z]{4}[A-Z0-9]{13}", "LV80BANK0000435195001"),
        "LT": IBANFormat("LT", "Lithuania", 20, r"\d{18}", "LT121000011101001000"),
    }

    @classmethod
    def get_combined_pattern(cls) -> str:
        """Generate single regex pattern matching all SEPA IBANs.

        Creates a combined regex pattern using alternation (|) that matches
        any valid IBAN from all 27 SEPA countries. Each country pattern is
        wrapped in a non-capturing group for proper matching.

        Returns:
            Combined regex pattern like:
            "(?:IT\\d{2}[A-Z]...)|(?:DE\\d{20})|(?:FR\\d{12}...)|..."

        Example:
            >>> pattern = SEPAIBANFormats.get_combined_pattern()
            >>> import re
            >>> iban_regex = re.compile(pattern, re.IGNORECASE)
            >>> bool(iban_regex.search("Transfer to IT60X0542811101000000123456"))
            True
            >>> bool(iban_regex.search("Payment from DE89370400440532013000"))
            True
        """
        patterns = [f"(?:{fmt.full_pattern})" for fmt in cls.FORMATS.values()]
        return "|".join(patterns)

    @classmethod
    def detect_country(cls, iban: str) -> str | None:
        """Detect country code from IBAN string.

        Extracts the first two characters and checks if they correspond to
        a registered SEPA country code.

        Args:
            iban: IBAN string (normalized or raw, case-insensitive)

        Returns:
            ISO 3166-1 alpha-2 country code (e.g., "IT", "DE") if recognized,
            None if IBAN is too short or country not in SEPA

        Example:
            >>> SEPAIBANFormats.detect_country("IT60X0542811101000000123456")
            'IT'
            >>> SEPAIBANFormats.detect_country("DE89370400440532013000")
            'DE'
            >>> SEPAIBANFormats.detect_country("GB82WEST12345698765432")  # UK not SEPA
            None
        """
        if not iban or len(iban) < 2:
            return None

        country_code = iban[:2].upper()
        return country_code if country_code in cls.FORMATS else None

    @classmethod
    def validate_length(cls, iban: str) -> bool:
        """Validate IBAN length matches country-specific format.

        Checks if the IBAN length is correct for the detected country.
        IBAN lengths vary from 15 (Norway) to 31 (Malta) characters.

        Args:
            iban: IBAN string (normalized: uppercase, no spaces)

        Returns:
            True if length matches expected format for detected country,
            False if country not recognized or length mismatch

        Example:
            >>> SEPAIBANFormats.validate_length("IT60X0542811101000000123456")
            True
            >>> SEPAIBANFormats.validate_length("IT60X05428111010000001234")  # Too short
            False
            >>> SEPAIBANFormats.validate_length("NO9386011117947")  # Norway (15 chars)
            True
            >>> SEPAIBANFormats.validate_length("MT84MALT011000012345MTLCAST001S")  # Malta (31 chars)
            True
        """
        country_code = cls.detect_country(iban)
        if not country_code:
            return False

        expected_length = cls.FORMATS[country_code].length
        return len(iban) == expected_length

    @classmethod
    def get_country_name(cls, iban: str) -> str | None:
        """Get full country name from IBAN.

        Args:
            iban: IBAN string

        Returns:
            Full country name (e.g., "Italy", "Germany") or None if not recognized

        Example:
            >>> SEPAIBANFormats.get_country_name("IT60X0542811101000000123456")
            'Italy'
            >>> SEPAIBANFormats.get_country_name("DE89370400440532013000")
            'Germany'
        """
        country_code = cls.detect_country(iban)
        if not country_code:
            return None

        return cls.FORMATS[country_code].country_name

    @classmethod
    def list_supported_countries(cls) -> list[str]:
        """Get list of all supported SEPA country codes.

        Returns:
            Sorted list of ISO 3166-1 alpha-2 country codes

        Example:
            >>> countries = SEPAIBANFormats.list_supported_countries()
            >>> len(countries)
            27
            >>> "IT" in countries
            True
            >>> "DE" in countries
            True
        """
        return sorted(cls.FORMATS.keys())

    @classmethod
    def get_example_iban(cls, country_code: str) -> str | None:
        """Get example IBAN for a specific country.

        Args:
            country_code: ISO 3166-1 alpha-2 code (e.g., "IT", "DE")

        Returns:
            Example IBAN string or None if country not found

        Example:
            >>> SEPAIBANFormats.get_example_iban("IT")
            'IT60X0542811101000000123456'
            >>> SEPAIBANFormats.get_example_iban("DE")
            'DE89370400440532013000'
        """
        country_code = country_code.upper()
        if country_code not in cls.FORMATS:
            return None

        return cls.FORMATS[country_code].example
