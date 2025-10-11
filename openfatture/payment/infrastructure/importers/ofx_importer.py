"""OFX/QFX importer using ofxparse library.

Supports Open Financial Exchange (OFX) format used by most banks.
"""

from datetime import datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

from ofxparse import OfxParser

from ...domain.enums import ImportSource
from ...domain.models import BankTransaction
from .base import BaseImporter

if TYPE_CHECKING:
    from ...domain.models import BankAccount


class OFXImporter(BaseImporter):
    """OFX/QFX importer using ofxparse library.

    Supports:
    - OFX 1.x (SGML format)
    - OFX 2.x (XML format)
    - Multiple accounts per file
    - Transaction types (DEBIT/CREDIT/DEP/XFER/CHECK/ATM)
    - Investment transactions (basic support)

    OFX Field Mapping:
    - FITID → reference (unique transaction ID)
    - DTPOSTED → date (posting date)
    - TRNAMT → amount (negative for debits)
    - MEMO → description
    - NAME → counterparty
    - BANKID + ACCTID → account matching

    Example:
        >>> importer = OFXImporter(Path("statement.ofx"))
        >>> transactions = importer.parse(account)
        >>> print(f"Imported {len(transactions)} transactions")
    """

    def __init__(self, file_path: Path, account_id: str | None = None) -> None:
        """Initialize OFX importer.

        Args:
            file_path: Path to OFX/QFX file
            account_id: Optional account ID to filter (ACCTID in OFX)
        """
        super().__init__(file_path)
        self.account_id = account_id

    def parse(self, account: "BankAccount") -> list[BankTransaction]:
        """Parse OFX file and extract transactions.

        Algorithm:
        1. Parse OFX using ofxparse library
        2. Find matching account statement (by ACCTID or use first)
        3. Extract transactions from statement
        4. Map OFX fields to BankTransaction
        5. Handle transaction types (DEBIT/CREDIT/etc.)
        6. Deduplicate by FITID (unique transaction ID)

        Args:
            account: BankAccount to associate transactions with

        Returns:
            List of parsed BankTransaction entities

        Raises:
            ValueError: If OFX parsing fails or account not found
        """
        # Parse OFX file
        with open(self.file_path, "rb") as f:
            raw_content = f.read()

        upper_sample = raw_content.upper()
        if b"<OFX" not in upper_sample and b"OFXHEADER" not in upper_sample:
            raise ValueError("Failed to parse OFX file: missing OFX header")

        try:
            ofx = OfxParser.parse(BytesIO(raw_content))
        except Exception as e:
            raise ValueError(f"Failed to parse OFX file: {e}") from e

        # Find account statement
        statement = self._find_statement(ofx)
        if statement is None:
            raise ValueError(
                f"No matching account found in OFX file. " f"Expected account_id: {self.account_id}"
            )

        # Extract transactions
        transactions = []
        seen_fitids = set()  # For deduplication

        for ofx_tx in statement.transactions:
            try:
                # Skip duplicates (FITID is unique transaction identifier)
                fitid = ofx_tx.id
                if fitid and fitid in seen_fitids:
                    continue
                if fitid:
                    seen_fitids.add(fitid)

                # Parse transaction
                transaction = self._parse_transaction(account, ofx_tx)
                transactions.append(transaction)

            except Exception as e:
                # Log error but continue processing
                print(f"Warning: Skipping OFX transaction {getattr(ofx_tx, 'id', 'unknown')}: {e}")
                continue

        return transactions

    def _find_statement(self, ofx):
        """Find matching account statement in OFX data.

        Args:
            ofx: Parsed OFX object from ofxparse

        Returns:
            Account statement or None if not found
        """
        # Check if OFX has account attribute (single account)
        if hasattr(ofx, "account") and ofx.account:
            account = ofx.account
            # If account_id specified, verify match
            if self.account_id:
                acct_id = getattr(account, "account_id", None)
                if acct_id != self.account_id:
                    return None
            return account.statement if hasattr(account, "statement") else account

        # Check if OFX has accounts list (multiple accounts)
        if hasattr(ofx, "accounts") and ofx.accounts:
            for account in ofx.accounts:
                if self.account_id:
                    acct_id = getattr(account, "account_id", None)
                    if acct_id == self.account_id:
                        return account.statement if hasattr(account, "statement") else account
                else:
                    # Use first account if no filter
                    return account.statement if hasattr(account, "statement") else account

        return None

    def _parse_transaction(self, account: "BankAccount", ofx_tx) -> BankTransaction:
        """Parse single OFX transaction into BankTransaction.

        Args:
            account: BankAccount entity
            ofx_tx: OFX transaction object from ofxparse

        Returns:
            BankTransaction entity

        Raises:
            ValueError: If required fields are missing
        """
        # Extract date (DTPOSTED)
        transaction_date = ofx_tx.date
        if isinstance(transaction_date, datetime):
            transaction_date = transaction_date.date()

        # Extract amount (TRNAMT) - negative for debits
        amount = Decimal(str(ofx_tx.amount))

        # Extract description (MEMO or NAME)
        description = self._build_description(ofx_tx)

        # Extract reference (FITID)
        reference = ofx_tx.id if ofx_tx.id else None

        # Extract counterparty (NAME or PAYEE)
        counterparty = self._extract_counterparty(ofx_tx)

        # Build raw data for debugging
        raw_data = {
            "fitid": ofx_tx.id,
            "type": ofx_tx.type,
            "date": str(transaction_date),
            "amount": str(amount),
            "memo": getattr(ofx_tx, "memo", ""),
            "payee": getattr(ofx_tx, "payee", ""),
            "checknum": getattr(ofx_tx, "checknum", ""),
        }

        return BankTransaction(
            account=account,
            date=transaction_date,
            amount=amount,
            description=description,
            reference=reference,
            counterparty=counterparty,
            counterparty_iban=None,  # OFX doesn't include IBAN
            import_source=ImportSource.OFX,
            raw_data=raw_data,
        )

    def _build_description(self, ofx_tx) -> str:
        """Build transaction description from OFX fields.

        Priority: MEMO > NAME > TYPE

        Args:
            ofx_tx: OFX transaction object

        Returns:
            Description string
        """
        # Try MEMO first (most descriptive)
        if hasattr(ofx_tx, "memo") and ofx_tx.memo:
            return ofx_tx.memo.strip()

        # Try NAME/PAYEE
        if hasattr(ofx_tx, "payee") and ofx_tx.payee:
            return ofx_tx.payee.strip()

        # Fallback: transaction type
        tx_type = ofx_tx.type if hasattr(ofx_tx, "type") else "Unknown"
        return f"{tx_type} Transaction"

    def _extract_counterparty(self, ofx_tx) -> str | None:
        """Extract counterparty name from OFX transaction.

        Args:
            ofx_tx: OFX transaction object

        Returns:
            Counterparty name or None
        """
        # Try PAYEE field
        if hasattr(ofx_tx, "payee") and ofx_tx.payee:
            return ofx_tx.payee.strip()

        # Try NAME field (alternative)
        if hasattr(ofx_tx, "name") and ofx_tx.name:
            return ofx_tx.name.strip()

        return None

    def validate_file(self) -> None:
        """Validate OFX file format.

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not valid OFX format
        """
        # Call parent validation
        super().validate_file()

        # Check OFX signature
        with open(self.file_path, "rb") as f:
            sample = f.read(1024).decode("utf-8", errors="ignore")

        # OFX files must contain one of these signatures
        ofx_signatures = ["<OFX>", "OFXHEADER:", "<?xml"]
        if not any(sig in sample for sig in ofx_signatures):
            raise ValueError("Failed to parse OFX file: missing OFX header")

    def __repr__(self) -> str:
        """Human-readable string representation."""
        account_filter = f", account_id='{self.account_id}'" if self.account_id else ""
        return f"<OFXImporter(file='{self.file_path.name}'{account_filter})>"
