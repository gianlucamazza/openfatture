"""Tests for OFX/QFX importer.

Tests cover: OFX 2.0 XML format, FITID handling, transaction types, date parsing.
"""

from decimal import Decimal
from pathlib import Path

import pytest

from openfatture.payment.domain.enums import ImportSource
from openfatture.payment.infrastructure.importers import ImporterFactory

pytestmark = pytest.mark.unit

FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures"


class TestOFXImporter:
    """Tests for OFX/QFX importer."""

    def test_ofx_import_success_with_balance(self, db_session, bank_account):
        """Test successful OFX import including balance information."""
        factory = ImporterFactory()
        importer = factory.create_from_file(FIXTURES_DIR / "sample_statement.ofx")

        result = importer.import_transactions(bank_account)

        assert result.success_count == 5
        assert result.error_count == 0
        assert result.total_count == 5

    def test_ofx_transaction_type_mapping(self, db_session, bank_account):
        """Test DEBIT/CREDIT transaction type mapping to amounts."""
        factory = ImporterFactory()
        importer = factory.create_from_file(FIXTURES_DIR / "sample_statement.ofx")

        result = importer.import_transactions(bank_account)
        for tx in result.transactions:
            db_session.add(tx)
        db_session.commit()

        # Check for both positive (CREDIT) and negative (DEBIT) amounts
        transactions = bank_account.transactions
        credits = [tx for tx in transactions if tx.amount > 0]
        debits = [tx for tx in transactions if tx.amount < 0]

        assert len(credits) == 4  # 4 CREDIT transactions
        assert len(debits) == 1  # 1 DEBIT transaction

    def test_ofx_date_parsing_yyyymmddhhmmss(self, db_session, bank_account):
        """Test OFX date format parsing (YYYYMMDDHHMMSS)."""
        factory = ImporterFactory()
        importer = factory.create_from_file(FIXTURES_DIR / "sample_statement.ofx")

        result = importer.import_transactions(bank_account)
        for tx in result.transactions:
            db_session.add(tx)
        db_session.commit()

        # Verify first transaction date (20250115000000 → 2025-01-15)
        first_tx = sorted(bank_account.transactions, key=lambda t: t.date)[0]
        assert first_tx.date.year == 2025
        assert first_tx.date.month == 1
        assert first_tx.date.day == 15

    def test_ofx_fitid_as_unique_identifier(self, db_session, bank_account):
        """Test FITID is stored as unique reference."""
        factory = ImporterFactory()
        importer = factory.create_from_file(FIXTURES_DIR / "sample_statement.ofx")

        result = importer.import_transactions(bank_account)
        for tx in result.transactions:
            db_session.add(tx)
        db_session.commit()

        # All transactions should have unique references from FITID
        transactions = bank_account.transactions
        references = [tx.reference for tx in transactions]

        assert all(ref is not None for ref in references)
        assert len(set(references)) == len(transactions)  # All unique
        assert any("TXN20250115001" in ref for ref in references)

    def test_ofx_memo_and_name_extraction(self, db_session, bank_account):
        """Test extraction of MEMO and NAME fields into description."""
        factory = ImporterFactory()
        importer = factory.create_from_file(FIXTURES_DIR / "sample_statement.ofx")

        result = importer.import_transactions(bank_account)
        for tx in result.transactions:
            db_session.add(tx)
        db_session.commit()

        # Check descriptions contain expected text
        descriptions = [tx.description for tx in bank_account.transactions]
        assert any("Fattura 2025/001" in d for d in descriptions)
        assert any("Pagamento servizi" in d for d in descriptions)

    def test_ofx_counterparty_from_name_field(self, db_session, bank_account):
        """Test counterparty extraction from NAME field."""
        factory = ImporterFactory()
        importer = factory.create_from_file(FIXTURES_DIR / "sample_statement.ofx")

        result = importer.import_transactions(bank_account)
        for tx in result.transactions:
            db_session.add(tx)
        db_session.commit()

        # Check counterparties
        counterparties = [tx.counterparty for tx in bank_account.transactions if tx.counterparty]
        assert len(counterparties) > 0
        assert any("ACME CORPORATION" in cp for cp in counterparties)
        assert any("TEST SRL" in cp for cp in counterparties)

    def test_ofx_amount_decimal_precision(self, db_session, bank_account):
        """Test amount parsing preserves decimal precision."""
        factory = ImporterFactory()
        importer = factory.create_from_file(FIXTURES_DIR / "sample_statement.ofx")

        result = importer.import_transactions(bank_account)
        for tx in result.transactions:
            db_session.add(tx)
        db_session.commit()

        # Find transaction with .50 amount
        tx_500_50 = next(
            (tx for tx in bank_account.transactions if tx.amount == Decimal("500.50")), None
        )
        assert tx_500_50 is not None
        assert tx_500_50.amount == Decimal("500.50")

    def test_ofx_import_source_tagged(self, db_session, bank_account):
        """Test transactions are tagged with OFX import source."""
        factory = ImporterFactory()
        importer = factory.create_from_file(FIXTURES_DIR / "sample_statement.ofx")

        result = importer.import_transactions(bank_account)
        for tx in result.transactions:
            db_session.add(tx)
        db_session.commit()

        # All transactions should have OFX source
        assert all(tx.import_source == ImportSource.OFX for tx in bank_account.transactions)

    def test_ofx_raw_data_preserved(self, db_session, bank_account):
        """Test raw OFX data is preserved for debugging."""
        factory = ImporterFactory()
        importer = factory.create_from_file(FIXTURES_DIR / "sample_statement.ofx")

        result = importer.import_transactions(bank_account)
        for tx in result.transactions:
            db_session.add(tx)
        db_session.commit()

        # Check first transaction has raw_data
        first_tx = bank_account.transactions[0]
        assert first_tx.raw_data is not None
        assert "fitid" in first_tx.raw_data
        assert "type" in first_tx.raw_data
        assert "amount" in first_tx.raw_data

    def test_ofx_duplicate_prevention_by_fitid(self, db_session, bank_account, tmp_path):
        """Test duplicate transactions are prevented by FITID."""
        # Create OFX file with duplicate FITID
        duplicate_ofx = tmp_path / "duplicate.ofx"
        duplicate_ofx.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<OFX>
  <SIGNONMSGSRSV1>
    <SONRS>
      <STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY></STATUS>
      <DTSERVER>20250228120000</DTSERVER>
      <LANGUAGE>ITA</LANGUAGE>
    </SONRS>
  </SIGNONMSGSRSV1>
  <BANKMSGSRSV1>
    <STMTTRNRS>
      <TRNUID>1001</TRNUID>
      <STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY></STATUS>
      <STMTRS>
        <CURDEF>EUR</CURDEF>
        <BANKACCTFROM>
          <BANKID>05428</BANKID>
          <ACCTID>000000123456</ACCTID>
          <ACCTTYPE>CHECKING</ACCTTYPE>
        </BANKACCTFROM>
        <BANKTRANLIST>
          <DTSTART>20250115000000</DTSTART>
          <DTEND>20250228235959</DTEND>
          <STMTTRN>
            <TRNTYPE>CREDIT</TRNTYPE>
            <DTPOSTED>20250115000000</DTPOSTED>
            <TRNAMT>1000.00</TRNAMT>
            <FITID>DUPLICATE_ID</FITID>
            <NAME>First Transaction</NAME>
            <MEMO>First</MEMO>
          </STMTTRN>
          <STMTTRN>
            <TRNTYPE>CREDIT</TRNTYPE>
            <DTPOSTED>20250116000000</DTPOSTED>
            <TRNAMT>2000.00</TRNAMT>
            <FITID>DUPLICATE_ID</FITID>
            <NAME>Second Transaction</NAME>
            <MEMO>Duplicate FITID</MEMO>
          </STMTTRN>
        </BANKTRANLIST>
        <LEDGERBAL>
          <BALAMT>3000.00</BALAMT>
          <DTASOF>20250228235959</DTASOF>
        </LEDGERBAL>
      </STMTRS>
    </STMTTRNRS>
  </BANKMSGSRSV1>
