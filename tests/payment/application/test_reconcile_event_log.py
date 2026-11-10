"""Manual reconciliation reaches the global event system end to end."""

from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

import openfatture.events.base as events_base
import openfatture.events.listeners as events_listeners
from openfatture.events import initialize_event_system
from openfatture.payment.application.payment_commands import reconcile_payment
from openfatture.payment.domain.enums import TransactionStatus
from openfatture.payment.domain.models import BankAccount, BankTransaction
from openfatture.storage.database.models import EventLog, Pagamento, StatoPagamento


@pytest.fixture
def fresh_event_system(monkeypatch, runtime_db):
    monkeypatch.setattr(events_base, "_global_event_bus", None)
    monkeypatch.setattr(events_listeners, "_persistence_listener", None)
    return initialize_event_system()


def test_reconcile_payment_persists_transaction_matched_event(
    fresh_event_system, runtime_session, seed_fattura
):
    pagamento = Pagamento(
        fattura_id=seed_fattura.id,
        importo=Decimal("1220.00"),
        data_scadenza=date.today() + timedelta(days=30),
        stato=StatoPagamento.DA_PAGARE,
    )
    account = BankAccount(name="Conto", iban="IT60X0542811101000000123456")
    runtime_session.add_all([pagamento, account])
    runtime_session.flush()
    transaction = BankTransaction(
        id=uuid4(),
        account_id=account.id,
        date=date.today(),
        amount=Decimal("1220.00"),
        description="Bonifico fattura 1/2025",
        status=TransactionStatus.UNMATCHED,
    )
    runtime_session.add(transaction)
    runtime_session.commit()

    result = reconcile_payment(str(transaction.id), pagamento.id)

    assert "error" not in result, result
    runtime_session.expire_all()
    logs = runtime_session.query(EventLog).filter_by(event_type="TransactionMatchedEvent").all()
    assert len(logs) == 1
    assert logs[0].entity_type == "payment"
    assert logs[0].entity_id == pagamento.id
