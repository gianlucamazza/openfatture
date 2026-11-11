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
                "Set or remove the social security contribution (rivalsa, "
                "DatiCassaPrevidenziale) of an invoice in BOZZA or DA_INVIARE status, e.g. INPS "
                "gestione separata TC22 at 4%. An invoice has at most one contribution: setting "
                "it replaces any existing one, and omitting tipo_cassa removes it. The amount is "
                "computed on the taxable amount of the lines excluding N1 lines, and the invoice "
                "totals and stamp duty are recomputed. Returns importo_contributo_cassa, "
                "invoice_totale and importo_bollo. Fails when the invoice is not found or not "
                "editable, tipo_cassa is not TC01-TC22, al_cassa is not above 0 and at most 100, "
                "or the VAT rate and natura are inconsistent."
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
                    description="Fund code TC01-TC22 (TC22 = INPS gestione separata); omit to remove the contribution",
                    required=False,
                ),
                ToolParameter(
                    name="al_cassa",
                    type=ToolParameterType.NUMBER,
                    description="Contribution rate in percent, above 0 and at most 100 (e.g. 4); required with tipo_cassa",
                    required=False,
                    default=0,
                ),
                ToolParameter(
                    name="aliquota_iva",
                    type=ToolParameterType.NUMBER,
                    description="VAT rate percentage on the contribution; omit for the cedente default (0% in the forfettario regime, else 22%)",
                    required=False,
                ),
                ToolParameter(
                    name="natura",
                    type=ToolParameterType.STRING,
                    description="VAT natura of the contribution, valid only with a 0% rate; defaults to N2.2 in the forfettario regime",
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
