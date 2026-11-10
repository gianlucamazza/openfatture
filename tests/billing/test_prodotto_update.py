"""Selective product updates: validation, change tracking and failure handling."""

from decimal import Decimal
from typing import Any

import pytest

from openfatture.billing.application import prodotto_ops
from openfatture.storage.database.models import Prodotto


@pytest.fixture
def product_id(runtime_db) -> int:
    created = prodotto_ops.create_prodotto(
        codice="SRV-1", descrizione="Consulenza", prezzo_unitario=80
    )
    assert created["success"], created
    return int(created["prodotto_id"])


@pytest.mark.parametrize(
    ("fields", "error"),
    [
        ({"descrizione": ""}, "descrizione must be 1-500 characters"),
        ({"descrizione": "x" * 501}, "descrizione must be 1-500 characters"),
        ({"prezzo_unitario": 0}, "prezzo_unitario must be positive"),
        ({"aliquota_iva": -1}, "aliquota_iva must be between 0 and 100"),
        ({"aliquota_iva": 101}, "aliquota_iva must be between 0 and 100"),
        ({"unita_misura": "x" * 11}, "unita_misura must be max 10 characters"),
        ({"categoria": "x" * 101}, "categoria must be max 100 characters"),
    ],
)
def test_invalid_values_are_rejected(fields: dict[str, Any], error: str):
    assert prodotto_ops.update_prodotto(1, **fields) == {"success": False, "error": error}


def test_missing_product_is_reported(runtime_db):
    assert prodotto_ops.update_prodotto(999) == {
        "success": False,
        "error": "Prodotto 999 not found",
    }


def test_no_fields_is_reported(product_id: int):
    assert prodotto_ops.update_prodotto(product_id) == {
        "success": False,
        "error": "No fields to update (all parameters are None)",
    }


def test_every_field_is_updated_in_order(runtime_session, product_id: int):
    result = prodotto_ops.update_prodotto(
        product_id,
        descrizione="Sviluppo",
        prezzo_unitario=90.5,
        aliquota_iva=10,
        unita_misura="giorni",
        categoria="IT",
        is_servizio=False,
        note="nota",
    )
    assert result["changes"] == [
        "descrizione",
        "prezzo_unitario",
        "aliquota_iva",
        "unita_misura",
        "categoria",
        "is_servizio",
        "note",
    ]
    assert result["message"] == "Prodotto 'SRV-1' aggiornato (7 campi)"
    prodotto = runtime_session.get(Prodotto, product_id)
    assert (
        prodotto.descrizione,
        prodotto.prezzo_unitario,
        prodotto.aliquota_iva,
        prodotto.unita_misura,
        prodotto.categoria,
        prodotto.is_servizio,
        prodotto.note,
    ) == ("Sviluppo", Decimal("90.50"), Decimal("10.00"), "giorni", "IT", False, "nota")


def test_failure_is_reported(monkeypatch: pytest.MonkeyPatch, product_id: int):
    def boom(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("log sink down")

    monkeypatch.setattr(prodotto_ops.logger, "info", boom)
    assert prodotto_ops.update_prodotto(product_id, note="x") == {
        "success": False,
        "error": "log sink down",
    }
