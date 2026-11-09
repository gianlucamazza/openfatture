"""Real database tests for collection operations and historical migration."""

import json
from datetime import date
from decimal import Decimal

import pytest

from openfatture.billing.application.invoice_queries import get_invoice_details
from openfatture.payment.application import collection_api as api
from openfatture.storage.database.models import (
    CollectionEntry,
    CollectionReceipt,
    Fattura,
    Pagamento,
)


def test_receipt_without_schedule_and_idempotent_replay(runtime_db, seed_fattura):
    invoice_id = seed_fattura.id
    result = api.record_collection("200.00", "record-1", invoice_id=invoice_id)
    assert result["success"], result
    assert api.record_collection("200.00", "record-1", invoice_id=invoice_id) == result
    assert api.record_collection("250.00", "record-1", invoice_id=invoice_id).get("error")
    assert get_invoice_details(invoice_id)["amount_paid"] == 200
    assert get_invoice_details(invoice_id)["outstanding"] == float(
        seed_fattura.totale - Decimal("200")
    )
    with runtime_db() as session:
        assert session.query(CollectionReceipt).count() == 1
        assert session.query(Pagamento).count() == 0


def test_split_allocation_is_atomic(runtime_db, seed_fattura):
    result = api.record_collection("500", "unassigned")
    receipt_id = result["receipt_id"]
    failed = api.allocate_collection_batch(
        receipt_id,
        json.dumps(
            [
                {"invoice_id": seed_fattura.id, "amount": "100"},
                {"invoice_id": 99999, "amount": "100"},
            ]
        ),
        "bad-split",
    )
    assert failed.get("error"), failed
    with runtime_db() as session:
        assert session.get(CollectionReceipt, receipt_id).allocated == 0
        assert session.query(CollectionEntry).count() == 0
    with runtime_db() as session:
        second = Fattura(
            numero="2", anno=2026, cliente_id=seed_fattura.cliente_id, totale=Decimal("500")
        )
        session.add(second)
        session.commit()
        second_id = second.id
    success = api.allocate_collection_batch(
        receipt_id,
        json.dumps(
            [
                {"invoice_id": seed_fattura.id, "amount": "100"},
                {"invoice_id": second_id, "amount": "200"},
            ]
        ),
        "good-split",
    )
    assert success["success"], success
    with runtime_db() as session:
        assert session.get(CollectionReceipt, receipt_id).allocated == 300


def test_manual_compatibility_tracks_corrections_and_unknown_dates(runtime_db, seed_fattura):
    created = api.create_payment(
        seed_fattura.id, float(seed_fattura.totale), None, 100, request_id="schedule"
    )
    assert created["success"], created
    changed = api.update_payment(created["payment_id"], importo_pagato=50, request_id="correct")
    assert changed["success"], changed
    with runtime_db() as session:
        payment = session.get(Pagamento, created["payment_id"])
        assert payment.data_scadenza is None
        assert payment.importo_pagato == 50
        assert session.query(CollectionEntry).count() == 2
    assert api.delete_payment(created["payment_id"]).get("error")


def test_owner_statement_does_not_invent_an_incasso(runtime_db, seed_fattura):
    result = api.declare_collection_status(
        seed_fattura.id, "not_settled", "owner", "owner-statement", "2026-11-09"
    )
    assert result["success"], result
    details = get_invoice_details(seed_fattura.id)
    assert details["amount_paid"] == 0
    assert details["collection_statement"] == {"value": "not_settled", "source": "owner"}


def test_legacy_opening_migration_preserves_cash(runtime_db, seed_fattura):
    from openfatture.payment.application.collection_migration import migrate_balances

    with runtime_db() as session:
        payment = Pagamento(
            fattura_id=seed_fattura.id,
            importo=seed_fattura.totale,
            importo_pagato=Decimal("500"),
            data_scadenza=date(2026, 11, 1),
        )
        session.add(payment)
        session.flush()
        migrate_balances(session)
        migrate_balances(session)
        session.commit()
        assert session.query(CollectionReceipt).count() == 1
        assert session.query(CollectionEntry).one().amount == 500
        assert payment.importo_pagato == 500


def test_bank_debit_is_rejected(db_session, bank_transaction):
    from openfatture.payment.application.bank_collections import bank_receipt

    bank_transaction.amount = Decimal("-500")
    with pytest.raises(ValueError, match="incoming"):
        bank_receipt(db_session, bank_transaction)
    assert db_session.query(CollectionReceipt).count() == 0


