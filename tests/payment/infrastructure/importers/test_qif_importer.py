"""Tests for QIF (Quicken Interchange Format) importer.

Tests cover: QIF field parsing, date format detection, split transactions, validation.
"""

from decimal import Decimal
from pathlib import Path

import pytest

from openfatture.payment.infrastructure.importers import ImporterFactory
from openfatture.payment.domain.models import BankAccount
from openfatture.payment.domain.enums import ImportSource

pytestmark = pytest.mark.unit

FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures"


class TestQIFImporter:
    """Tests for QIF (Quicken Interchange Format) importer."""

    def test_qif_import_success(self, db_session, bank_account):
        """Test successful QIF import of bank transactions."""
        factory = ImporterFactory()
        importer = factory.create_from_file(FIXTURES_DIR / "sample_statement.qif")

        result = importer.import_transactions(bank_account)

        assert result.success_count == 10
        assert result.error_count == 0
        assert result.total_count == 10

    def test_qif_date_format_us_mmddyyyy(self, db_session, bank_account):
        """Test US date format parsing (MM/DD/YYYY)."""
        factory = ImporterFactory()
        importer = factory.create_from_file(FIXTURES_DIR / "sample_statement.qif")

        importer.import_transactions(bank_account)

        # Verify first transaction date (01/15/2025 → 2025-01-15)
        first_tx = sorted(bank_account.transactions, key=lambda t: t.date)[0]
        assert first_tx.date.year == 2025
        assert first_tx.date.month == 1
        assert first_tx.date.day == 15

    def test_qif_amount_positive_negative(self, db_session, bank_account):
        """Test QIF amount parsing with positive and negative values."""
        factory = ImporterFactory()
        importer = factory.create_from_file(FIXTURES_DIR / "sample_statement.qif")

        importer.import_transactions(bank_account)

        # Check for both credits and debits
        credits = [tx for tx in bank_account.transactions if tx.amount > 0]
        debits = [tx for tx in bank_account.transactions if tx.amount < 0]

        assert len(credits) > 0
        assert len(debits) > 0

        # Verify specific amounts
        max_credit = max(tx.amount for tx in credits)
        assert max_credit == Decimal("3000.00")

        max_debit = min(tx.amount for tx in debits)
        assert max_debit == Decimal("-300.00")

    def test_qif_payee_and_memo_extraction(self, db_session, bank_account):
        """Test extraction of Payee (P) and Memo (M) fields."""
        factory = ImporterFactory()
        importer = factory.create_from_file(FIXTURES_DIR / "sample_statement.qif")

        importer.import_transactions(bank_account)

        # Check descriptions contain Payee and Memo
        descriptions = [tx.description for tx in bank_account.transactions]
        assert any("ACME CORPORATION" in d for d in descriptions)
        assert any("Fattura 2025/001" in d for d in descriptions)
        assert any("Pagamento servizi" in d for d in descriptions)

    def test_qif_counterparty_from_payee_field(self, db_session, bank_account):
        """Test counterparty is extracted from Payee field."""
        factory = ImporterFactory()
        importer = factory.create_from_file(FIXTURES_DIR / "sample_statement.qif")

        importer.import_transactions(bank_account)

        # Check counterparties
        counterparties = [tx.counterparty for tx in bank_account.transactions if tx.counterparty]
        assert len(counterparties) > 0
        assert any("ACME CORPORATION" in cp for cp in counterparties)
        assert any("TEST SRL" in cp for cp in counterparties)
        assert any("Utilities Provider" in cp for cp in counterparties)

    def test_qif_transaction_end_marker(self, db_session, bank_account, tmp_path):
        """Test QIF transactions are properly delimited by ^ marker."""
        qif_file = tmp_path / "test_markers.qif"
        qif_file.write_text(
            """!Type:Bank
D01/15/2025
T100.00
PTest Payee 1
^
D01/16/2025
T200.00
PTest Payee 2
^
"""
        )

        factory = ImporterFactory()
        importer = factory.create_from_file(qif_file)

        result = importer.import_transactions(bank_account)

        assert result.success_count == 2
        assert len(bank_account.transactions) == 2

    def test_qif_import_source_tagged(self, db_session, bank_account):
        """Test transactions are tagged with QIF import source."""
        factory = ImporterFactory()
        importer = factory.create_from_file(FIXTURES_DIR / "sample_statement.qif")

        importer.import_transactions(bank_account)

        # All transactions should have QIF source
        assert all(tx.import_source == ImportSource.QIF for tx in bank_account.transactions)

    def test_qif_raw_data_preserved(self, db_session, bank_account):
        """Test raw QIF data is preserved for debugging."""
        factory = ImporterFactory()
        importer = factory.create_from_file(FIXTURES_DIR / "sample_statement.qif")

        importer.import_transactions(bank_account)

        # Check first transaction has raw_data
        first_tx = bank_account.transactions[0]
        assert first_tx.raw_data is not None
        assert "date_str" in first_tx.raw_data
        assert "amount_str" in first_tx.raw_data
        assert "payee" in first_tx.raw_data

    def test_qif_date_format_variations(self, db_session, bank_account, tmp_path):
        """Test various QIF date format parsing."""
        qif_file = tmp_path / "date_formats.qif"
        qif_file.write_text(
            """!Type:Bank
D01/15/2025
T100.00
PSlash separator
^
D01-16-2025
T200.00
PDash separator
^
D2025-01-17
T300.00
PISO format
^
"""
        )

        factory = ImporterFactory()
        importer = factory.create_from_file(qif_file)

        result = importer.import_transactions(bank_account)

        # All date formats should be parsed correctly
        assert result.success_count == 3
        dates = sorted(tx.date for tx in bank_account.transactions)
        assert dates[0].day == 15
        assert dates[1].day == 16
        assert dates[2].day == 17

    def test_qif_amount_with_thousand_separator(self, db_session, bank_account, tmp_path):
        """Test QIF amount parsing with thousand separators."""
        qif_file = tmp_path / "thousand_sep.qif"
        qif_file.write_text(
            """!Type:Bank
D01/15/2025
T1,234.56
PThousand separator
^
D01/16/2025
T10,000.00
PLarge amount
^
"""
        )

        factory = ImporterFactory()
        importer = factory.create_from_file(qif_file)

        result = importer.import_transactions(bank_account)

        assert result.success_count == 2
        amounts = [tx.amount for tx in bank_account.transactions]
        assert Decimal("1234.56") in amounts
        assert Decimal("10000.00") in amounts

    def test_qif_negative_amount_parentheses(self, db_session, bank_account, tmp_path):
        """Test QIF negative amounts in parentheses format: (150.00)."""
        qif_file = tmp_path / "parentheses.qif"
        qif_file.write_text(
            """!Type:Bank
D01/15/2025
T(150.00)
PParentheses negative
^
D01/16/2025
T-200.00
PMinus sign negative
^
"""
        )

        factory = ImporterFactory()
        importer = factory.create_from_file(qif_file)

        result = importer.import_transactions(bank_account)

        assert result.success_count == 2
        amounts = sorted(tx.amount for tx in bank_account.transactions)
        assert amounts[0] == Decimal("-200.00")
        assert amounts[1] == Decimal("-150.00")

    def test_qif_split_transaction_handling(self, db_session, bank_account, tmp_path):
        """Test QIF split transactions are combined correctly."""
        qif_file = tmp_path / "split.qif"
        qif_file.write_text(
            """!Type:Bank
D01/15/2025
T300.00
PSplit Transaction
SCategory 1
$100.00
SCategory 2
$200.00
^
"""
        )

        factory = ImporterFactory()
        importer = factory.create_from_file(qif_file)

        result = importer.import_transactions(bank_account)

        # Split should be combined into single transaction with total amount
        assert result.success_count == 1
        tx = bank_account.transactions[0]
        assert tx.amount == Decimal("300.00")  # Sum of splits

    def test_qif_missing_required_fields_skipped(self, db_session, bank_account, tmp_path):
        """Test QIF transactions missing required fields are skipped."""
        qif_file = tmp_path / "missing_fields.qif"
        qif_file.write_text(
            """!Type:Bank
D01/15/2025
T100.00
PValid transaction
^
D01/16/2025
PMissing amount field
^
T200.00
PMissing date field
^
"""
        )

        factory = ImporterFactory()
        importer = factory.create_from_file(qif_file)

        result = importer.import_transactions(bank_account)

        # Only valid transaction should be imported
        assert result.success_count == 1
        assert len(bank_account.transactions) == 1

    def test_qif_type_bank_header_required(self, db_session, bank_account, tmp_path):
        """Test QIF requires !Type:Bank header."""
        qif_file = tmp_path / "no_header.qif"
        qif_file.write_text(
            """D01/15/2025
T100.00
PNo header
^
"""
        )

        factory = ImporterFactory()
        importer = factory.create_from_file(qif_file)

        # Should still parse (warning issued but continues)
        result = importer.import_transactions(bank_account)
        assert result.success_count == 1

    def test_qif_empty_file_returns_zero(self, db_session, bank_account, tmp_path):
        """Test empty QIF file returns zero transactions."""
        qif_file = tmp_path / "empty.qif"
        qif_file.write_text("!Type:Bank\n")

        factory = ImporterFactory()
        importer = factory.create_from_file(qif_file)

        result = importer.import_transactions(bank_account)

        assert result.success_count == 0
        assert result.total_count == 0

    def test_qif_description_memo_only(self, db_session, bank_account, tmp_path):
        """Test QIF transaction with Memo but no Payee."""
        qif_file = tmp_path / "memo_only.qif"
        qif_file.write_text(
            """!Type:Bank
D01/15/2025
T100.00
MOnly memo field, no payee
^
"""
        )

        factory = ImporterFactory()
        importer = factory.create_from_file(qif_file)

        result = importer.import_transactions(bank_account)

        assert result.success_count == 1
        tx = bank_account.transactions[0]
        assert "Only memo field" in tx.description
        assert tx.counterparty is None  # No Payee field

    def test_qif_reference_field_check_number(self, db_session, bank_account, tmp_path):
        """Test QIF reference field (N) for check numbers."""
        qif_file = tmp_path / "check_number.qif"
        qif_file.write_text(
            """!Type:Bank
D01/15/2025
T-150.00
PCheck Payment
N1234
^
"""
        )

        factory = ImporterFactory()
        importer = factory.create_from_file(qif_file)

        result = importer.import_transactions(bank_account)

        assert result.success_count == 1
        tx = bank_account.transactions[0]
        assert tx.reference == "1234"
