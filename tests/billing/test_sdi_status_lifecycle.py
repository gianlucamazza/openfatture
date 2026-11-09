"""Persistence, idempotency and concurrency of invoice lifecycle evidence."""

from datetime import datetime
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from openfatture.billing.application.invoice_status import InvoiceStateConflict, change_status
from openfatture.sdi.notifiche.parser import NotificaSDI
from openfatture.sdi.notifiche.processor import NotificationProcessor
from openfatture.sdi.pec_sender.sender import PECSender
from openfatture.storage.database.models import (
    Fattura,
    LogSDI,
    SDINotificationRecord,
    SDISubmissionAttempt,
)
from openfatture.storage.database.models import StatoFattura as S
from openfatture.storage.database.status_migration import (
    downgrade_status_schema,
    upgrade_status_schema,
)


def receipt(kind="RC", **values):
    return NotificaSDI(
        tipo=kind,
        identificativo_sdi="99123",
        nome_file="exact.xml",
        data_ricezione=datetime(2026, 11, 1),
        **values,
    )


@pytest.fixture
def historical(db_session, sample_fattura):
    sample_fattura.issued_elsewhere = True
    sample_fattura.xml_path = "/archive/exact.xml"
    db_session.commit()
    return sample_fattura


def test_receipt_is_idempotent_and_preserves_historical_block(db_session, historical):
    processor = NotificationProcessor(db_session)
    assert processor.process_notification(receipt())[0]
    assert processor.process_notification(receipt())[0]
    assert historical.stato == S.CONSEGNATA
    assert historical.numero_sdi == "99123"
    assert historical.issued_elsewhere
    assert db_session.query(LogSDI).count() == 1
    assert db_session.query(SDINotificationRecord).count() == 1


def test_old_and_conflicting_receipts_do_not_overwrite(db_session, historical):
    processor = NotificationProcessor(db_session)
    assert processor.process_notification(receipt("NE", esito_committente="EC01"))[0]
    assert not processor.process_notification(receipt("RC"))[0]
    assert not processor.process_notification(receipt("NE", esito_committente="EC02"))[0]
    assert historical.stato == S.ACCETTATA
    assert {r.outcome for r in db_session.query(SDINotificationRecord)} == {
        "applied",
        "conflict",
        "out_of_order",
    }


def test_unassociated_receipt_can_be_explicitly_associated(db_session, sample_fattura):
    processor = NotificationProcessor(db_session)
    assert not processor.process_notification(receipt())[0]
    assert db_session.query(SDINotificationRecord).one().outcome == "unassociated"
    assert processor.process_notification(
        receipt(),
        associated_invoice_id=sample_fattura.id,
        association_note="External reference checked by operator",
    )[0]
    assert sample_fattura.stato == S.CONSEGNATA


def test_substring_does_not_match(db_session, sample_fattura):
    sample_fattura.xml_path = "/archive/other-1-2025.xml"
    db_session.commit()
    assert NotificationProcessor(db_session)._find_invoice(receipt()) is None


def test_identifier_filename_conflict_is_persisted(db_session, historical, sample_cliente):
    second = Fattura(
        numero="11", anno=2025, cliente_id=sample_cliente.id, numero_sdi="99123", stato=S.INVIATA
    )
    db_session.add(second)
    db_session.commit()
    assert not NotificationProcessor(db_session).process_notification(receipt())[0]
    assert db_session.query(SDINotificationRecord).one().outcome == "association_conflict"
    assert historical.stato == S.BOZZA


def test_postcommit_event_error_does_not_reverse_success(db_session, historical):
    with patch(
        "openfatture.sdi.notifiche.processor.get_global_event_bus",
        side_effect=RuntimeError("event unavailable"),
    ):
        assert NotificationProcessor(db_session).process_notification(receipt())[0]
    assert historical.stato == S.CONSEGNATA


def test_unknown_receipt_is_preserved_without_transition(db_session, historical):
    assert not NotificationProcessor(db_session).process_notification(receipt("FUTURE"))[0]
    assert historical.stato == S.BOZZA
    assert db_session.query(SDINotificationRecord).one().outcome == "unsupported"


def test_compare_and_set_rejects_stale_reader(db_session, sample_fattura):
    other = Session(bind=db_session.get_bind())
    stale = other.get(Fattura, sample_fattura.id)
    change_status(db_session, sample_fattura, S.CONSEGNATA)
    db_session.commit()
    with pytest.raises(InvoiceStateConflict):
        change_status(other, stale, S.DA_INVIARE)
    other.rollback()
    other.close()


def test_uncertain_transport_blocks_second_attempt(
    db_session, sample_fattura, test_settings, tmp_path
):
    path = tmp_path / "invoice.xml"
    path.write_text("<xml/>")
    sender = PECSender(test_settings)
    with patch.object(sender, "_send_with_retry", return_value=(False, "timeout")) as transport:
        assert not sender.send_invoice(sample_fattura, path)[0]
        assert not sender.send_invoice(sample_fattura, path)[0]
        assert transport.call_count == 1
    assert db_session.query(SDISubmissionAttempt).one().outcome == "uncertain"
    assert sample_fattura.stato == S.BOZZA


def test_schema_upgrade_is_idempotent_and_downgrade_preserves_evidence(db_session, historical):
    upgrade_status_schema(db_session.get_bind())
    upgrade_status_schema(db_session.get_bind())
    assert NotificationProcessor(db_session).process_notification(receipt())[0]
    with pytest.raises(ValueError, match="evidence"):
        downgrade_status_schema(db_session.get_bind())


