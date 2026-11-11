"""Cassa previdenziale tools — adapter over billing.application.cassa_ops."""

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType, ToolRisk
from openfatture.billing.application.cassa_ops import set_cassa_previdenziale

__all__ = ["set_cassa_previdenziale"]


def tools() -> list[Tool]:
    """Assistant tool definitions for the cassa previdenziale."""
    return [
        Tool(
            name="set_cassa_previdenziale",
            risk=ToolRisk.MUTATE,
            description=(
                "Set or remove the invoice's social security contribution (rivalsa, "
                "DatiCassaPrevidenziale), e.g. INPS gestione separata TC22 at 4%. "
                "The amount is computed on the lines (excluding N1) and added to the totals."
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
                    name="tipo_cassa",
                    type=ToolParameterType.STRING,
                    description="TC01..TC22 (TC22 = INPS gestione separata); omit to remove",
                    required=False,
                ),
                ToolParameter(
                    name="al_cassa",
                    type=ToolParameterType.NUMBER,
                    description="Contribution rate percentage (e.g. 4)",
                    required=False,
                    default=0,
                ),
                ToolParameter(
                    name="aliquota_iva",
                    type=ToolParameterType.NUMBER,
                    description="VAT rate on the contribution; omit for the cedente default",
                    required=False,
                ),
                ToolParameter(
                    name="natura",
                    type=ToolParameterType.STRING,
                    description="VAT natura of the contribution with a 0% rate (default N2.2 for forfettario)",
                    required=False,
                ),
            ],
            func=set_cassa_previdenziale,
            requires_confirmation=True,
            examples=[
                "set_cassa_previdenziale(fattura_id=12, tipo_cassa='TC22', al_cassa=4)",
                "set_cassa_previdenziale(fattura_id=12)",
            ],
            tags=["write", "update"],
        ),
    ]