</OFX>
"""
        )

        factory = ImporterFactory()
        importer = factory.create_from_file(duplicate_ofx)

        result = importer.import_transactions(bank_account)
        for tx in result.transactions:
            db_session.add(tx)
        db_session.commit()

        # Only 1 transaction should be imported (duplicate skipped)
        assert result.success_count == 1
        assert len(bank_account.transactions) == 1

    def test_ofx_invalid_file_raises_error(self, db_session, bank_account, tmp_path):
        """Test invalid OFX file raises clear error."""
        invalid_file = tmp_path / "invalid.ofx"
        invalid_file.write_text("This is not OFX data")

        factory = ImporterFactory()
        importer = factory.create_from_file(invalid_file)

        with pytest.raises(ValueError, match="Failed to parse OFX file"):
            importer.import_transactions(bank_account)

    def test_ofx_account_currency_eur(self, db_session, bank_account):
        """Test OFX import handles EUR currency correctly."""
        factory = ImporterFactory()
        importer = factory.create_from_file(FIXTURES_DIR / "sample_statement.ofx")

        result = importer.import_transactions(bank_account)

        # All transactions imported (EUR is default currency)
        assert result.success_count == 5

    def test_ofx_negative_amounts_for_debits(self, db_session, bank_account):
        """Test DEBIT transactions have negative amounts."""
        factory = ImporterFactory()
        importer = factory.create_from_file(FIXTURES_DIR / "sample_statement.ofx")

        result = importer.import_transactions(bank_account)
        for tx in result.transactions:
            db_session.add(tx)
        db_session.commit()

        # Find the DEBIT transaction (-150.00)
        debit_tx = next((tx for tx in bank_account.transactions if tx.amount < 0), None)
        assert debit_tx is not None
        assert debit_tx.amount == Decimal("-150.00")
        assert "Utilities Provider" in debit_tx.counterparty
