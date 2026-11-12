"""Check an EU VAT number in VIES, the European Commission's registry.

The one online lookup of the assistant. It is deliberately narrow: the
endpoint is fixed, only a validated VAT number (and the issuer's own, as
requester) leaves the computer, and the answer is reduced to a few typed
fields. The free text VIES returns (name, address) is truncated and stripped
of control characters, because it is untrusted data that reaches the model.

API: https://ec.europa.eu/assets/taxud/vow-information/swagger_publicVAT.yaml
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

import httpx

from openfatture.platform.logging import get_logger
from openfatture.platform.validators import validate_partita_iva

logger = get_logger(__name__)

VIES_URL = "https://ec.europa.eu/taxation_customs/vies/rest-api/check-vat-number"
# National registries answer through VIES in seconds, sometimes in about 30.
TIMEOUT = httpx.Timeout(35.0, connect=10.0)
TEXT_LIMIT = 200
SOURCE = "VIES – Commissione europea"

# VIES country codes: EU member states (Greece is EL) and XI for Northern Ireland.
MEMBER_STATES = frozenset(
    "AT BE BG CY CZ DE DK EE EL ES FI FR HR HU IE IT LT LU LV MT NL PL PT RO SE SI SK XI".split()
)
_VAT_PATTERN = re.compile(r"^[0-9A-Z+*]{2,12}$")
# Member-state errors that mean "cannot be checked now", not "invalid".
_UNAVAILABLE = frozenset(
    {
        "MS_UNAVAILABLE",
        "MS_MAX_CONCURRENT_REQ",
        "GLOBAL_MAX_CONCURRENT_REQ",
        "SERVICE_UNAVAILABLE",
        "TIMEOUT",
    }
)


def normalize(vat_number: str, country_code: str) -> tuple[str, str]:
    """Upper-case country and number, without spaces, dots or a repeated prefix.

    Raises ``ValueError`` with a message for the user when either is invalid.
    """
    country = country_code.strip().upper()
    if country == "GR":
        country = "EL"
    if country not in MEMBER_STATES:
        raise ValueError(f"{country_code!r} is not an EU country code known to VIES")
    number = re.sub(r"[\s.\-]", "", vat_number).upper()
    if number.startswith(country) or (country == "EL" and number.startswith("GR")):
        number = number[2:]
    if not _VAT_PATTERN.match(number):
        raise ValueError(f"{vat_number!r} is not a VAT number format accepted by VIES")
    if country == "IT" and not validate_partita_iva(number):
        raise ValueError(f"{vat_number!r} is not a valid Italian partita IVA")
    return country, number


def _clean(text: Any) -> str | None:
    """Single-line, printable, bounded text; VIES returns '---' when undisclosed."""
    if not isinstance(text, str):
        return None
    printable = "".join(
        " " if unicodedata.category(c)[0] == "C" else c for c in text.replace("\n", " ")
    )
    collapsed = " ".join(printable.split())
    if not collapsed or collapsed == "---":
        return None
    return collapsed[:TEXT_LIMIT]


def _error_codes(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return []
    return [
        str(wrapper.get("error"))
        for wrapper in payload.get("errorWrappers") or []
        if isinstance(wrapper, dict) and wrapper.get("error")
    ]


def check_vat_vies(
    vat_number: str,
    country_code: str = "IT",
    *,
    requester_vat: str | None = None,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Ask VIES whether ``vat_number`` is a valid VAT registration in ``country_code``.

    ``requester_vat`` (an Italian partita IVA) makes VIES return a consultation
    number, ``request_identifier``, which proves the check. A service outage
    returns ``verifiable: False``; it does not mean the number is invalid.
    """
    try:
        country, number = normalize(vat_number, country_code)
    except ValueError as exc:
        return {"error": str(exc), "source": SOURCE}
    body: dict[str, str] = {"countryCode": country, "vatNumber": number}
    if requester_vat and validate_partita_iva(requester_vat):
        body |= {"requesterMemberStateCode": "IT", "requesterNumber": requester_vat}
    try:
        if client is None:
            with httpx.Client(timeout=TIMEOUT, follow_redirects=False) as owned:
                response = owned.post(VIES_URL, json=body)
        else:
            response = client.post(VIES_URL, json=body)
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("vies_request_failed", country=country, error=type(exc).__name__)
        return {
            "verifiable": False,
            "error": "VIES cannot be reached now (network or service error); try again later",
            "source": SOURCE,
        }
    codes = _error_codes(payload)
    if response.status_code != 200 or codes:
        if not codes or any(code in _UNAVAILABLE for code in codes):
            return {
                "verifiable": False,
                "error": (
                    f"The {country} VAT registry does not answer VIES now"
                    f" ({', '.join(codes) or response.status_code}); this is not an invalid number"
                ),
                "source": SOURCE,
            }
        return {"error": f"VIES refused the request: {', '.join(codes)}", "source": SOURCE}
    logger.info("vies_checked", country=country, valid=bool(payload.get("valid")))
    return {
        "verifiable": True,
        "valid": bool(payload.get("valid")),
        "country_code": country,
        "vat_number": number,
        "name": _clean(payload.get("name")),
        "address": _clean(payload.get("address")),
        "request_date": _clean(payload.get("requestDate")),
        "request_identifier": _clean(payload.get("requestIdentifier")),
        "source": SOURCE,
    }
