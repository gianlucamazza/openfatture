"""Additional unit coverage for CSVImporter helper behaviour."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from openfatture.payment.infrastructure.importers.csv_importer import CSVConfig, CSVImporter


def _make_csv(tmp_path, content: str):
    file_path = tmp_path / "sample.csv"
    file_path.write_text(content, encoding="utf-8")
    return file_path


def test_get_field_missing_required_raises(tmp_path, bank_account):
    config = CSVConfig(field_mapping={})
    importer = CSVImporter(_make_csv(tmp_path, "date,amount,description\n"), config)

    with pytest.raises(ValueError, match="Field mapping missing"):
        importer._get_field({}, "date", required=True)


def test_parse_date_fallback_to_dateutil(tmp_path, bank_account):
    config = CSVConfig(date_format="%Y-%m-%d")
    importer = CSVImporter(_make_csv(tmp_path, "dummy"), config)
    parsed = importer._parse_date("15/01/2025")
    assert parsed == date(2025, 1, 15)


def test_parse_date_invalid(tmp_path):
    importer = CSVImporter(_make_csv(tmp_path, "dummy"), CSVConfig())
    with pytest.raises(ValueError, match="Could not parse date"):
        importer._parse_date("not-a-date")


def test_parse_decimal_handles_european_format(tmp_path):
    importer = CSVImporter(
        _make_csv(tmp_path, "dummy"), CSVConfig(decimal_separator=",", thousands_separator=".")
    )
    value = importer._parse_decimal("1.234,56")
    assert value == Decimal("1234.56")


def test_parse_decimal_invalid(tmp_path):
    importer = CSVImporter(_make_csv(tmp_path, "dummy"), CSVConfig())
    with pytest.raises(ValueError, match="Could not parse number"):
        importer._parse_decimal("abc")


def test_normalize_description_includes_context(tmp_path, bank_account):
    importer = CSVImporter(_make_csv(tmp_path, "dummy"), CSVConfig())
    normalized = importer._normalize_description(
        description="Pagamento",
        reference="Ref-001",
        counterparty="ACME",
    )
    assert "Ref-001" in normalized and "ACME" in normalized


def test_detect_delimiter_fallback(tmp_path):
    content = "Data|Importo|Descrizione\n2025-01-15|100.00|Test"
    file_path = _make_csv(tmp_path, content)
    importer = CSVImporter(file_path, CSVConfig(delimiter="auto"))
    assert importer._detect_delimiter() == "|"


def test_parse_skips_duplicate_rows(tmp_path, bank_account):
    config = CSVConfig(
        delimiter=",",
        field_mapping={
            "date": "date",
            "amount": "amount",
            "description": "description",
        },
    )
    file_path = _make_csv(
        tmp_path,
        "date,amount,description\n2025-01-15,100.00,Invoice\n2025-01-15,100.00,Invoice\n",
    )
    importer = CSVImporter(file_path, config)
    transactions = importer.parse(bank_account)
    assert len(transactions) == 1  # Deduplicated via hash


def test_parse_logs_warning_on_invalid_row(tmp_path, bank_account, capsys):
    config = CSVConfig(
        delimiter=",",
        field_mapping={
            "date": "date",
            "amount": "amount",
            "description": "description",
        },
    )
    file_path = _make_csv(
        tmp_path,
        "date,amount,description\ninvalid-date,123,Payment\n2025-01-16,200.00,Valid\n",
    )
    importer = CSVImporter(file_path, config)
    transactions = importer.parse(bank_account)

    out, _ = capsys.readouterr()
    assert "Skipping row" in out
    assert len(transactions) == 1
