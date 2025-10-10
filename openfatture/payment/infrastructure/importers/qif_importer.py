"""QIF (Quicken Interchange Format) importer.

Supports legacy Quicken format used by older financial software.
"""

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import TYPE_CHECKING

from ...domain.enums import ImportSource
from ...domain.models import BankTransaction
from .base import BaseImporter

if TYPE_CHECKING:
    from ...domain.models import BankAccount


class QIFImporter(BaseImporter):
    """QIF (Quicken Interchange Format) importer.

    Supports:
    - Bank account transactions (!Type:Bank)
    - Credit card transactions (!Type:CCard)
    - Investment transactions (basic support)
    - Split transactions (combined into single entry)
    - Various date formats (US and European)

    QIF Field Codes:
    - D: Date (MM/DD/YYYY or DD/MM/YYYY)
    - T: Amount (negative for debits)
    - P: Payee/Description
    - M: Memo
    - N: Check number/Reference
    - C: Cleared status (*, c, X)
    - ^: End of transaction marker

    Example QIF file:
        !Type:Bank
        D01/15/2024
        T-150.00
        PGrocery Store
        MWeekly shopping
        ^
        D01/20/2024
        T500.00
        PSalary
        ^

    Example:
        >>> importer = QIFImporter(Path("statement.qif"))
        >>> transactions = importer.parse(account)
        >>> print(f"Imported {len(transactions)} transactions")
    """

    # Supported account types
    SUPPORTED_TYPES = ["Bank", "CCard", "Cash", "Oth A", "Oth L"]

    def __init__(self, file_path: Path, date_format: str = "auto") -> None:
        """Initialize QIF importer.

        Args:
            file_path: Path to QIF file
            date_format: Date format ("auto", "US" for MM/DD/YYYY, "EU" for DD/MM/YYYY)
        """
        super().__init__(file_path)
        self.date_format = date_format

    def parse(self, account: "BankAccount") -> list[BankTransaction]:
        """Parse QIF file and extract transactions.

        Algorithm:
        1. Read file line by line
        2. Detect account type (!Type:Bank)
        3. Use state machine to parse transactions
        4. Each transaction ends with ^ marker
        5. Accumulate fields (D, T, P, M, N) until ^
        6. Create BankTransaction from accumulated fields
        7. Handle split transactions (combine amounts)

        Args:
            account: BankAccount to associate transactions with

        Returns:
            List of parsed BankTransaction entities

        Raises:
            ValueError: If QIF format is invalid or unsupported type
        """
        encoding = self.detect_encoding()
        transactions = []
        current_tx = {}
        account_type = None

        with open(self.file_path, "r", encoding=encoding, errors="replace") as f:
            for line_num, line in enumerate(f, start=1):
                line = line.strip()

                # Skip empty lines
                if not line:
                    continue

                # Check for account type header
                if line.startswith("!Type:"):
                    account_type = line[6:].strip()
                    if account_type not in self.SUPPORTED_TYPES:
                        print(
                            f"Warning: Unsupported QIF type '{account_type}', attempting to parse anyway"
                        )
                    continue

                # Parse field code
                if len(line) < 1:
                    continue

                field_code = line[0]
                field_value = line[1:].strip() if len(line) > 1 else ""

                # End of transaction marker
                if field_code == "^":
                    if current_tx:
                        try:
                            transaction = self._parse_transaction(account, current_tx)
                            transactions.append(transaction)
                        except Exception as e:
                            print(f"Warning: Skipping transaction at line {line_num}: {e}")
                        current_tx = {}
                    continue

                # Accumulate transaction fields
                if field_code == "D":
                    current_tx["date"] = field_value
                elif field_code == "T":
                    current_tx["amount"] = field_value
                elif field_code == "P":
                    current_tx["payee"] = field_value
                elif field_code == "M":
                    current_tx["memo"] = field_value
                elif field_code == "N":
                    current_tx["reference"] = field_value
                elif field_code == "C":
                    current_tx["cleared"] = field_value
                elif field_code == "S":
                    # Split category (ignore for now)
                    pass
                elif field_code == "E":
                    # Split memo (ignore for now)
                    pass
                elif field_code == "$":
                    # Split amount (accumulate into total)
                    if "split_amounts" not in current_tx:
                        current_tx["split_amounts"] = []
                    current_tx["split_amounts"].append(field_value)

        # Handle last transaction if file doesn't end with ^
        if current_tx:
            try:
                transaction = self._parse_transaction(account, current_tx)
                transactions.append(transaction)
            except Exception as e:
                print(f"Warning: Skipping final transaction: {e}")

        return transactions

    def _parse_transaction(self, account: "BankAccount", tx_data: dict) -> BankTransaction:
        """Parse accumulated QIF transaction fields into BankTransaction.

        Args:
            account: BankAccount entity
            tx_data: Dictionary of accumulated field values

        Returns:
            BankTransaction entity

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Extract and validate required fields
        if "date" not in tx_data:
            raise ValueError("Missing required field: Date (D)")
        if "amount" not in tx_data:
            raise ValueError("Missing required field: Amount (T)")

        # Parse date
        transaction_date = self._parse_date(tx_data["date"])

        # Parse amount (handle split transactions)
        if "split_amounts" in tx_data and tx_data["split_amounts"]:
            # Sum split amounts
            amount = sum(self._parse_decimal(amt) for amt in tx_data["split_amounts"])
        else:
            amount = self._parse_decimal(tx_data["amount"])

        # Build description (Payee + Memo)
        description = self._build_description(tx_data)

        # Extract reference (check number or N field)
        reference = tx_data.get("reference")

        # Extract counterparty (Payee)
        counterparty = tx_data.get("payee")

        # Build raw data for debugging
        raw_data = {
            "date_str": tx_data.get("date"),
            "amount_str": tx_data.get("amount"),
            "payee": tx_data.get("payee"),
            "memo": tx_data.get("memo"),
            "reference": tx_data.get("reference"),
            "cleared": tx_data.get("cleared"),
            "split_amounts": tx_data.get("split_amounts"),
        }

        return BankTransaction(
            account=account,
            date=transaction_date,
            amount=amount,
            description=description,
            reference=reference,
            counterparty=counterparty,
            counterparty_iban=None,  # QIF doesn't include IBAN
            import_source=ImportSource.QIF,
            raw_data=raw_data,
        )

    def _parse_date(self, date_str: str) -> datetime.date:
        """Parse QIF date with format detection.

        Supports:
        - US format: MM/DD/YYYY or MM-DD-YYYY or MM/DD/YY
        - EU format: DD/MM/YYYY or DD-MM-YYYY or DD/MM/YY
        - ISO format: YYYY-MM-DD

        Args:
            date_str: Date string from QIF

        Returns:
            Parsed date

        Raises:
            ValueError: If date cannot be parsed
        """
        # Normalize separators
        date_str = date_str.replace("/", "-").replace(".", "-").replace(" ", "-")

        # Try ISO format first (YYYY-MM-DD)
        if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            try:
                return datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                pass

        # Detect format based on position of year
        parts = date_str.split("-")
        if len(parts) != 3:
            raise ValueError(f"Invalid date format: {date_str}")

        # Convert 2-digit years to 4-digit
        parts = [p.zfill(2) for p in parts]
        for i, part in enumerate(parts):
            if len(part) == 2 and part.isdigit():
                year_int = int(part)
                # Assume 20xx for years < 50, 19xx for years >= 50
                parts[i] = f"20{part}" if year_int < 50 else f"19{part}"

        # Try to detect format
        if self.date_format == "US" or (
            self.date_format == "auto" and len(parts[0]) <= 2 and int(parts[0]) <= 12
        ):
            # US format: MM-DD-YYYY
            try:
                month, day, year = parts
                return datetime(int(year), int(month), int(day)).date()
            except (ValueError, IndexError):
                pass

        if self.date_format == "EU" or self.date_format == "auto":
            # EU format: DD-MM-YYYY
            try:
                day, month, year = parts
                return datetime(int(year), int(month), int(day)).date()
            except (ValueError, IndexError):
                pass

        # Final fallback: try both formats
        for fmt in ["%m-%d-%Y", "%d-%m-%Y"]:
            try:
                return datetime.strptime("-".join(parts), fmt).date()
            except ValueError:
                continue

        raise ValueError(f"Could not parse date: {date_str}")

    def _parse_decimal(self, amount_str: str) -> Decimal:
        """Parse QIF amount string.

        Args:
            amount_str: Amount string (e.g., "-150.00", "1,234.56")

        Returns:
            Parsed Decimal

        Raises:
            ValueError: If amount cannot be parsed
        """
        # Remove whitespace and thousand separators
        amount_str = amount_str.strip().replace(",", "")

        # Handle parentheses for negative amounts: (150.00) → -150.00
        if amount_str.startswith("(") and amount_str.endswith(")"):
            amount_str = "-" + amount_str[1:-1]

        try:
            return Decimal(amount_str)
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f"Could not parse amount: {amount_str}") from e

    def _build_description(self, tx_data: dict) -> str:
        """Build transaction description from Payee and Memo.

        Args:
            tx_data: Transaction field dictionary

        Returns:
            Description string
        """
        payee = tx_data.get("payee", "").strip()
        memo = tx_data.get("memo", "").strip()

        # Combine Payee and Memo
        if payee and memo:
            return f"{payee} - {memo}"
        elif payee:
            return payee
        elif memo:
            return memo
        else:
            return "QIF Transaction"

    def validate_file(self) -> None:
        """Validate QIF file format.

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not valid QIF format
        """
        # Call parent validation
        super().validate_file()

        # Check QIF signature
        with open(self.file_path, "r", encoding=self.detect_encoding()) as f:
            sample = f.read(1024)

        # QIF files typically start with !Type: or !Account:
        if not (sample.startswith("!Type:") or sample.startswith("!Account:")):
            # Check if any !Type: exists in first 1KB
            if "!Type:" not in sample and "!Account:" not in sample:
                raise ValueError(
                    f"File does not appear to be valid QIF format: {self.file_path.name}"
                )

    def __repr__(self) -> str:
        """Human-readable string representation."""
        return f"<QIFImporter(file='{self.file_path.name}', date_format='{self.date_format}')>"
