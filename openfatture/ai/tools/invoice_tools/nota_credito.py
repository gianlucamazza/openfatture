"""Nota di credito tools — thin adapter over billing.application.nota_credito_ops."""

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType, ToolRisk
from openfatture.billing.application.nota_credito_ops import (
    create_nota_credito_from_fattura,
)

__all__ = [
    "create_nota_credito_from_fattura",
]


def tools() -> list[Tool]:
    """Assistant tool definitions for credit notes."""
    return [
        Tool(
            name="create_nota_credito_from_fattura",
            risk=ToolRisk.MUTATE,
            description=(
                "Create a credit note (nota di credito, TD04) for the whole of an existing "
                "invoice: a new BOZZA document for the same client, numbered in the current "
                "year and dated today, linked to the source in DatiFattureCollegate, with every "
                "line copied at positive amounts and the same social security contribution. "
                "Returns nota_credito_id, numero, anno, totale and source_invoice. Fails when "
                "the source invoice is not found or has no lines. Partial credit notes are not "
                "available through this tool: full_refund=false is refused because the lines "
                "to credit cannot be passed. The alternative is a TD04 made with create_invoice "
                "and create_riga, which has no link to the source invoice. Nothing is sent to "
                "SDI."
            ),
            category="invoices",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="ID of the invoice being credited",
                    required=True,
                ),
                ToolParameter(
                    name="note",
                    type=ToolParameterType.STRING,
                    description="Free-text notes stored on the credit note, e.g. the reason for the refund",
                    required=False,
                ),
                ToolParameter(
                    name="full_refund",
                    type=ToolParameterType.BOOLEAN,
                    description="Credit every line of the source invoice; default true. false is refused (no line selection is exposed)",
                    required=False,
                    default=True,
                ),
            ],
            func=create_nota_credito_from_fattura,
            requires_confirmation=True,
            examples=[
                "create_nota_credito_from_fattura(fattura_id=123, note='Storno completo')",
                "create_nota_credito_from_fattura(fattura_id=456, full_refund=False, note='Storno parziale')",
            ],
            tags=["write", "create", "credit_note", "storno"],
        ),
    ]