def test_commit_failure_after_transport_keeps_durable_claim(
    db_session, sample_fattura, test_settings, tmp_path
):
    path = tmp_path / "commit.xml"
    path.write_text("<xml/>")
    sender = PECSender(test_settings)
    original_commit = db_session.commit
    calls = 0

    def commit():
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("database failed after transport")
        original_commit()

    with (
        patch.object(db_session, "commit", side_effect=commit),
        patch.object(sender, "_send_with_retry", return_value=(True, None)) as transport,
    ):
        assert not sender.send_invoice(sample_fattura, path)[0]
        assert transport.call_count == 1
    assert db_session.query(SDISubmissionAttempt).one().outcome == "pending"
    with patch.object(sender, "_send_with_retry") as transport:
        assert not sender.send_invoice(sample_fattura, path)[0]
        transport.assert_not_called()


def test_claim_failure_prevents_network(db_session, sample_fattura, test_settings, tmp_path):
    path = tmp_path / "claim.xml"
    path.write_text("<xml/>")
    sender = PECSender(test_settings)
    with (
        patch.object(db_session, "commit", side_effect=RuntimeError("disk full")),
        patch.object(sender, "_send_with_retry") as transport,
    ):
        assert not sender.send_invoice(sample_fattura, path)[0]
        transport.assert_not_called()


def test_explicit_resolution_can_release_uncertain_claim(
    db_session, sample_fattura, test_settings, tmp_path
):
    from openfatture.sdi.application.submissions import resolve_submission

    path = tmp_path / "resolve.xml"
    path.write_text("<xml/>")
    sender = PECSender(test_settings)
    with patch.object(sender, "_send_with_retry", return_value=(False, "timeout")):
        sender.send_invoice(sample_fattura, path)
    attempt = db_session.query(SDISubmissionAttempt).one()
    resolve_submission(
        db_session, attempt.id, sent=False, note="Provider confirmed no message accepted"
    )
    with patch.object(sender, "_send_with_retry", return_value=(True, None)) as transport:
        assert sender.send_invoice(sample_fattura, path)[0]
        transport.assert_called_once()
    assert sample_fattura.stato == S.INVIATA


def test_date_is_only_taken_from_attested_delivery_event(db_session, historical):
    value = datetime(2026, 10, 25, 12, 0)
    assert NotificationProcessor(db_session).process_notification(receipt(data_evento=value))[0]
    assert historical.data_consegna_sdi == value
    assert historical.data_invio_sdi is None


def test_concurrent_submission_claims_allow_one_transport(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier, Lock
    from types import SimpleNamespace

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from openfatture.sdi.application.submissions import journaled_submission
    from openfatture.storage.database.base import Base
    from openfatture.storage.database.models import Cliente

    engine = create_engine(f"sqlite:///{tmp_path / 'concurrent.db'}")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    with sessions() as session:
        client = Cliente(denominazione="Synthetic client")
        session.add(client)
        session.flush()
        invoice = Fattura(numero="1", anno=2026, cliente_id=client.id, stato=S.BOZZA)
        session.add(invoice)
        session.commit()
        invoice_id = invoice.id
    path = tmp_path / "race.xml"
    path.write_text("<xml/>")
    barrier, lock = Barrier(2), Lock()
    calls = []

    class Sender:
        settings = SimpleNamespace(
            pec_address="synthetic@example.invalid", pec_password="synthetic"
        )

        @journaled_submission
        def send(self, invoice, path, signed=False):
            with lock:
                calls.append(invoice.id)
            return True, None

    def worker():
        with sessions() as session:
            invoice = session.get(Fattura, invoice_id)
            barrier.wait(timeout=10)
            return Sender().send(invoice, path)[0]

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: worker(), range(2)))
        assert sorted(results) == [False, True]
        assert calls == [invoice_id]
        with sessions() as session:
            assert session.query(SDISubmissionAttempt).count() == 1
            assert session.get(Fattura, invoice_id).stato == S.INVIATA
    finally:
        engine.dispose()


def test_historical_sender_refuses_before_network(db_session, historical, test_settings, tmp_path):
    sender = PECSender(test_settings)
    with patch.object(sender, "_send_with_retry") as transport:
        assert not sender.send_invoice(historical, tmp_path / "absent.xml")[0]
        transport.assert_not_called()
    assert db_session.query(SDISubmissionAttempt).count() == 0


def test_uncertain_submission_is_exposed_to_assistant(db_session, sample_fattura):
    from openfatture.billing.application.invoice_queries import (
        get_invoice_details,
        get_invoice_stats,
    )

    db_session.add(
        SDISubmissionAttempt(
            invoice_id=sample_fattura.id,
            active_invoice_id=sample_fattura.id,
            filename="uncertain.xml",
            xml_sha256="a" * 64,
            outcome="uncertain",
        )
    )
    db_session.commit()
    details = get_invoice_details(sample_fattura.id, session=db_session)
    assert details["status_origin"] == "submission_uncertain"
    assert details["submission_state"] == "uncertain"
    stats = get_invoice_stats(sample_fattura.anno, session=db_session)
    assert stats["invii_da_verificare"][0]["invoice_id"] == sample_fattura.id
    assert sample_fattura.stato == S.BOZZA


def test_submission_path_uses_recorded_archive_identity(historical, test_settings):
    from pathlib import Path

    from openfatture.billing.fatture.service import InvoiceService

    assert InvoiceService(test_settings).get_xml_path(historical) == Path("/archive/exact.xml")
