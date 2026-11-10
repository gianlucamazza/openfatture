"""Untrusted XML (SDI notifications from PEC) is parsed without entity expansion."""

import pytest

from openfatture.sdi.notifiche.parser import SDINotificationParser
from openfatture.sdi.safe_xml import ParseError, parse_untrusted


def test_external_entities_are_not_resolved(tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("TOP-SECRET")
    xml = f'<?xml version="1.0"?><!DOCTYPE r [<!ENTITY x SYSTEM "file://{secret}">]><r>&x;</r>'

    root = parse_untrusted(xml)

    assert "TOP-SECRET" not in (root.text or "")


def test_entity_expansion_is_not_performed():
    xml = (
        '<?xml version="1.0"?><!DOCTYPE r [<!ENTITY a "aaaaaaaaaa">'
        '<!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">]><r>&b;</r>'
    )

    root = parse_untrusted(xml)

    assert "aaaaaaaaaa" not in (root.text or "")


def test_malformed_xml_raises_parse_error():
    with pytest.raises(ParseError):
        parse_untrusted("<r>")


def test_notification_parser_rejects_malformed_input():
    ok, error, notification = SDINotificationParser().parse_xml("<RicevutaConsegna>")

    assert not ok and error and notification is None
