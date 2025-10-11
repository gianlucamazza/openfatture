"""Unit coverage for ImporterFactory utilities and format detection."""

from __future__ import annotations

from pathlib import Path

import pytest

from openfatture.payment.infrastructure.importers.base import BaseImporter, FileFormat
from openfatture.payment.infrastructure.importers.factory import ImporterFactory


class MinimalImporter(BaseImporter):
    """Very small importer used to validate the registry mechanism."""

    def __init__(self, file_path: Path):
        super().__init__(file_path)

    def parse(self, account):
        return []


def _write(tmp_path, name: str, content: str) -> Path:
    file_path = tmp_path / name
    file_path.write_text(content, encoding="utf-8")
    return file_path


def test_register_custom_importer(tmp_path):
    original = ImporterFactory._registry.get(FileFormat.UNKNOWN)
    try:
        ImporterFactory.register(FileFormat.UNKNOWN, MinimalImporter)
        assert ImporterFactory._registry[FileFormat.UNKNOWN] is MinimalImporter
    finally:
        if original is None:
            ImporterFactory._registry.pop(FileFormat.UNKNOWN, None)
        else:
            ImporterFactory._registry[FileFormat.UNKNOWN] = original


def test_detect_format_by_extension_and_content(tmp_path):
    csv_file = _write(tmp_path, "statement.csv", "date,amount\n")
    assert ImporterFactory.detect_format(csv_file) == FileFormat.CSV

    ofx_file = _write(
        tmp_path,
        "statement.ofx",
        "OFXHEADER:100\n<OFX><BANKMSGSRSV1></BANKMSGSRSV1></OFX>",
    )
    assert ImporterFactory.detect_format(ofx_file) == FileFormat.OFX

    qif_file = _write(tmp_path, "statement.qif", "!Type:Bank\n")
    assert ImporterFactory.detect_format(qif_file) == FileFormat.QIF


def test_detect_format_unknown(tmp_path):
    binary_file = tmp_path / "binary.dat"
    binary_file.write_bytes(b"\x00\x01")
    assert ImporterFactory.detect_format(binary_file) == FileFormat.UNKNOWN


def test_create_with_unknown_preset(tmp_path):
    csv_file = _write(tmp_path, "statement.csv", "date,amount\n")
    with pytest.raises(ValueError, match="Unknown bank preset"):
        ImporterFactory.create(FileFormat.CSV, csv_file, bank_preset="nonexistent")


def test_create_from_file_raises_for_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        ImporterFactory.create_from_file(tmp_path / "missing.csv")


def test_create_unsupported_format(tmp_path):
    csv_file = _write(tmp_path, "statement.csv", "date,amount\n")
    with pytest.raises(ValueError, match="Unsupported format"):
        ImporterFactory.create(FileFormat.UNKNOWN, csv_file)
