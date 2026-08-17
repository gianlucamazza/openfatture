"""Tests for the bank-statement import tool.

These run against a real, isolated database (``runtime_db``) rather than a
mocked session: the tool opens its own session via ``get_session()``, and the
deduplication path it implements is only meaningful against real persisted
rows.

Regression coverage: this tool previously imported two modules that do not
exist in the codebase, so every call raised ImportError before reaching any
of the logic below.
"""

import shutil
from pathlib import Path

import pytest

from openfatture.ai.tools.payment_tools import import_bank_transactions
from openfatture.payment.domain.enums import ImportSource
from openfatture.payment.domain.models import BankAccount, BankTransaction

FIXTURE = Path(__file__).parent.parent / "payment" / "fixtures" / "sample_statement.ofx"


@pytest.fixture
def statement(tmp_path: Path) -> Path:
    """A copy of the sample OFX statement, in a writable temp location."""
    target = tmp_path / "statement.ofx"
    shutil.copy(FIXTURE, target)
    return target


class TestImportBankTransactions:
    """Behaviour of the import_bank_transactions tool."""

    def test_imports_transactions_and_creates_account(self, runtime_db, statement: Path):
        result = import_bank_transactions(str(statement), account_name="Test Account")

        assert "error" not in result, result
        assert result["success"] is True
        assert result["account_name"] == "Test Account"
        assert result["imported"] > 0
        assert result["skipped"] == 0
        assert result["total_transactions"] == result["imported"]

        session = runtime_db()
        try:
            account = session.query(BankAccount).filter_by(name="Test Account").one()
            assert account.currency == "EUR"

            stored = session.query(BankTransaction).filter_by(account_id=account.id).all()
            assert len(stored) == result["imported"]
            assert all(tx.import_source is ImportSource.OFX for tx in stored)
            # The OFX FITID is what the dedup below keys on.
            assert all(tx.reference for tx in stored)
        finally:
            session.close()

    def test_reimporting_the_same_file_skips_every_transaction(self, runtime_db, statement: Path):
        first = import_bank_transactions(str(statement), account_name="Test Account")
        second = import_bank_transactions(str(statement), account_name="Test Account")

        assert second["imported"] == 0
        assert second["skipped"] == first["imported"]

        session = runtime_db()
        try:
            # No duplicate rows were written on the second pass.
            assert session.query(BankTransaction).count() == first["imported"]
        finally:
            session.close()

    def test_separate_accounts_do_not_share_deduplication(self, runtime_db, statement: Path):
        first = import_bank_transactions(str(statement), account_name="Account A")
        second = import_bank_transactions(str(statement), account_name="Account B")

        # Same statement, different account: the references are not "already known".
        assert second["imported"] == first["imported"]
        assert second["skipped"] == 0

        session = runtime_db()
        try:
            assert session.query(BankAccount).count() == 2
            assert session.query(BankTransaction).count() == first["imported"] * 2
        finally:
            session.close()

    def test_missing_file_is_reported(self, runtime_db, tmp_path: Path):
        result = import_bank_transactions(str(tmp_path / "absent.ofx"))

        assert "File not found" in result["error"]

    def test_wrong_extension_is_rejected(self, runtime_db, tmp_path: Path):
        wrong = tmp_path / "statement.csv"
        wrong.write_text("not an ofx file")

        result = import_bank_transactions(str(wrong))

        assert "Invalid file type" in result["error"]

    def test_unparseable_file_is_reported_not_raised(self, runtime_db, tmp_path: Path):
        broken = tmp_path / "statement.ofx"
        broken.write_text("this is not OFX content")

        result = import_bank_transactions(str(broken))

        assert "error" in result
