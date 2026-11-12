"""VIES lookup: fixed endpoint, validated input, bounded output; no real network."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from openfatture.billing.application import vat_lookup
from openfatture.billing.application.vat_lookup import VIES_URL, check_vat_vies, normalize


def _client(status: int, payload: Any, seen: list[httpx.Request] | None = None) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(request)
        return httpx.Response(status, json=payload)

    return httpx.Client(transport=httpx.MockTransport(handler))


@pytest.mark.parametrize(
    ("raw", "country", "expected"),
    [
        ("IT 12345678903", "it", ("IT", "12345678903")),
        ("123.456.789.03", "IT", ("IT", "12345678903")),
        ("DE123456789", "DE", ("DE", "123456789")),
        ("EL123456789", "GR", ("EL", "123456789")),
        ("GR123456789", "EL", ("EL", "123456789")),
    ],
)
def test_numbers_are_normalized(raw: str, country: str, expected: tuple[str, str]) -> None:
    assert normalize(raw, country) == expected


@pytest.mark.parametrize(
    ("raw", "country", "reason"),
    [
        ("12345678903", "US", "not an EU country"),
        ("ABC", "XX", "not an EU country"),
        ("12345678901", "IT", "not a valid Italian"),
        ("1234/5678", "DE", "not a VAT number format"),
        ("1", "FR", "not a VAT number format"),
    ],
)
def test_invalid_input_never_reaches_the_network(raw: str, country: str, reason: str) -> None:
    def fail(request: httpx.Request) -> httpx.Response:
        raise AssertionError("no request expected")

    client = httpx.Client(transport=httpx.MockTransport(fail))
    result = check_vat_vies(raw, country, client=client)
    assert reason in result["error"]


def test_a_valid_number_returns_the_registered_data() -> None:
    seen: list[httpx.Request] = []
    payload = {
        "countryCode": "DE",
        "vatNumber": "123456789",
        "valid": True,
        "name": "Beispiel\nGmbH\x07",
        "address": "x" * 500,
        "requestDate": "2026-11-12T10:00:00.000Z",
        "requestIdentifier": "WAPIAAAAX1",
    }
    result = check_vat_vies(
        "DE 123456789", "DE", requester_vat="12345678903", client=_client(200, payload, seen)
    )
    assert result == {
        "verifiable": True,
        "valid": True,
        "country_code": "DE",
        "vat_number": "123456789",
        "name": "Beispiel GmbH",
        "address": "x" * vat_lookup.TEXT_LIMIT,
        "request_date": "2026-11-12T10:00:00.000Z",
        "request_identifier": "WAPIAAAAX1",
        "source": vat_lookup.SOURCE,
    }
    assert str(seen[0].url) == VIES_URL
    assert json.loads(seen[0].content) == {
        "countryCode": "DE",
        "vatNumber": "123456789",
        "requesterMemberStateCode": "IT",
        "requesterNumber": "12345678903",
    }


def test_an_invalid_number_and_undisclosed_details() -> None:
    payload = {"valid": False, "name": "---", "address": "---"}
    result = check_vat_vies("12345678903", client=_client(200, payload))
    assert result["valid"] is False
    assert result["name"] is None and result["address"] is None


def test_an_invalid_requester_is_not_sent() -> None:
    seen: list[httpx.Request] = []
    check_vat_vies("DE123456789", "DE", requester_vat="nope", client=_client(200, {}, seen))
    assert "requesterNumber" not in json.loads(seen[0].content)


@pytest.mark.parametrize("code", ["MS_UNAVAILABLE", "MS_MAX_CONCURRENT_REQ", "TIMEOUT"])
def test_an_outage_is_not_an_invalid_number(code: str) -> None:
    payload = {"actionSucceed": False, "errorWrappers": [{"error": code, "message": "x"}]}
    result = check_vat_vies("DE123456789", "DE", client=_client(500, payload))
    assert result["verifiable"] is False
    assert "not an invalid number" in result["error"]
    assert "valid" not in result


def test_a_refused_request_is_an_error() -> None:
    payload = {"actionSucceed": False, "errorWrappers": [{"error": "INVALID_INPUT"}]}
    result = check_vat_vies("DE123456789", "DE", client=_client(400, payload))
    assert result["error"] == "VIES refused the request: INVALID_INPUT"


def test_network_failure_is_not_verifiable() -> None:
    def broken(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timeout", request=request)

    client = httpx.Client(transport=httpx.MockTransport(broken))
    result = check_vat_vies("DE123456789", "DE", client=client)
    assert result["verifiable"] is False
    assert "cannot be reached" in result["error"]


def test_the_tool_takes_the_requester_from_the_configuration(monkeypatch) -> None:
    from types import SimpleNamespace

    from openfatture.ai.tools import vat_tools

    calls: list[dict[str, Any]] = []

    def record(*args: Any, **kwargs: Any) -> dict[str, Any]:
        calls.append({"args": args, **kwargs})
        return {}

    monkeypatch.setattr(vat_tools, "check_vat_vies", record)
    monkeypatch.setattr(
        "openfatture.platform.config.get_settings",
        lambda: SimpleNamespace(cedente_partita_iva="12345678903"),
    )
    vat_tools.check_vat_number("DE123456789", "DE")
    assert calls == [{"args": ("DE123456789", "DE"), "requester_vat": "12345678903"}]
