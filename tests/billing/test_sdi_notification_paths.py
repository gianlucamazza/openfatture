"""Association guards and persistence outcomes of SDI receipt processing."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from unittest.mock import patch

import pytest
from sqlalchemy.exc import IntegrityError

from openfatture.events import SDINotificationReceivedEvent
from openfatture.sdi.notifiche.parser import NotificaSDI
from openfatture.sdi.notifiche.processor import NotificationProcessor
from openfatture.storage.database.models import (
    Fattura,
    LogSDI,
    SDIInvoiceIdentity,
    SDINotificationRecord,
)
from openfatture.storage.database.models import StatoFattura as S

BUS = "openfatture.sdi.notifiche.processor.get_global_event_bus"


def receipt(kind: str = "RC", identifier: str = "99123", **values: Any) -> NotificaSDI:
    return NotificaSDI(
        tipo=kind,
        identificativo_sdi=identifier,
        nome_file="exact.xml",
        data_ricezione=datetime(2026, 11, 1),
        **values,
    )


class Bus:
    def __init__(self) -> None:
        self.events: list[Any] = []

    def publish(self, event: Any) -> None:
        self.events.append(event)


@pytest.fixture
def historical(db_session, sample_fattura):
    sample_fattura.issued_elsewhere = True
    sample_fattura.xml_path = "/archive/exact.xml"
    db_session.commit()
    return sample_fattura


@pytest.fixture
def other_invoice(db_session, sample_cliente):
    invoice = Fattura(numero="77", anno=2025, cliente_id=sample_cliente.id, stato=S.INVIATA)
    db_session.add(invoice)
    db_session.commit()
    return invoice


def _record(db_session) -> SDINotificationRecord:
    return db_session.query(SDINotificationRecord).one()


def test_applied_receipt_records_identity_delivery_and_event(db_session, historical) -> None:
    bus = Bus()
    with patch(BUS, return_value=bus):
        result = NotificationProcessor(db_session).process_notification(
            receipt(data_evento=datetime(2026, 10, 30), messaggio="ok"), raw_xml="<RC/>"
        )

    assert result[:2] == (True, None)
    assert historical.stato == S.CONSEGNATA
    assert historical.numero_sdi == "99123"
    assert historical.data_consegna_sdi == datetime(2026, 10, 30)
    record = _record(db_session)
    assert (record.outcome, record.invoice_id, record.raw_xml) == (
        "applied",
        historical.id,
        "<RC/>",
    )
    assert record.raw_sha256
    identity = db_session.query(SDIInvoiceIdentity).one()
    assert (identity.identifier, identity.invoice_id) == ("99123", historical.id)
    log = db_session.query(LogSDI).one()
    assert (log.fattura_id, log.descrizione) == (historical.id, "ok")
    (event,) = bus.events
    assert isinstance(event, SDINotificationReceivedEvent)
    assert event.invoice_id == historical.id
    assert event.invoice_number == "1/2025"
    assert event.notification_id == 99123
    assert event.message == "ok"


def test_receipt_without_event_date_keeps_delivery_date(db_session, historical) -> None:
    with patch(BUS, return_value=None):
        assert NotificationProcessor(db_session).process_notification(receipt())[0]
    assert historical.data_consegna_sdi is None
    assert _record(db_session).raw_sha256 is None


def test_non_numeric_identifier_publishes_without_notification_id(db_session, historical) -> None:
    bus = Bus()
    historical.numero_sdi = "SDI-A"
    db_session.commit()
    with patch(BUS, return_value=bus):
        assert NotificationProcessor(db_session).process_notification(receipt(identifier="SDI-A"))[
            0
        ]
    assert bus.events[0].notification_id is None


def test_existing_identity_for_same_invoice_is_reused(db_session, historical) -> None:
    db_session.add(SDIInvoiceIdentity(identifier="99123", invoice_id=historical.id))
    db_session.commit()
    assert NotificationProcessor(db_session).process_notification(receipt())[0]
    assert db_session.query(SDIInvoiceIdentity).count() == 1


def test_identity_owned_by_another_invoice_rolls_back(
    db_session, historical, other_invoice
) -> None:
    db_session.add(SDIInvoiceIdentity(identifier="99123", invoice_id=other_invoice.id))
    db_session.commit()
    ok, error, _ = NotificationProcessor(db_session).process_notification(receipt())
    assert not ok
    assert (
        error == "Failed to process notification: SDI identifier already belongs to another invoice"
    )
    assert historical.stato == S.BOZZA
    assert db_session.query(SDINotificationRecord).count() == 0


def test_manual_association_requires_a_note(db_session, sample_fattura) -> None:
    processor = NotificationProcessor(db_session)
    assert not processor.process_notification(receipt())[0]
    ok, error, _ = processor.process_notification(
        receipt(), associated_invoice_id=sample_fattura.id, association_note="  "
    )
    assert not ok
    assert error == (
        "Failed to process notification: Manual association requires evidence/reference notes"
    )
    assert _record(db_session).outcome == "unassociated"


def test_manual_association_cannot_contradict_the_match(
    db_session, historical, other_invoice
) -> None:
    ok, error, _ = NotificationProcessor(db_session).process_notification(
        receipt(), associated_invoice_id=other_invoice.id, association_note="operator"
    )
    assert not ok
    assert (
        error
        == "Failed to process notification: Explicit association contradicts recorded identity"
    )


def test_manual_association_rejects_conflicting_sdi_number(db_session, sample_fattura) -> None:
    sample_fattura.numero_sdi = "11111"
    db_session.commit()
    ok, error, _ = NotificationProcessor(db_session).process_notification(
        receipt(), associated_invoice_id=sample_fattura.id, association_note="operator"
    )
    assert not ok
    assert error == "Failed to process notification: SDI identifier conflicts with recorded invoice"


def test_manual_association_of_conflicting_record_is_retried(
    db_session, historical, sample_cliente
) -> None:
    second = Fattura(
        numero="11", anno=2025, cliente_id=sample_cliente.id, numero_sdi="99123", stato=S.INVIATA
    )
    db_session.add(second)
    db_session.commit()
    processor = NotificationProcessor(db_session)
    assert not processor.process_notification(receipt())[0]
    assert _record(db_session).outcome == "association_conflict"
    ok, error, _ = processor.process_notification(
        receipt(), associated_invoice_id=historical.id, association_note="operator"
    )
    assert not ok
    assert error == "SDI identifier conflicts with invoice filename"
    assert _record(db_session).reason == "SDI identifier conflicts with invoice filename"


def test_manual_association_is_recorded(db_session, sample_fattura) -> None:
    processor = NotificationProcessor(db_session)
    assert processor.process_notification(
        receipt(), associated_invoice_id=sample_fattura.id, association_note="checked"
    )[0]
    record = _record(db_session)
    assert (record.source, record.reason, record.invoice_id) == (
        "manual_association",
        "checked",
        sample_fattura.id,
    )


def test_settled_record_ignores_later_manual_association(db_session, historical) -> None:
    processor = NotificationProcessor(db_session)
    assert processor.process_notification(receipt())[0]
    assert processor.process_notification(
        receipt(), associated_invoice_id=historical.id, association_note="again"
    ) == (True, None, receipt())
    assert db_session.query(LogSDI).count() == 1


def test_rejected_transition_is_persisted(db_session, historical) -> None:
    processor = NotificationProcessor(db_session)
    assert processor.process_notification(receipt("NE", esito_committente="EC01"))[0]
    ok, error, _ = processor.process_notification(receipt("RC", messaggio="late"))
    assert (ok, error) == (False, "out_of_order")
    assert processor.process_notification(receipt("RC", messaggio="late"))[:2] == (
        False,
        "out_of_order",
    )


def test_concurrent_integrity_error_is_reported(db_session, historical) -> None:
    with patch.object(
        db_session, "commit", side_effect=IntegrityError("insert", {}, Exception("unique"))
    ):
        ok, error, _ = NotificationProcessor(db_session).process_notification(receipt())
    assert not ok
    assert error == "Duplicate or conflicting concurrent SDI receipt; reload before retrying"


def test_post_commit_email_failure_keeps_success(db_session, historical) -> None:
    sender = object()
    processor = NotificationProcessor(db_session, email_sender=sender)
    with (
        patch(BUS, return_value=None),
        patch.object(
            processor, "_send_email_notification", side_effect=RuntimeError("smtp")
        ) as send,
    ):
        assert processor.process_notification(receipt())[0]
    send.assert_called_once()
    assert historical.stato == S.CONSEGNATA
