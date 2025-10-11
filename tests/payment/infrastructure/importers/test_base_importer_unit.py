"""Unit tests targeting BaseImporter helpers and ImportResult utilities."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from openfatture.payment.domain.enums import ImportSource, TransactionStatus
from openfatture.payment.domain.models import BankTransaction
from openfatture.payment.infrastructure.importers.base import BaseImporter, ImportResult


class DummyImporter(BaseImporter):
    """Minimal importer stub allowing direct control over parsed transactions."""

    def __init__(
        self,
        file_path: Path,
        transactions: list[BankTransaction],
        raise_in_parse: bool = False,
    ) -> None:
        super().__init__(file_path)
        self._transactions = transactions
        self._raise_in_parse = raise_in_parse

    def parse(self, account) -> list[BankTransaction]:
        if self._raise_in_parse:
            raise ValueError("parse failure")
        return list(self._transactions)


def _make_transaction(account, *, amount: str, description: str, tx_date: date) -> BankTransaction:
    return BankTransaction(
        id=uuid4(),
        account=account,
        date=tx_date,
        amount=Decimal(amount),
        description=description,
        status=TransactionStatus.UNMATCHED,
        import_source=ImportSource.CSV,
    )


def test_import_result_helpers():
    """ImportResult should expose intuitive helpers and representations."""
    result = ImportResult(success_count=3, error_count=1, duplicate_count=2, errors=["oops"])
    assert result.total_count == 6
    assert result.success_rate == pytest.approx(0.5)
    payload = result.to_dict()
    assert payload["success_count"] == 3
    text = str(result)
    assert "success=3/6" in text


def test_import_result_success_rate_zero_total():
    """Success rate should degrade gracefully when nothing processed."""
    result = ImportResult()
    assert result.total_count == 0
    assert result.success_rate == 0.0


def test_import_transactions_deduplicates(
    db_session: Session, bank_account, bank_transaction, tmp_path
):
    """import_transactions should skip duplicates when enabled."""
    file_path = tmp_path / "bank.csv"
    file_path.write_text("header\n")

    duplicate = _make_transaction(
        bank_account,
        amount=str(bank_transaction.amount),
        description=bank_transaction.description,
        tx_date=bank_transaction.date,
    )
    fresh = _make_transaction(
        bank_account,
        amount="250.00",
        description="Fresh import",
        tx_date=date.today(),
    )

    importer = DummyImporter(file_path, [duplicate, fresh])
    result = importer.import_transactions(bank_account, skip_duplicates=True)

    assert result.success_count == 1
    assert result.duplicate_count == 1
    assert result.error_count == 0
    assert result.transactions == [fresh]


def test_import_transactions_skip_duplicates_false(
    db_session: Session, bank_account, bank_transaction, tmp_path
):
    """Disabling duplicate filtering should import every transaction."""
    file_path = tmp_path / "allow_duplicates.csv"
    file_path.write_text("header\n")

    duplicate = _make_transaction(
        bank_account,
        amount=str(bank_transaction.amount),
        description=bank_transaction.description,
        tx_date=bank_transaction.date,
    )
    fresh = _make_transaction(
        bank_account,
        amount="150.00",
        description="Another import",
        tx_date=date.today(),
    )

    importer = DummyImporter(file_path, [duplicate, fresh])
    result = importer.import_transactions(bank_account, skip_duplicates=False)

    assert result.success_count == 2
    assert result.duplicate_count == 0
    assert len(result.transactions) == 2


def test_import_transactions_parse_error_propagates(db_session: Session, bank_account, tmp_path):
    """Errors raised during parse should be surfaced after result bookkeeping."""
    file_path = tmp_path / "parse_error.csv"
    file_path.write_text("header\n")

    importer = DummyImporter(file_path, [], raise_in_parse=True)
    with pytest.raises(ValueError, match="parse failure"):
        importer.import_transactions(bank_account)


def test_import_transactions_without_bound_session(tmp_path, db_session, bank_account):
    """When the account is detached, importer should instantiate its own session."""
    from sqlalchemy.orm import sessionmaker

    from openfatture.payment.infrastructure.importers import base as importer_base

    engine = db_session.get_bind()
    session_factory = sessionmaker(bind=engine)

    original_session_local = importer_base.SessionLocal
    importer_base.SessionLocal = session_factory

    try:
        detached_account = type(bank_account)(
            name="Detached",
            iban="IT60X0542811101000000123457",
            bic_swift="BCITITMM",
            bank_name="Intesa Sanpaolo",
        )
        file_path = tmp_path / "standalone.csv"
        file_path.write_text("header\n")
        tx = _make_transaction(
            detached_account,
            amount="100.00",
            description="Detached transaction",
            tx_date=date.today(),
        )
        importer = DummyImporter(file_path, [tx])
        result = importer.import_transactions(detached_account)
        assert result.success_count == 1
    finally:
        importer_base.SessionLocal = original_session_local


def test_validate_file_errors(tmp_path, bank_account):
    """Base validation should guard against missing or empty files."""
    importer = DummyImporter(tmp_path / "missing.csv", [])
    with pytest.raises(FileNotFoundError):
        importer.import_transactions(bank_account)

    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("")  # zero bytes
    importer = DummyImporter(empty_file, [])
    with pytest.raises(ValueError, match="File is empty"):
        importer.import_transactions(bank_account)


def test_detect_encoding_prefers_first_working(tmp_path, bank_account):
    """detect_encoding should return the first compatible encoding."""
    file_path = tmp_path / "latin1.txt"
    file_path.write_bytes("Caffè".encode("iso-8859-1"))
    importer = DummyImporter(file_path, [])
    assert importer.detect_encoding() in {"iso-8859-1", "cp1252"}


def test_transaction_exists_helper(db_session: Session, bank_account, bank_transaction):
    """_transaction_exists should reflect presence/absence of duplicates."""
    duplicate = _make_transaction(
        bank_account,
        amount=str(bank_transaction.amount),
        description=bank_transaction.description,
        tx_date=bank_transaction.date,
    )
    unique = _make_transaction(
        bank_account,
        amount="321.00",
        description="Unique description",
        tx_date=date.today(),
    )

    assert BaseImporter._transaction_exists(db_session, bank_account, duplicate)
    assert not BaseImporter._transaction_exists(db_session, bank_account, unique)
