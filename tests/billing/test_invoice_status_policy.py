from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from openfatture.billing.application.invoice_status import validate_manual_transition
from openfatture.billing.batch.operations import bulk_update_status
from openfatture.storage.database.models import StatoFattura as S


def invoice(historical=False):
    return SimpleNamespace(
        stato=S.BOZZA, issued_elsewhere=historical, righe=[object()], cliente=object()
    )


def test_historical_transition_refused():
    with pytest.raises(ValueError):
        validate_manual_transition(invoice(True), S.DA_INVIARE)


def test_manual_cannot_assert_sdi_delivery():
    with pytest.raises(ValueError):
        validate_manual_transition(invoice(), S.CONSEGNATA)


def test_batch_is_validated_before_mutation():
    first, second = invoice(), invoice(True)
    session = MagicMock()
    result = bulk_update_status([first, second], S.DA_INVIARE, session)
    assert result.succeeded == 0
    assert first.stato == S.BOZZA
    session.commit.assert_not_called()
    session.rollback.assert_called_once()


def test_same_status_is_noop():
    validate_manual_transition(invoice(True), S.BOZZA)
