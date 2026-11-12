"""AI tool adapter over `openfatture.billing.application.vat_lookup` (VIES)."""

from typing import Any

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType, ToolRisk
from openfatture.billing.application.vat_lookup import check_vat_vies


def check_vat_number(vat_number: str, country_code: str = "IT") -> dict[str, Any]:
    from openfatture.platform.config import get_settings

    # The requester is the issuer from the configuration, never a model argument.
    return check_vat_vies(
        vat_number, country_code, requester_vat=get_settings().cedente_partita_iva or None
    )


def get_vat_tools() -> list[Tool]:
    return [
        Tool(
            name="check_vat_vies",
            risk=ToolRisk.LOOKUP,
            description=(
                "Check an EU VAT number in VIES, the European Commission registry, online. "
                "Sends only the VAT number and, as requester, the issuer's own partita IVA, "
                "so VIES returns request_identifier, the consultation number that proves "
                "the check. Returns valid, country_code, vat_number, name and address (as "
                "registered, possibly null when the member state does not disclose them), "
                "request_date and request_identifier. verifiable=false means the national "
                "registry or VIES does not answer now: the number is not invalid, it cannot "
                "be checked yet. Format errors are reported before any request. It does not "
                "change the client record; use update_client for that."
            ),
            category="vat",
            parameters=[
                ToolParameter(
                    name="vat_number",
                    type=ToolParameterType.STRING,
                    description=(
                        "VAT number, with or without the country prefix; spaces and dots "
                        "are ignored"
                    ),
                    required=True,
                ),
                ToolParameter(
                    name="country_code",
                    type=ToolParameterType.STRING,
                    description=(
                        "Two-letter VIES country code of the VAT number: EU member states "
                        "(EL for Greece) or XI for Northern Ireland; defaults to IT"
                    ),
                    required=False,
                    default="IT",
                ),
            ],
            func=check_vat_number,
            tags=["vat", "vies", "lookup", "online"],
        ),
    ]