def test_concurrent_allocations_never_overdraw_receipt(runtime_db, seed_fattura):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    receipt_id = api.record_collection("100", "parallel-receipt")["receipt_id"]
    # Prepare opening balances before the competing operations.
    gate = Barrier(2)
    invoice_id = seed_fattura.id

    def attempt(key):
        gate.wait(timeout=10)
        return api.allocate_collection(receipt_id, invoice_id, "80", key)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, ["parallel-a", "parallel-b"]))
    assert sum(bool(result.get("success")) for result in results) == 1, results
    with runtime_db() as session:
        assert session.get(CollectionReceipt, receipt_id).allocated == 80
        assert sum(entry.amount for entry in session.query(CollectionEntry).all()) == 80


def test_events_are_discarded_on_rollback(runtime_db):
    from openfatture.payment.application.deferred_events import after_commit

    delivered = []
    with runtime_db() as session:
        session.begin()
        after_commit(session, lambda: delivered.append("rolled-back"))
        session.rollback()
        session.begin()
        after_commit(session, lambda: delivered.append("committed"))
        session.commit()
    assert delivered == ["committed"]


def test_migration_rejects_inconsistent_receipt_cache(runtime_db):
    from openfatture.payment.application.collection_migration import migrate_balances

    with runtime_db() as session:
        session.add(
            CollectionReceipt(request_id="broken", amount=100, allocated=50, origin="manual")
        )
        session.flush()
        with pytest.raises(ValueError, match="Ledger/cache mismatch"):
            migrate_balances(session)


def test_nested_rollback_does_not_publish_discarded_events(runtime_db):
    from openfatture.payment.application.deferred_events import after_commit

    delivered = []
    with runtime_db() as session:
        session.begin()
        after_commit(session, lambda: delivered.append("outer"))
        nested = session.begin_nested()
        after_commit(session, lambda: delivered.append("discarded"))
        nested.rollback()
        with session.begin_nested():
            after_commit(session, lambda: delivered.append("nested-committed"))
        assert delivered == []
        session.commit()
    assert delivered == ["outer", "nested-committed"]


def test_unknown_deadline_report_does_not_claim_all_settled(runtime_db, seed_fattura):
    from openfatture.billing.application.report_queries import get_due_dates

    assert api.create_payment(seed_fattura.id, 100, None, request_id="unknown-deadline")["success"]
    result = get_due_dates()
    assert result["has_outstanding"] is True
    assert result["without_due_date"][0]["due_date"] is None
    assert result["without_due_date"][0]["residual"] == 100


def test_historical_invoice_participates_in_revenue_report(runtime_db, seed_fattura):
    from openfatture.billing.application.report_queries import generate_client_report

    with runtime_db() as session:
        session.get(Fattura, seed_fattura.id).issued_elsewhere = True
        session.commit()
    result = generate_client_report(anno=seed_fattura.anno)
    assert result["total_revenue"] == float(seed_fattura.totale), result


@pytest.mark.parametrize("direct_collection", [False, True])
def test_reminder_does_not_send_with_unknown_deadline_or_unassigned_cash(
    runtime_db, seed_fattura, direct_collection
):
    import asyncio
    from unittest.mock import AsyncMock, Mock

    from openfatture.payment.application.services.reminder_scheduler import ReminderScheduler
    from openfatture.payment.domain.enums import ReminderStrategy
    from openfatture.payment.domain.models import PaymentReminder

    result = api.create_payment(
        seed_fattura.id,
        100,
        "2026-11-09" if direct_collection else None,
        request_id="reminder-installment",
    )
    if direct_collection:
        assert api.record_collection("50", "unassigned-to-installment", invoice_id=seed_fattura.id)[
            "success"
        ]
    with runtime_db() as session:
        payment = session.get(Pagamento, result["payment_id"])
        reminder = PaymentReminder(
            payment_id=payment.id,
            payment=payment,
            reminder_date=date.today(),
            strategy=ReminderStrategy.DEFAULT,
        )
        repo = Mock()
        repo.get_due_reminders.return_value = [reminder]
        notifier = Mock()
        notifier.send_reminder = AsyncMock(return_value=True)
        scheduler = ReminderScheduler(repo, Mock(), notifier)
        assert asyncio.run(scheduler.process_due_reminders()) == 0
        notifier.send_reminder.assert_not_called()
