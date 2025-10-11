"""CSV importer with configurable field mapping.

Provides flexible CSV import with support for various formats and encodings.
"""

import csv
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import TYPE_CHECKING, Literal, overload

from dateutil import parser as dateutil_parser  # type: ignore[import-untyped]

from ...domain.enums import ImportSource
from ...domain.models import BankTransaction
from .base import BaseImporter

if TYPE_CHECKING:
    from ...domain.models import BankAccount


@dataclass
class CSVConfig:
    """Configuration for CSV import.

    Attributes:
        delimiter: CSV delimiter (default: auto-detect)
        encoding: File encoding (default: auto-detect)
        skip_rows: Number of header rows to skip
        skip_footer: Number of footer rows to skip
        field_mapping: Mapping of internal fields to CSV columns
        date_format: Date format string (e.g., "%d/%m/%Y")
        decimal_separator: Decimal separator ("." or ",")
        thousands_separator: Thousands separator (optional)
        optional_fields: Fields that can be missing
    """

    delimiter: str = ","
    encoding: str = "utf-8"
    skip_rows: int = 0
    skip_footer: int = 0

    # Field mapping: internal field name → CSV column name
    field_mapping: dict[str, str] = field(
        default_factory=lambda: {
            "date": "Date",
            "amount": "Amount",
            "description": "Description",
            "reference": "Reference",
        }
    )

    # Date parsing
    date_format: str = "%Y-%m-%d"  # ISO format default

    # Number parsing
    decimal_separator: str = "."
    thousands_separator: str | None = None

    # Optional fields (won't error if missing)
    optional_fields: list[str] = field(
        default_factory=lambda: [
            "reference",
            "counterparty",
            "counterparty_iban",
        ]
    )


