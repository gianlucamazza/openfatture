"""Characterization of QIF date detection and the transaction state machine."""

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from openfatture.payment.domain.models import BankAccount
from openfatture.payment.infrastructure.importers.qif_importer import QIFImporter

pytestmark = pytest.mark.unit


@dataclass(frozen=True)
class _Err:
    message: str


DATE_CASES = [
    ("auto", "2024-01-15", date(2024, 1, 15)),
    ("auto", "2024-02-30", _Err("Could not parse date: 2024-02-30")),
    ("auto", "2024/01/15", date(2024, 1, 15)),
    ("auto", "01/15/2024", date(2024, 1, 15)),
    ("auto", "15/01/2024", date(2024, 1, 15)),
    ("auto", "15.01.2024", date(2024, 1, 15)),
    ("auto", "01 15 2024", date(2024, 1, 15)),
    ("auto", "1/2/2024", date(2024, 1, 2)),
    ("auto", "01/15/99", date(1999, 1, 15)),
    ("auto", "01/15/24", date(2024, 1, 15)),
    ("auto", "15-01-24", date(2024, 1, 15)),
    ("auto", "45/01/15", _Err("Could not parse date: 45-01-15")),
    ("auto", "05/45/01", _Err("Could not parse date: 05-45-01")),
    ("auto", "12-31-99", date(1999, 12, 31)),
    ("auto", "31-12-99", date(1999, 12, 31)),
    ("auto", "31/12/2024", date(2024, 12, 31)),
    ("auto", "13/13/2024", _Err("Could not parse date: 13-13-2024")),
    ("auto", "02/30/2024", _Err("Could not parse date: 02-30-2024")),
    ("auto", "1-2", _Err("Invalid date format: 1-2")),
    ("auto", "abc/01/2024", _Err("Could not parse date: abc-01-2024")),
    ("auto", "ab/01/2024", _Err("invalid literal for int() with base 10: 'ab'")),
    ("auto", "001/02/2024", date(2024, 2, 1)),
    ("US", "2024-01-15", date(2024, 1, 15)),
    ("US", "2024-02-30", _Err("Could not parse date: 2024-02-30")),
    ("US", "2024/01/15", date(2024, 1, 15)),
    ("US", "01/15/2024", date(2024, 1, 15)),
    ("US", "15/01/2024", date(2024, 1, 15)),
    ("US", "15.01.2024", date(2024, 1, 15)),
    ("US", "01 15 2024", date(2024, 1, 15)),
    ("US", "1/2/2024", date(2024, 1, 2)),
    ("US", "01/15/99", date(1999, 1, 15)),
    ("US", "01/15/24", date(2024, 1, 15)),
    ("US", "15-01-24", date(2024, 1, 15)),
    ("US", "45/01/15", _Err("Could not parse date: 45-01-15")),
    ("US", "05/45/01", _Err("Could not parse date: 05-45-01")),
    ("US", "12-31-99", date(1999, 12, 31)),
    ("US", "31-12-99", date(1999, 12, 31)),
    ("US", "31/12/2024", date(2024, 12, 31)),
    ("US", "13/13/2024", _Err("Could not parse date: 13-13-2024")),
    ("US", "02/30/2024", _Err("Could not parse date: 02-30-2024")),
    ("US", "1-2", _Err("Invalid date format: 1-2")),
    ("US", "abc/01/2024", _Err("Could not parse date: abc-01-2024")),
    ("US", "ab/01/2024", _Err("invalid literal for int() with base 10: 'ab'")),
    ("US", "001/02/2024", date(2024, 1, 2)),
    ("EU", "2024-01-15", date(2024, 1, 15)),
    ("EU", "2024-02-30", _Err("Could not parse date: 2024-02-30")),
    ("EU", "2024/01/15", date(2024, 1, 15)),
    ("EU", "01/15/2024", date(2024, 1, 15)),
    ("EU", "15/01/2024", date(2024, 1, 15)),
    ("EU", "15.01.2024", date(2024, 1, 15)),
    ("EU", "01 15 2024", date(2024, 1, 15)),
    ("EU", "1/2/2024", date(2024, 2, 1)),
    ("EU", "01/15/99", date(1999, 1, 15)),
    ("EU", "01/15/24", date(2024, 1, 15)),
    ("EU", "15-01-24", date(2024, 1, 15)),
    ("EU", "45/01/15", _Err("Could not parse date: 45-01-15")),
    ("EU", "05/45/01", _Err("Could not parse date: 05-45-01")),
    ("EU", "12-31-99", date(1999, 12, 31)),
    ("EU", "31-12-99", date(1999, 12, 31)),
    ("EU", "31/12/2024", date(2024, 12, 31)),
    ("EU", "13/13/2024", _Err("Could not parse date: 13-13-2024")),
    ("EU", "02/30/2024", _Err("Could not parse date: 02-30-2024")),
    ("EU", "1-2", _Err("Invalid date format: 1-2")),
    ("EU", "abc/01/2024", _Err("Could not parse date: abc-01-2024")),
    ("EU", "ab/01/2024", _Err("invalid literal for int() with base 10: 'ab'")),
    ("EU", "001/02/2024", date(2024, 2, 1)),
    ("other", "2024-01-15", date(2024, 1, 15)),
    ("other", "2024-02-30", _Err("Could not parse date: 2024-02-30")),
    ("other", "2024/01/15", date(2024, 1, 15)),
    ("other", "01/15/2024", date(2024, 1, 15)),
    ("other", "15/01/2024", date(2024, 1, 15)),
    ("other", "15.01.2024", date(2024, 1, 15)),
    ("other", "01 15 2024", date(2024, 1, 15)),
    ("other", "1/2/2024", date(2024, 1, 2)),
    ("other", "01/15/99", date(1999, 1, 15)),
    ("other", "01/15/24", date(2024, 1, 15)),
    ("other", "15-01-24", date(2024, 1, 15)),
    ("other", "45/01/15", _Err("Could not parse date: 45-01-15")),
    ("other", "05/45/01", _Err("Could not parse date: 05-45-01")),
    ("other", "12-31-99", date(1999, 12, 31)),
    ("other", "31-12-99", date(1999, 12, 31)),
    ("other", "31/12/2024", date(2024, 12, 31)),
    ("other", "13/13/2024", _Err("Could not parse date: 13-13-2024")),
    ("other", "02/30/2024", _Err("Could not parse date: 02-30-2024")),
    ("other", "1-2", _Err("Invalid date format: 1-2")),
    ("other", "abc/01/2024", _Err("Could not parse date: abc-01-2024")),
    ("other", "ab/01/2024", _Err("invalid literal for int() with base 10: 'ab'")),
    ("other", "001/02/2024", _Err("Could not parse date: 001-02-2024")),
    ("auto", "1/2/3", date(3, 1, 2)),
    ("auto", "10/20/345", date(345, 10, 20)),
    ("EU", "1/2/3", date(3, 2, 1)),
    ("EU", "10/20/345", _Err("Could not parse date: 10-20-345")),
]


