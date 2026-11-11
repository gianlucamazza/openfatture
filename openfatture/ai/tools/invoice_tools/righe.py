"""Invoice line tools — adapters over billing.application.line_commands."""

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType, ToolRisk
from openfatture.billing.application.line_commands import (
    create_riga,
    delete_riga,
    update_riga,
)

__all__ = ["create_riga", "update_riga", "delete_riga"]


def tools() -> list[Tool]:
    """Assistant tool definitions for invoice lines."""
    return [
        Tool(
            name="create_riga",
            risk=ToolRisk.MUTATE,
            description="Add line item to invoice. Updates invoice totals automatically.",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID",
                    required=True,
                ),
                ToolParameter(
                    name="descrizione",
                    type=ToolParameterType.STRING,
                    description="Item description",
                    required=True,
                ),
                ToolParameter(
                    name="quantita",
                    type=ToolParameterType.NUMBER,
                    description="Quantity",
                    required=True,
                ),
                ToolParameter(
                    name="prezzo_unitario",
                    type=ToolParameterType.NUMBER,
                    description="Unit price in euros",
                    required=True,
                ),
                ToolParameter(
                    name="aliquota_iva",
                    type=ToolParameterType.NUMBER,
                    description=(
                        "VAT rate percentage; omit for the cedente default "
                        "(0% with natura N2.2 in the forfettario regime, else 22%)"
                    ),
                    required=False,
                ),
                ToolParameter(
                    name="unita_misura",
                    type=ToolParameterType.STRING,
                    description="Unit of measure (default 'ore')",
                    required=False,
                    default="ore",
                ),
                ToolParameter(
                    name="natura",
                    type=ToolParameterType.STRING,
                    description=(
                        "VAT natura, only with a 0% rate: N2.2 forfettario (default), "
                        "N1 for the stamp duty charged to the customer, N4 exempt, ..."
                    ),
                    required=False,
                ),
            ],
            func=create_riga,
            requires_confirmation=True,
            examples=[
                "create_riga(fattura_id=123, descrizione='Web consulting', quantita=3, prezzo_unitario=150)",
                "create_riga(fattura_id=123, descrizione='Backend dev', quantita=8, prezzo_unitario=100, aliquota_iva=22)",
            ],
            tags=["write", "create"],
        ),
        Tool(
            name="update_riga",
            risk=ToolRisk.MUTATE,
            description="Update line item in invoice (only BOZZA or DA_INVIARE). Updates invoice totals automatically.",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="riga_id",
                    type=ToolParameterType.INTEGER,
                    description="Line item ID",
                    required=True,
                ),
                ToolParameter(
                    name="descrizione",
                    type=ToolParameterType.STRING,
                    description="Item description",
                    required=False,
                ),
                ToolParameter(
                    name="quantita",
                    type=ToolParameterType.NUMBER,
                    description="Quantity",
                    required=False,
                ),
                ToolParameter(
                    name="prezzo_unitario",
                    type=ToolParameterType.NUMBER,
                    description="Unit price in euros",
                    required=False,
                ),
                ToolParameter(
                    name="aliquota_iva",
                    type=ToolParameterType.NUMBER,
                    description="VAT rate percentage",
                    required=False,
                ),
                ToolParameter(
                    name="natura",
                    type=ToolParameterType.STRING,
                    description="VAT natura, only with a 0% rate (e.g. N2.2, N1, N4)",
                    required=False,
                ),
                ToolParameter(
                    name="unita_misura",
                    type=ToolParameterType.STRING,
                    description="Unit of measure",
                    required=False,
                ),
            ],
            func=update_riga,
            requires_confirmation=True,
            examples=[
                "update_riga(riga_id=5, quantita=5)",
                "update_riga(riga_id=10, descrizione='Updated consulting', prezzo_unitario=200)",
            ],
            tags=["write", "update"],
        ),
        Tool(
            name="delete_riga",
            risk=ToolRisk.MUTATE,
            description="CRITICAL: Delete line item from invoice (only BOZZA or DA_INVIARE). Updates invoice totals automatically.",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="riga_id",
                    type=ToolParameterType.INTEGER,
                    description="Line item ID to delete",
                    required=True,
                ),
            ],
            func=delete_riga,
            requires_confirmation=True,
            examples=["delete_riga(riga_id=5)"],
            tags=["write", "delete", "critical"],
        ),
    ]
