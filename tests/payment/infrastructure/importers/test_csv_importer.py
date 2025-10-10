"""Tests for CSV importers with bank-specific presets.

Tests cover: Intesa Sanpaolo, UniCredit, Revolut formats plus generic CSV.
"""

from decimal import Decimal
from pathlib import Path

import pytest

from openfatture.payment.infrastructure.importers import ImporterFactory

pytestmark = pytest.mark.unit

FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures"


class TestCSVImporterIntesa:
    """Tests for Intesa Sanpaolo CSV format."""

    def test_intesa_import_success_10_transactions(self, db_session, bank_account):
        """Test successful import of 10 Intesa transactions."""
        factory = ImporterFactory()
        csv_file = FIXTURES_DIR / "intesa_sanpaolo_sample.csv"
        importer = factory.create_from_file(csv_file, bank_preset="intesa")

        result = importer.import_transactions(bank_account)

        # Persist transactions to database
        for tx in result.transactions:
            db_session.add(tx)
        db_session.commit()

        assert result.success_count == 10
        assert result.error_count == 0
        assert result.total_count == 10

    def test_intesa_date_format_dd_mm_yyyy(self, db_session, bank_account):
        """Test Italian date format (DD/MM/YYYY) parsing."""
        factory = ImporterFactory()
        csv_file = FIXTURES_DIR / "intesa_sanpaolo_sample.csv"
        importer = factory.create_from_file(csv_file, bank_preset="intesa")

        result = importer.import_transactions(bank_account)

        # Verify first transaction date
        transactions = bank_account.transactions
        assert len(transactions) == 10
        first_tx = sorted(transactions, key=lambda t: t.date)[0]
        assert first_tx.date.day == 15
        assert first_tx.date.month == 1
        assert first_tx.date.year == 2025

    def test_intesa_amount_format_italian_decimals(self, db_session, bank_account):
        """Test comma separator for decimals (Italian format)."""
        factory = ImporterFactory()
        csv_file = FIXTURES_DIR / "intesa_sanpaolo_sample.csv"
        importer = factory.create_from_file(csv_file, bank_preset="intesa")

        result = importer.import_transactions(bank_account)

        # Verify amount parsing (comma → decimal point)
        transactions = sorted(bank_account.transactions, key=lambda t: t.amount, reverse=True)
        max_amount = transactions[0].amount
        assert max_amount == Decimal("3000.00")  # "3.000,00" → 3000.00

    def test_intesa_debit_credit_detection(self, db_session, bank_account):
        """Test negative amounts for debits."""
        factory = ImporterFactory()
        csv_file = FIXTURES_DIR / "intesa_sanpaolo_sample.csv"
        importer = factory.create_from_file(csv_file, bank_preset="intesa")

        importer.import_transactions(bank_account)

        # Check for negative amounts (debits)
        debits = [tx for tx in bank_account.transactions if tx.amount < 0]
        credits = [tx for tx in bank_account.transactions if tx.amount > 0]

        assert len(debits) > 0
        assert len(credits) > 0

    def test_intesa_description_field_mapping(self, db_session, bank_account):
        """Test that Causale maps to description."""
        factory = ImporterFactory()
        csv_file = FIXTURES_DIR / "intesa_sanpaolo_sample.csv"
        importer = factory.create_from_file(csv_file, bank_preset="intesa")

        importer.import_transactions(bank_account)

        # Verify description contains expected text
        descriptions = [tx.description for tx in bank_account.transactions]
        assert any("ACME CORPORATION" in d for d in descriptions)
        assert any("Fattura 2025/001" in d for d in descriptions)


class TestCSVImporterUniCredit:
    """Tests for UniCredit CSV format."""

    def test_unicredit_import_with_balance(self, db_session, bank_account):
        """Test UniCredit import includes balance column."""
        factory = ImporterFactory()
        csv_file = FIXTURES_DIR / "unicredit_sample.csv"
        importer = factory.create_from_file(csv_file, bank_preset="unicredit")

        result = importer.import_transactions(bank_account)

        assert result.success_count == 10
        # Balance column exists but may not be stored in transaction

    def test_unicredit_semicolon_separator(self, db_session, bank_account):
        """Test semicolon as CSV separator."""
        factory = ImporterFactory()
        csv_file = FIXTURES_DIR / "unicredit_sample.csv"
        importer = factory.create_from_file(csv_file, bank_preset="unicredit")

        result = importer.import_transactions(bank_account)

        # Should parse correctly despite ; separator
        assert result.error_count == 0

    def test_unicredit_iso_date_format(self, db_session, bank_account):
        """Test ISO date format (YYYY-MM-DD)."""
        factory = ImporterFactory()
        csv_file = FIXTURES_DIR / "unicredit_sample.csv"
        importer = factory.create_from_file(csv_file, bank_preset="unicredit")

        importer.import_transactions(bank_account)

        # Verify date parsing
        first_tx = sorted(bank_account.transactions, key=lambda t: t.date)[0]
        assert first_tx.date.year == 2025
        assert first_tx.date.month == 1
        assert first_tx.date.day == 15


class TestCSVImporterRevolut:
    """Tests for Revolut CSV format."""

    def test_revolut_international_format(self, db_session, bank_account):
        """Test English-language international format."""
        factory = ImporterFactory()
        csv_file = FIXTURES_DIR / "revolut_sample.csv"
        importer = factory.create_from_file(csv_file, bank_preset="revolut")

        result = importer.import_transactions(bank_account)

        assert result.success_count == 10

    def test_revolut_multi_currency_handling(self, db_session, bank_account):
        """Test Currency column is parsed (all EUR in sample)."""
        factory = ImporterFactory()
        csv_file = FIXTURES_DIR / "revolut_sample.csv"
        importer = factory.create_from_file(csv_file, bank_preset="revolut")

        importer.import_transactions(bank_account)

        # All transactions should be imported (EUR)
        assert len(bank_account.transactions) == 10


class TestCSVImporterGeneric:
    """Tests for generic CSV importer."""

    def test_csv_empty_file_returns_zero(self, db_session, bank_account, tmp_path):
        """Test empty CSV file returns zero transactions."""
        empty_file = tmp_path / "empty.csv"
        empty_file.write_text("Date,Amount,Description\n")  # Header only

        factory = ImporterFactory()
        importer = factory.create_from_file(empty_file)

        result = importer.import_transactions(bank_account)

        assert result.success_count == 0
        assert result.total_count == 0

    def test_csv_duplicate_detection(self, db_session, bank_account):
        """Test that importing same file twice detects duplicates."""
        factory = ImporterFactory()
        csv_file = FIXTURES_DIR / "intesa_sanpaolo_sample.csv"
        importer = factory.create_from_file(csv_file, bank_preset="intesa")

        # First import
        result1 = importer.import_transactions(bank_account)
        assert result1.success_count == 10

        # Second import (same file)
        result2 = importer.import_transactions(bank_account)
        assert result2.duplicate_count > 0