class CSVImporter(BaseImporter):
    """Configurable CSV importer with field mapping.

    Features:
    - Auto-detect delimiter using csv.Sniffer
    - Auto-detect encoding (UTF-8, ISO-8859-1, CP1252)
    - Flexible field mapping via configuration
    - Multiple date format support with dateutil fallback
    - European decimal format support (1.234,56)
    - Encoding detection and handling
    - Duplicate detection based on hash

    Example:
        >>> config = CSVConfig(
        ...     delimiter=";",
        ...     encoding="ISO-8859-1",
        ...     field_mapping={
        ...         "date": "Data operazione",
        ...         "amount": "Importo",
        ...         "description": "Descrizione",
        ...     },
        ...     date_format="%d/%m/%Y",
        ...     decimal_separator=",",
        ... )
        >>> importer = CSVImporter(Path("statement.csv"), config)
        >>> transactions = importer.parse(account)
    """

    def __init__(self, file_path: Path, config: CSVConfig) -> None:
        """Initialize CSV importer with configuration.

        Args:
            file_path: Path to CSV file
            config: CSV configuration
        """
        super().__init__(file_path)
        self.config = config

    def parse(self, account: "BankAccount") -> list[BankTransaction]:
        """Parse CSV file and extract transactions.

        Algorithm:
        1. Detect delimiter if not specified
        2. Detect encoding if needed
        3. Read CSV with DictReader (memory efficient)
        4. Map fields according to configuration
        5. Parse and validate each row
        6. Create BankTransaction entities
        7. Deduplicate based on (date, amount, description)

        Args:
            account: BankAccount to associate transactions with

        Returns:
            List of parsed BankTransaction entities

        Raises:
            ValueError: If required fields are missing
            IOError: If file cannot be read
        """
        # Detect delimiter if auto
        if not self.config.delimiter or self.config.delimiter == "auto":
            self.config.delimiter = self._detect_delimiter()

        # Open file with correct encoding
        encoding = self.config.encoding or self.detect_encoding()

        transactions = []
        seen_hashes = set()  # For deduplication

        with open(self.file_path, encoding=encoding, errors="replace") as f:
            # Skip header rows
            for _ in range(self.config.skip_rows):
                next(f, None)

            # Create CSV reader
            reader = csv.DictReader(f, delimiter=self.config.delimiter)

            for row_num, row in enumerate(reader, start=self.config.skip_rows + 1):
                try:
                    # Parse transaction from row
                    transaction = self._parse_row(account, row)

                    # Deduplicate
                    tx_hash = self._hash_transaction(transaction)
                    if tx_hash in seen_hashes:
                        continue

                    seen_hashes.add(tx_hash)
                    transactions.append(transaction)

                except Exception as e:
                    # Log error but continue processing
                    # In production, would use proper logging
                    print(f"Warning: Skipping row {row_num}: {e}")
                    continue

        return transactions

    def _detect_delimiter(self) -> str:
        """Auto-detect CSV delimiter using csv.Sniffer.

        Returns:
            Detected delimiter (comma, semicolon, tab, or pipe)

        Raises:
            ValueError: If delimiter cannot be detected
        """
        with open(self.file_path, encoding=self.detect_encoding()) as f:
            # Read first 1KB for detection
            sample = f.read(1024)

        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample)
            return dialect.delimiter
        except csv.Error:
            # Fallback: Try common delimiters
            for delim in [",", ";", "\t", "|"]:
                if delim in sample:
                    return delim

            raise ValueError("Could not detect CSV delimiter")

    def _parse_row(self, account: "BankAccount", row: dict[str, str]) -> BankTransaction:
        """Parse a single CSV row into BankTransaction.

        Args:
            account: BankAccount
            row: CSV row as dictionary

        Returns:
            BankTransaction entity

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Extract fields using mapping
        date_str = self._get_field(row, "date", required=True)
        amount_str = self._get_field(row, "amount", required=True)
        description = self._get_field(row, "description", required=True)
        reference = self._get_field(row, "reference", required=False)
        counterparty = self._get_field(row, "counterparty", required=False)
        counterparty_iban = self._get_field(row, "counterparty_iban", required=False)

        # Parse date
        transaction_date = self._parse_date(date_str)

        # Parse amount
        amount = self._parse_decimal(amount_str)

        # Normalise description with reference/counterparty context
        description = self._normalize_description(
            description=description,
            reference=reference,
            counterparty=counterparty,
        )

        # Create transaction
        return BankTransaction(
            account=account,
            date=transaction_date,
            amount=amount,
            description=description,
            reference=reference,
            counterparty=counterparty,
            counterparty_iban=counterparty_iban,
            import_source=ImportSource.CSV,
            raw_data=row,  # Store original row for debugging
        )

    @overload
    def _get_field(
        self, row: dict[str, str], internal_name: str, required: Literal[True] = True
    ) -> str: ...

    @overload
    def _get_field(
        self, row: dict[str, str], internal_name: str, required: Literal[False]
    ) -> str | None: ...

    def _get_field(
        self, row: dict[str, str], internal_name: str, required: bool = True
    ) -> str | None:
        """Get field from CSV row using field mapping.

        Args:
            row: CSV row dictionary
            internal_name: Internal field name (e.g., "date")
            required: Whether field is required

        Returns:
            Field value or None if not required and missing

        Raises:
            ValueError: If required field is missing
        """
        csv_column = self.config.field_mapping.get(internal_name)

        if csv_column is None:
            if required and internal_name not in self.config.optional_fields:
                raise ValueError(f"Field mapping missing for: {internal_name}")
            return None

        value = row.get(csv_column, "").strip()

        if not value:
            if required and internal_name not in self.config.optional_fields:
                raise ValueError(f"Required field '{csv_column}' is empty")
            return None

        return value

    def _parse_date(self, date_str: str) -> date:
        """Parse date string with configured format or fallback.

        Args:
            date_str: Date string from CSV

        Returns:
            Parsed date

        Raises:
            ValueError: If date cannot be parsed
        """
        # Try configured format first
        try:
            return datetime.strptime(date_str, self.config.date_format).date()
        except ValueError:
            pass

        # Fallback: dateutil parser (handles many formats)
        try:
            parsed = dateutil_parser.parse(date_str, dayfirst=True)  # Italian format
            return parsed.date()
        except (ValueError, TypeError) as e:
            raise ValueError(f"Could not parse date: {date_str}") from e

    def _parse_decimal(self, value_str: str) -> Decimal:
        """Parse decimal number handling European format.

        Args:
            value_str: Number string (e.g., "1.234,56" or "1,234.56")

        Returns:
            Parsed Decimal

        Raises:
            ValueError: If number cannot be parsed
        """
        # Clean whitespace
        value_str = value_str.strip()

        # Remove thousands separator if specified
        if self.config.thousands_separator:
            value_str = value_str.replace(self.config.thousands_separator, "")

        # Replace decimal separator with dot
        if self.config.decimal_separator == ",":
            value_str = value_str.replace(",", ".")

        # Remove any remaining non-numeric characters except dot and minus
        value_str = re.sub(r"[^\d.\-]", "", value_str)

        try:
            return Decimal(value_str)
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f"Could not parse number: {value_str}") from e

    def _hash_transaction(self, transaction: BankTransaction) -> str:
        """Create hash for deduplication.

        Uses date + amount + first 50 chars of description.

        Args:
            transaction: BankTransaction

        Returns:
            Hash string
        """
        key = f"{transaction.date}|{transaction.amount}|{transaction.description[:50]}"
        return key

    def __repr__(self) -> str:
        """Human-readable string representation."""
        return (
            f"<CSVImporter("
            f"delimiter='{self.config.delimiter}', "
            f"encoding='{self.config.encoding}')>"
        )

    @staticmethod
    def _normalize_description(
        description: str,
        reference: str | None = None,
        counterparty: str | None = None,
    ) -> str:
        """Compose a richer description including reference/counterparty if present."""
        parts: list[str] = [description.strip()]

        if reference:
            reference_clean = reference.strip()
            if reference_clean and reference_clean.lower() not in description.lower():
                parts.append(reference_clean)

        if counterparty:
            counterparty_clean = counterparty.strip()
            if counterparty_clean and counterparty_clean.lower() not in description.lower():
                parts.append(counterparty_clean)

        # Remove duplicates while preserving order
        seen: set[str] = set()
        normalized_parts: list[str] = []
        for part in parts:
            key = part.lower()
            if key and key not in seen:
                seen.add(key)
                normalized_parts.append(part)

        return " - ".join(normalized_parts)
