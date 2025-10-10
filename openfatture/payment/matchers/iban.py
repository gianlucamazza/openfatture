"""IBAN matcher strategy.

Matches bank transactions to payments by finding IBAN in transaction reference field.
Particularly useful for Italian bank transfers where the payment IBAN is often included
in the bank statement reference/memo field.
"""

import re
from datetime import timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from ..domain.enums import MatchType
from ..domain.value_objects import MatchResult
from .base import IMatcherStrategy, payment_amount_for_matching

if TYPE_CHECKING:
    from ...storage.database.models import Pagamento
    from ..domain.models import BankTransaction


class IBANMatcher(IMatcherStrategy):
    """Match transactions by finding payment IBAN in transaction reference.

    This strategy looks for the payment's IBAN (from payment.iban field) in the
    transaction's reference or description field. Common in Italy where bank
    transfers include beneficiary IBAN in the reference.

    Confidence Scoring:
    - IBAN found in reference → confidence 0.90
    - IBAN found + amount exact match → confidence 0.95
    - IBAN found + date exact match → confidence 0.95

    Attributes:
        date_tolerance_days: Date window for matching (default 30 days for IBAN)
        amount_tolerance_pct: Amount difference tolerance (default 5%)

    Example:
        >>> matcher = IBANMatcher()
        >>> # Transaction has reference: "Bonifico a IT60X0542811101000000123456"
        >>> # Payment has iban: "IT60X0542811101000000123456"
        >>> results = matcher.match(transaction, payments)
        >>> assert results[0].confidence >= 0.90
    """

    # Italian IBAN format: IT + 2 check digits + 23 digits
    # We'll support flexible IBAN detection (with/without spaces)
    IBAN_PATTERN = re.compile(r"IT\d{2}[A-Z]\d{10}[0-9A-Z]{12}", re.IGNORECASE)

    def __init__(self, date_tolerance_days: int = 30, amount_tolerance_pct: float = 5.0) -> None:
        """Initialize IBAN matcher.

        Args:
            date_tolerance_days: Number of days ± from due date to consider
            amount_tolerance_pct: Percentage difference in amount to tolerate
        """
        self.date_tolerance_days = date_tolerance_days
        self.amount_tolerance_pct = amount_tolerance_pct

    def match(
        self, transaction: "BankTransaction", payments: list["Pagamento"]
    ) -> list["MatchResult"]:
        """Match transaction to payments by finding IBAN in reference.

        Algorithm:
        1. Extract all IBANs from transaction reference/description using regex
        2. Normalize IBANs (remove spaces, uppercase)
        3. For each payment:
           a. Check if payment has IBAN
           b. Normalize payment IBAN
           c. Check if payment IBAN is in extracted IBANs
           d. If found, calculate confidence based on amount/date match
        4. Sort by confidence descending

        Args:
            transaction: Bank transaction to match
            payments: List of candidate payments

        Returns:
            List of IBAN matches with confidence >= 0.90,
            sorted by confidence descending.
        """
        results: list[MatchResult] = []

        # Extract IBANs from transaction text fields
        transaction_ibans = self._extract_ibans(transaction)

        if not transaction_ibans:
            # No IBANs found in transaction, cannot match
            return results

        # Date filter
        date_min = transaction.date - timedelta(days=self.date_tolerance_days)
        date_max = transaction.date + timedelta(days=self.date_tolerance_days)

        for payment in payments:
            # Skip if payment has no IBAN
            if not payment.iban:
                continue

            # Normalize payment IBAN
            payment_iban = self._normalize_iban(payment.iban)

            # Check if payment IBAN is in transaction IBANs
            if payment_iban not in transaction_ibans:
                continue

            # Check date tolerance
            if not (date_min <= payment.data_scadenza <= date_max):
                continue

            # Calculate confidence based on amount and date match
            confidence = self._calculate_confidence(transaction, payment)

            # Calculate amount difference
            transaction_amount = abs(transaction.amount)
            payment_amount = payment_amount_for_matching(payment)
            amount_diff = abs(transaction_amount - payment_amount)

            # Build match reason
            match_reason = self._build_match_reason(transaction, payment, payment_iban)

            results.append(
                MatchResult(
                    transaction=transaction,
                    payment=payment,
                    confidence=self._validate_confidence(confidence),
                    match_reason=match_reason,
                    match_type=MatchType.IBAN,
                    matched_fields=["iban"],
                    amount_diff=amount_diff,
                )
            )

        # Sort by confidence descending
        results.sort(key=lambda r: r.confidence, reverse=True)

        return results

    def _extract_ibans(self, transaction: "BankTransaction") -> set[str]:
        """Extract and normalize all IBANs from transaction text fields.

        Args:
            transaction: Bank transaction

        Returns:
            Set of normalized IBANs (uppercase, no spaces)
        """
        ibans = set()

        # Search in reference field
        if transaction.reference:
            found = self.IBAN_PATTERN.findall(transaction.reference)
            ibans.update(self._normalize_iban(iban) for iban in found)

        # Search in description field
        if transaction.description:
            found = self.IBAN_PATTERN.findall(transaction.description)
            ibans.update(self._normalize_iban(iban) for iban in found)

        # Search in counterparty_iban field (if available)
        if transaction.counterparty_iban:
            ibans.add(self._normalize_iban(transaction.counterparty_iban))

        return ibans

    def _normalize_iban(self, iban: str) -> str:
        """Normalize IBAN for comparison.

        Normalization:
        1. Remove all whitespace
        2. Convert to uppercase
        3. Remove any non-alphanumeric characters

        Args:
            iban: Raw IBAN string

        Returns:
            Normalized IBAN (uppercase, no spaces)
        """
        if not iban:
            return ""

        # Remove whitespace
        iban = re.sub(r"\s+", "", iban)

        # Convert to uppercase
        iban = iban.upper()

        # Remove non-alphanumeric
        iban = re.sub(r"[^A-Z0-9]", "", iban)

        return iban

    def _calculate_confidence(self, transaction: "BankTransaction", payment: "Pagamento") -> float:
        """Calculate confidence score based on amount and date match quality.

        Scoring:
        - Base confidence: 0.90 (IBAN found)
        - +0.05 if amount matches exactly (within 1 cent)
        - +0.05 if date matches exactly
        - Max confidence: 0.95

        Args:
            transaction: Bank transaction
            payment: Payment record

        Returns:
            Confidence score (0.90-0.95)
        """
        confidence = 0.90  # Base confidence for IBAN match

        # Check amount match
        transaction_amount = abs(transaction.amount)
        payment_amount = payment_amount_for_matching(payment)
        amount_diff = abs(transaction_amount - payment_amount)
        amount_tolerance = payment_amount * (self.amount_tolerance_pct / 100)
        if amount_diff <= Decimal("0.01"):
            confidence = min(0.95, confidence + 0.05)  # Exact amount
        elif amount_diff <= amount_tolerance:
            confidence = min(0.95, confidence + 0.02)  # Close amount

        # Check date match
        date_diff_days = abs((payment.data_scadenza - transaction.date).days)
        if date_diff_days == 0:
            confidence = min(0.95, confidence + 0.05)  # Same date
        elif date_diff_days <= 3:
            confidence = min(0.95, confidence + 0.02)  # Close date

        return confidence

    def _build_match_reason(
        self, transaction: "BankTransaction", payment: "Pagamento", matched_iban: str
    ) -> str:
        """Build human-readable explanation of IBAN match.

        Args:
            transaction: Bank transaction
            payment: Payment record
            matched_iban: The IBAN that matched

        Returns:
            Human-readable match reason
        """
        transaction_amount = abs(transaction.amount)
        amount_diff = abs(transaction_amount - payment_amount_for_matching(payment))
        date_diff_days = abs((payment.data_scadenza - transaction.date).days)

        # Mask IBAN for privacy (show first 6 and last 4)
        masked_iban = f"{matched_iban[:6]}...{matched_iban[-4:]}"

        reason = f"IBAN match: {masked_iban} found in transaction"

        if amount_diff <= Decimal("0.01"):
            reason += ", exact amount"
        elif amount_diff > 0:
            reason += f", amount diff €{amount_diff:.2f}"

        if date_diff_days == 0:
            reason += ", same date"
        elif date_diff_days > 0:
            reason += f", {date_diff_days} days apart"

        return reason

    def __repr__(self) -> str:
        """Human-readable string representation."""
        return (
            f"<IBANMatcher("
            f"date_tolerance={self.date_tolerance_days} days, "
            f"amount_tolerance={self.amount_tolerance_pct}%)>"
        )
