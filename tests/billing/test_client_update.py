"""Field-level behaviour of the client update use case on a real database."""

from __future__ import annotations

from typing import Any

import pytest

import openfatture.events as events
from openfatture.billing.application.client_commands import update_client
from openfatture.events import ClientUpdatedEvent
from openfatture.storage.database.models import Cliente

NEW_VALUES: dict[str, str] = {
    "denominazione": "Acme Italia",
    "partita_iva": "01234567890",
    "codice_fiscale": "RSSMRA80A01H501U",
    "email": "new@acme.com",
    "pec": "new@pec.it",
    "indirizzo": "Via Milano 2",
    "cap": "00100",
    "comune": "Roma",
    "provincia": "RM",
    "nazione": "SM",
    "codice_destinatario": "XYZ9876",
    "telefono": "+39 06 1234",
    "note": "VIP",
}


class Bus:
    def __init__(self) -> None:
        self.events: list[Any] = []

    def publish(self, event: Any) -> None:
        self.events.append(event)


@pytest.fixture
def bus(monkeypatch: pytest.MonkeyPatch) -> Bus:
    recorder = Bus()
    monkeypatch.setattr(events, "get_global_event_bus", lambda: recorder)
    return recorder


def test_every_field_is_updated_in_declaration_order(runtime_session, seed_cliente, bus) -> None:
    result = update_client(seed_cliente.id, **NEW_VALUES)

    assert result == {
        "success": True,
        "client_id": seed_cliente.id,
        "denominazione": "Acme Italia",
        "changes": list(NEW_VALUES),
        "message": "Client updated successfully. Changed fields: " + ", ".join(NEW_VALUES),
    }
    runtime_session.expire_all()
    stored = runtime_session.get(Cliente, seed_cliente.id)
    assert {field: getattr(stored, field) for field in NEW_VALUES} == NEW_VALUES
    (event,) = bus.events
    assert isinstance(event, ClientUpdatedEvent)
    assert event.client_id == seed_cliente.id
    assert event.client_name == "Acme Italia"
    assert event.updated_fields == list(NEW_VALUES)


def test_unchanged_and_omitted_fields_are_not_reported(runtime_session, seed_cliente, bus) -> None:
    result = update_client(
        seed_cliente.id, denominazione="Acme Corporation", email="other@acme.com", comune=None
    )

    assert result["changes"] == ["email"]
    runtime_session.expire_all()
    stored = runtime_session.get(Cliente, seed_cliente.id)
    assert stored.email == "other@acme.com"
    assert stored.comune == "Milano"


def test_identical_values_make_no_changes(runtime_session, seed_cliente, bus) -> None:
    current = {field: getattr(seed_cliente, field) for field in NEW_VALUES if field != "note"}

    result = update_client(seed_cliente.id, **current)

    assert result == {
        "success": True,
        "client_id": seed_cliente.id,
        "message": "No changes made (all fields same as current values)",
    }
    assert bus.events == []


def test_missing_client_is_reported(runtime_session, bus) -> None:
    assert update_client(987654, email="x@example.com") == {"error": "Client 987654 not found"}


def test_without_event_bus_update_still_succeeds(
    runtime_session, seed_cliente, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(events, "get_global_event_bus", lambda: None)
    assert update_client(seed_cliente.id, note="later")["changes"] == ["note"]


def test_failure_returns_error(
    runtime_session, seed_cliente, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken() -> None:
        raise RuntimeError("bus offline")

    monkeypatch.setattr(events, "get_global_event_bus", broken)

    result = update_client(seed_cliente.id, telefono="000")

    assert set(result) == {"error"}
    assert result["error"]
