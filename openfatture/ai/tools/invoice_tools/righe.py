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
            description=(
                "Append a line to an invoice in BOZZA or DA_INVIARE status and recompute the "
                "invoice totals (lines, social security contribution and stamp duty). Returns "
                "riga_id, numero_riga, the line imponibile, iva and totale, and invoice_totale. "
                "Fails when the invoice is not found, is in another status, or the VAT rate and "
                "natura are inconsistent (a 0% rate needs a natura outside the forfettario "
                "regime; a natura needs a 0% rate). Catalogue products are not linked: copy "
                "price and VAT from search_prodotti. For a training course billed as one lump "
                "sum use create_course_line."
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
                    name="descrizione",
                    type=ToolParameterType.STRING,
                    description="Line description as printed on the invoice",
                    required=True,
                ),
                ToolParameter(
                    name="quantita",
                    type=ToolParameterType.NUMBER,
                    description="Quantity in unita_misura (decimals allowed, e.g. 7.5 hours)",
                    required=True,
                ),
                ToolParameter(
                    name="prezzo_unitario",
                    type=ToolParameterType.NUMBER,
                    description="Unit price in euros, VAT excluded",
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
                    description="Unit of measure, e.g. ore, giorni, servizio, pz; default 'ore'",
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
            description=(
                "Change the fields passed on one invoice line, when the invoice is in BOZZA or "
                "DA_INVIARE status; a change of quantity, price, rate or natura recomputes the "
                "line and the invoice totals. Returns riga_id, numero_riga, changes, the line "
                "amounts and invoice_totale; when nothing differs it succeeds with no changes. "
                "Fails when the line is not found, the invoice status does not allow edits, or "
                "the resulting rate and natura are inconsistent. Setting a 0% rate without "
                "natura keeps the line's current natura."
            ),
            category="invoices",
            parameters=[
                ToolParameter(
                    name="riga_id",
                    type=ToolParameterType.INTEGER,
                    description="Line ID (riga_id returned by create_riga or create_course_line)",
                    required=True,
                ),
                ToolParameter(
                    name="descrizione",
                    type=ToolParameterType.STRING,
                    description="New line description; omit to keep it",
                    required=False,
                ),
                ToolParameter(
                    name="quantita",
                    type=ToolParameterType.NUMBER,
                    description="New quantity in the line's unit of measure; omit to keep it",
                    required=False,
                ),
                ToolParameter(
                    name="prezzo_unitario",
                    type=ToolParameterType.NUMBER,
                    description="New unit price in euros, VAT excluded; omit to keep it",
                    required=False,
                ),
                ToolParameter(
                    name="aliquota_iva",
                    type=ToolParameterType.NUMBER,
                    description="New VAT rate percentage (e.g. 22, 10, 0); omit to keep it",
                    required=False,
                ),
                ToolParameter(
                    name="natura",
                    type=ToolParameterType.STRING,
                    description="New VAT natura, valid only with a 0% rate (e.g. N2.2 forfettario, N1, N4 exempt); omit to keep it",
                    required=False,
                ),
                ToolParameter(
                    name="unita_misura",
                    type=ToolParameterType.STRING,
                    description="New unit of measure (e.g. ore, giorni, servizio); omit to keep it",
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
            description=(
                "Remove one line from an invoice in BOZZA or DA_INVIARE status and recompute the "
                "invoice totals. Irreversible. Returns riga_id, numero_riga, descrizione, "
                "riga_totale (the removed amount) and invoice_totale. Fails when the line is not "
                "found or the invoice status does not allow edits. Remaining lines keep their "
                "numero_riga."
            ),
            category="invoices",
            parameters=[
                ToolParameter(
                    name="riga_id",
                    type=ToolParameterType.INTEGER,
                    description="Line ID (riga_id returned by create_riga or create_course_line)",
                    required=True,
                ),
            ],
            func=delete_riga,
            requires_confirmation=True,
            examples=["delete_riga(riga_id=5)"],
            tags=["write", "delete", "critical"],
        ),
    ]
