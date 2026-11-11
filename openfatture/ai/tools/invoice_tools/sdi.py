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
                "Generate the FatturaPA XML of an invoice, validate it against the XSD and, "
                "if valid, save it in the archive with the SDI file name (returns xml_path). "
                "Use it to produce the XML file, to check it before sending, and before "
                "sign_invoice_xml. It does not transmit anything."
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
            description="Send invoice to SDI via PEC. CRITICAL: Cannot be undone!",
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
                    description="Whether XML is digitally signed (default False)",
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
