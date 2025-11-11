"""IBAN matcher strategy with SEPA multi-country support.

Matches bank transactions to payments by finding IBAN in transaction reference field.
Supports all 27 SEPA countries with automatic country detection and validation.

Particularly useful for European bank transfers where the beneficiary IBAN is often
included in the bank statement reference/memo field.
"""

import re
from datetime import timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from ..domain.enums import MatchType
from ..domain.value_objects import MatchResult
from .base import IMatcherStrategy, as_match_results, payment_amount_for_matching
from .iban_formats import SEPAIBANFormats

if TYPE_CHECKING:
    from ...storage.database.models import Pagamento
    from ..domain.models import BankTransaction


class IBANMatcher(IMatcherStrategy):
    """Match transactions by finding payment IBAN in transaction reference.

    This strategy looks for the payment's IBAN (from payment.iban field) in the
    transaction's reference or description field. Supports all 27 SEPA countries
    with automatic country detection and format validation.

    Supported SEPA Countries (27):
        Austria, Belgium, Bulgaria, Croatia, Cyprus, Czech Republic, Denmark,
        Estonia, Finland, France, Germany, Greece, Hungary, Iceland, Ireland,
        Italy, Latvia, Liechtenstein, Lithuania, Luxembourg, Malta, Netherlands,
        Norway, Poland, Portugal, Romania, Slovakia, Slovenia, Spain, Sweden

    Confidence Scoring:
    - IBAN found in reference → confidence 0.90
    - IBAN found + amount exact match → confidence 0.95
    - IBAN found + date exact match → confidence 0.95

    Attributes:
        date_tolerance_days: Date window for matching (default 30 days for IBAN)
        amount_tolerance_pct: Amount difference tolerance (default 5%)

    Example:
        >>> matcher = IBANMatcher()
        >>> # Italian IBAN
        >>> # Transaction has reference: "Bonifico a IT60X0542811101000000123456"
        >>> # Payment has iban: "IT60X0542811101000000123456"
        >>> results = matcher.match(transaction, payments)
        >>> assert results[0].confidence >= 0.90
        >>> assert "Italy" in results[0].match_reason

        >>> # German IBAN
        >>> # Transaction: "Transfer from DE89370400440532013000"
        >>> results = matcher.match(transaction, payments)
        >>> assert "Germany" in results[0].match_reason
    """

    # SEPA IBAN pattern: Supports all 27 SEPA countries
    # Pattern auto-generated from SEPAIBANFormats registry
    IBAN_PATTERN = re.compile(SEPAIBANFormats.get_combined_pattern(), re.IGNORECASE)

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

        transaction_ibans = self._extract_ibans(transaction)
        transaction_text = self._collect_transaction_text(transaction)

        # Date filter
        date_min = transaction.date - timedelta(days=self.date_tolerance_days)
        date_max = transaction.date + timedelta(days=self.date_tolerance_days)

        for payment in payments:
            payment_iban_raw = self._get_payment_iban(payment)
            if not payment_iban_raw:
                continue

            payment_iban = self._normalize_iban(payment_iban_raw)
            if not payment_iban:
                continue

            is_full_match = payment_iban in transaction_ibans
            is_partial_match = False

            if not is_full_match and payment_iban and transaction_text:
                iban_tail = payment_iban[-4:]
                if iban_tail and iban_tail.isdigit():
                    tail_pattern = re.compile(rf"(?<!\d){iban_tail}(?!\d)")
                    if tail_pattern.search(transaction_text):
                        is_partial_match = True

            if not is_full_match and not is_partial_match:
                continue

            # Check date tolerance
            if not (date_min <= payment.data_scadenza <= date_max):
                continue

            # Calculate confidence based on amount and date match
            base_confidence = 0.90 if is_full_match else 0.75
            confidence = self._calculate_confidence(transaction, payment, base_confidence)

            # Calculate amount difference
            transaction_amount = abs(transaction.amount)
            payment_amount = payment_amount_for_matching(payment)
            amount_diff = abs(transaction_amount - payment_amount)

            # Build match reason
            match_reason = self._build_match_reason(
                transaction, payment, payment_iban, is_partial_match
            )

            matched_fields = ["iban"]
            if is_partial_match:
                matched_fields.append("iban_last4")

            results.append(
                MatchResult(
                    transaction=transaction,
                    payment=payment,
                    confidence=self._validate_confidence(confidence),
                    match_reason=match_reason,
                    match_type=MatchType.IBAN,
                    matched_fields=matched_fields,
                    amount_diff=amount_diff,
                )
            )

        # Sort by confidence descending
        results.sort(key=lambda r: r.confidence, reverse=True)

        return as_match_results(results)

    def _extract_ibans(self, transaction: "BankTransaction") -> set[str]:
        """Extract and normalize all IBANs from transaction text fields.

        Extracts IBANs from multiple transaction fields (reference, description,
        memo, counterparty_iban) and validates them against SEPA country formats.

        Args:
            transaction: Bank transaction

        Returns:
            Set of normalized and validated IBANs (uppercase, no spaces)
            Only includes IBANs that match SEPA country patterns and lengths
        """
        ibans: set[str] = set()

        reference = self._get_text(transaction, "reference")
        if reference:
            found = self.IBAN_PATTERN.findall(reference)
            ibans.update(self._normalize_iban(iban) for iban in found)

        # Search in description field
        description = self._get_text(transaction, "description")
        if description:
            found = self.IBAN_PATTERN.findall(description)
            ibans.update(self._normalize_iban(iban) for iban in found)

        memo = self._get_text(transaction, "memo") or self._get_text(transaction, "note")
        if memo:
            found = self.IBAN_PATTERN.findall(memo)
            ibans.update(self._normalize_iban(iban) for iban in found)

        # Search in counterparty_iban field (if available)
        counterparty_iban = self._get_text(transaction, "counterparty_iban")
        if counterparty_iban:
            ibans.add(self._normalize_iban(counterparty_iban))

        # Validate extracted IBANs against SEPA country formats
        validated_ibans = {iban for iban in ibans if SEPAIBANFormats.validate_length(iban)}

        return validated_ibans

    def _collect_transaction_text(self, transaction: "BankTransaction") -> str:
        """Collect normalized text blob for partial IBAN matching."""
        parts = []
        for attr in ("reference", "description", "memo", "note"):
            value = self._get_text(transaction, attr)
            if value:
                parts.append(value)

        return " ".join(parts).upper()

    def _get_payment_iban(self, payment: "Pagamento") -> str | None:
        """Extract IBAN from payment or related entities."""
        candidates = [
            getattr(payment, "iban", None),
            getattr(payment, "beneficiary_iban", None),
            getattr(payment, "counterparty_iban", None),
        ]

        fattura = getattr(payment, "fattura", None)
        if fattura is not None:
            candidates.append(getattr(fattura, "iban", None))
            cliente = getattr(fattura, "cliente", None)
            if cliente is not None:
                candidates.append(getattr(cliente, "iban", None))
                candidates.append(getattr(cliente, "conto_corrente", None))

        for candidate in candidates:
            if isinstance(candidate, str) and candidate.strip():
                return candidate

        return None

    def _get_text(self, obj: object, attr: str) -> str:
        """Safely retrieve a string attribute from an object."""
        if obj is None:
            return ""
        value = getattr(obj, attr, "")
        return value if isinstance(value, str) else ""

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

    def _calculate_confidence(
        self,
        transaction: "BankTransaction",
        payment: "Pagamento",
        base_confidence: float,
    ) -> float:
        """Calculate confidence score based on amount and date match quality.

        Scoring:
        - Base confidence: provided base (full vs partial match)
        - +0.05 if amount matches exactly (within 1 cent)
        - +0.05 if date matches exactly
        - Max confidence: 0.95

        Args:
            transaction: Bank transaction
            payment: Payment record

        Returns:
            Confidence score (float)
        """
        confidence = Decimal(str(base_confidence))

        # Check amount match
        transaction_amount = abs(transaction.amount)
        payment_amount = payment_amount_for_matching(payment)
        amount_diff = abs(transaction_amount - payment_amount)
        tolerance_pct = Decimal(str(self.amount_tolerance_pct)) / Decimal("100")
        amount_tolerance = payment_amount * tolerance_pct
        if amount_diff <= Decimal("0.01"):
            confidence = min(Decimal("1.0"), confidence + Decimal("0.05"))  # Exact amount
        elif amount_diff <= amount_tolerance:
            confidence = min(Decimal("1.0"), confidence + Decimal("0.02"))  # Close amount

        # Check date match
        date_diff_days = abs((payment.data_scadenza - transaction.date).days)
        if date_diff_days == 0:
            confidence = min(Decimal("1.0"), confidence + Decimal("0.05"))  # Same date
        elif date_diff_days <= 3:
            confidence = min(Decimal("1.0"), confidence + Decimal("0.02"))  # Close date

        # Convert to float for MatchResult compatibility
        return float(confidence)

    def _build_match_reason(
        self,
        transaction: "BankTransaction",
        payment: "Pagamento",
        matched_iban: str,
        is_partial: bool = False,
    ) -> str:
        """Build human-readable explanation of IBAN match.

        Includes country detection for enhanced context and transparency.

        Args:
            transaction: Bank transaction
            payment: Payment record
            matched_iban: The IBAN that matched
            is_partial: Whether the match used partial digits

        Returns:
            Human-readable match reason with country name
            Example: "IBAN match (Germany): DE8937...3000 found in transaction, exact amount"
        """
        transaction_amount = abs(transaction.amount)
        amount_diff = abs(transaction_amount - payment_amount_for_matching(payment))
        date_diff_days = abs((payment.data_scadenza - transaction.date).days)

        # Detect country from IBAN
        country_name = SEPAIBANFormats.get_country_name(matched_iban) or "Unknown"

        # Mask IBAN for privacy (show first 6 and last 4)
        masked_iban = f"{matched_iban[:6]}...{matched_iban[-4:]}"

        if is_partial:
            reason = (
                f"IBAN partial match ({country_name}): "
                f"last 4 digits {matched_iban[-4:]} detected in transaction"
            )
        else:
            reason = f"IBAN match ({country_name}): {masked_iban} found in transaction"

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

    def _validate_confidence(self, confidence: float | Decimal) -> float:
        """Clamp confidence to [0.0, 1.0] and return float.

        Overrides base class to accept both float and Decimal for internal
        calculations, but always returns float for MatchResult compatibility.

        Args:
            confidence: Confidence value (float or Decimal)

        Returns:
            Clamped confidence as float (0.0-1.0)
        """
        value = Decimal(str(confidence))
        if value < Decimal("0.0"):
            return 0.0
        if value > Decimal("1.0"):
            return 1.0
        return float(value)
