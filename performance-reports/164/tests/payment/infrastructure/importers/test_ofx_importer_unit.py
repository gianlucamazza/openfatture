"""Focused tests for OFXImporter covering parsing branches and validation."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from openfatture.payment.infrastructure.importers.ofx_importer import OFXImporter

OFX_SAMPLE = """OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

<OFX>
  <SIGNONMSGSRSV1>
    <SONRS>
      <STATUS>
        <CODE>0</CODE>
        <SEVERITY>INFO</SEVERITY>
      </STATUS>
      <DTSERVER>20250115000000</DTSERVER>
      <LANGUAGE>ENG</LANGUAGE>
    </SONRS>
  </SIGNONMSGSRSV1>
  <BANKMSGSRSV1>
    <STMTTRNRS>
      <TRNUID>1</TRNUID>
      <STATUS>
        <CODE>0</CODE>
        <SEVERITY>INFO</SEVERITY>
      </STATUS>
      <STMTRS>
        <CURDEF>EUR</CURDEF>
        <BANKACCTFROM>
          <BANKID>123</BANKID>
          <BRANCHID>0001</BRANCHID>
          <ACCTID>ACC123</ACCTID>
          <ACCTTYPE>CHECKING</ACCTTYPE>
        </BANKACCTFROM>
        <BANKTRANLIST>
          <STMTTRN>
            <TRNTYPE>DEBIT</TRNTYPE>
            <DTPOSTED>20250115120000</DTPOSTED>
            <TRNAMT>-100.00</TRNAMT>
            <FITID>1</FITID>
            <NAME>Vendor</NAME>
            <MEMO>Invoice Payment</MEMO>
          </STMTTRN>
          <STMTTRN>
            <TRNTYPE>CREDIT</TRNTYPE>
            <DTPOSTED>20250116120000</DTPOSTED>
            <TRNAMT>200.00</TRNAMT>
            <FITID>2</FITID>
            <NAME>Client</NAME>
          </STMTTRN>
        </BANKTRANLIST>
      </STMTRS>
    </STMTTRNRS>
  </BANKMSGSRSV1>
</OFX>
"""


def _write(tmp_path, name: str, content: str):
    file_path = tmp_path / name
    file_path.write_text(content, encoding="utf-8")
    return file_path


def test_ofx_parse_success(tmp_path, bank_account):
    file_path = _write(tmp_path, "statement.ofx", OFX_SAMPLE)
    importer = OFXImporter(file_path)
    transactions = importer.parse(bank_account)

    assert len(transactions) == 2

    first, second = transactions
    assert first.amount == Decimal("-100")
    assert first.description == "Invoice Payment"
    assert first.reference == "1"
    assert first.counterparty == "Vendor"
    assert first.date == date(2025, 1, 15)

    assert second.amount == Decimal("200")
    assert second.description == "Client"
    assert second.reference == "2"
    assert second.counterparty == "Client"


def test_ofx_account_filtering(tmp_path, bank_account):
    file_path = _write(tmp_path, "statement.ofx", OFX_SAMPLE)
    importer = OFXImporter(file_path, account_id="OTHER")

    with pytest.raises(ValueError, match="No matching account"):
        importer.parse(bank_account)


def test_ofx_invalid_header(tmp_path, bank_account):
    file_path = _write(tmp_path, "invalid.ofx", "<NOTOFX>")
    importer = OFXImporter(file_path)
    with pytest.raises(ValueError, match="missing OFX header"):
        importer.parse(bank_account)


def test_ofx_validate_file(tmp_path):
    file_path = _write(tmp_path, "header.ofx", "data")
    importer = OFXImporter(file_path)
    with pytest.raises(ValueError, match="missing OFX header"):
        importer.validate_file()