@pytest.mark.parametrize(("date_format", "raw", "expected"), DATE_CASES)
def test_parse_date(date_format: str, raw: str, expected: date | _Err):
    importer = QIFImporter(Path("statement.qif"), date_format=date_format)
    if isinstance(expected, _Err):
        with pytest.raises(ValueError, match=re.escape(expected.message)):
            importer._parse_date(raw)
    else:
        assert importer._parse_date(raw) == expected


def _parse(tmp_path: Path, content: str) -> list:
    path = tmp_path / "statement.qif"
    path.write_text(content)
    return QIFImporter(path).parse(BankAccount(name="Conto"))


def test_state_machine_accumulates_every_field(tmp_path: Path):
    transactions = _parse(
        tmp_path,
        "!Type:Invst\n"
        "\n"
        "^\n"
        "D01/15/2024\n"
        "T300.00\n"
        "PPayee\n"
        "MMemo\n"
        "N1001\n"
        "C*\n"
        "SCategory\n"
        "ESplit memo\n"
        "$100.00\n"
        "$200.50\n"
        "X ignored\n"
        "^\n"
        "D02/01/2024\n"
        "T-5\n",
    )
    first, last = transactions
    assert first.amount == Decimal("300.50")
    assert first.description == "Payee - Memo"
    assert first.reference == "1001"
    assert first.raw_data == {
        "date_str": "01/15/2024",
        "amount_str": "300.00",
        "payee": "Payee",
        "memo": "Memo",
        "reference": "1001",
        "cleared": "*",
        "split_amounts": ["100.00", "200.50"],
    }
    assert (last.date, last.amount, last.description) == (
        date(2024, 2, 1),
        Decimal("-5"),
        "QIF Transaction",
    )


def test_invalid_transactions_are_skipped(tmp_path: Path):
    transactions = _parse(tmp_path, "!Type:Bank\nT1\n^\nD01/02/2024\nT2\n^\nD01/03/2024\n")
    assert [tx.amount for tx in transactions] == [Decimal("2")]
