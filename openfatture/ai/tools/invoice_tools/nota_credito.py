"""Nota di credito tools — thin adapter over billing.application.nota_credito_ops."""

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
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
            description="Create a nota di credito (TD04 credit note) from an existing invoice. Links to source invoice with FatturaPA DatiFattureCollegate. Supports full or partial refund.",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Source invoice ID to create credit note from",
                    required=True,
                ),
                ToolParameter(
                    name="note",
                    type=ToolParameterType.STRING,
                    description="Optional notes for the credit note",
                    required=False,
                ),
                ToolParameter(
                    name="full_refund",
                    type=ToolParameterType.BOOLEAN,
                    description="If True, copies all lines from source; if False, use line_items for partial refund (default True)",
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
