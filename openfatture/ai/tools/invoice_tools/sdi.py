"""Invoice SDI tools — adapters over sdi.application.invoice_sdi_ops."""

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType, ToolRisk
from openfatture.sdi.application.invoice_sdi_ops import (
    generate_invoice_xml,
    send_invoice_to_sdi,
)

__all__ = ["generate_invoice_xml", "send_invoice_to_sdi"]


def tools() -> list[Tool]:
    """Assistant tool definitions for the FatturaPA XML and SDI sending."""
    return [
        Tool(
            name="generate_invoice_xml",
            risk=ToolRisk.LOCAL_ARTIFACT,
            description=(
                "Build the FatturaPA XML of an invoice from its current data, validate it "
                "against the XSD and, only when valid, write it to the archive (archivio/xml) "
                "with the SDI file name and record the path on the invoice. Returns valid, "
                "invoice_number and xml_path; when invalid it returns valid=false with the "
                "validation error and writes nothing. Fails when the invoice is not found or "
                "has no lines. Use it to produce or check the XML and before sign_invoice_xml; "
                "it transmits nothing."
            ),
            category="invoices",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID",
                    required=True,
                ),
            ],
            func=generate_invoice_xml,
            examples=["generate_invoice_xml(fattura_id=123)"],
            tags=["xml", "validation", "file"],
        ),
        Tool(
            name="send_invoice_to_sdi",
            risk=ToolRisk.TRANSMIT,
            description=(
                "Transmit an invoice in BOZZA or DA_INVIARE status to SDI by PEC. Irreversible: "
                "the document reaches the tax authority. Unsigned, the XML is regenerated from "
                "the current data and validated first; signed, the stored .p7m is sent only "
                "when it matches the current invoice data. Returns invoice_number, stato, "
                "data_invio and sdi_address. Fails for invoices issued elsewhere, other "
                "statuses, no lines, invalid XML, a missing or stale signature, or a PEC error."
            ),
            category="invoices",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID",
                    required=True,
                ),
                ToolParameter(
                    name="signed",
                    type=ToolParameterType.BOOLEAN,
                    description="Send the signed .p7m made by sign_invoice_xml instead of the plain XML; default false",
                    required=False,
                    default=False,
                ),
            ],
            func=send_invoice_to_sdi,
            requires_confirmation=True,
            enabled=False,
            examples=[
                "send_invoice_to_sdi(fattura_id=123)",
                "send_invoice_to_sdi(fattura_id=123, signed=True)",
            ],
            tags=["write", "send", "critical", "transmit"],
        ),
    ]
