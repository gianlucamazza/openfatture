"""Invoice SDI tools — adapters over sdi.application.invoice_sdi_ops."""

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType, ToolRisk
from openfatture.sdi.application.invoice_sdi_ops import (
    send_invoice_to_sdi,
    validate_invoice_xml,
)

__all__ = ["validate_invoice_xml", "send_invoice_to_sdi"]


def tools() -> list[Tool]:
    """Assistant tool definitions for SDI validation and sending."""
    return [
        Tool(
            name="validate_invoice_xml",
            risk=ToolRisk.READ,
            description="Validate FatturaPA XML for invoice before sending to SDI",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID",
                    required=True,
                ),
            ],
            func=validate_invoice_xml,
            examples=["validate_invoice_xml(fattura_id=123)"],
            tags=["validation", "xml"],
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
