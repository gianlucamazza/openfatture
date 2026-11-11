"""AI tool adapters over the preventivo application services."""

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType, ToolRisk
from openfatture.billing.application.preventivo_commands import (
    convert_preventivo_to_invoice,
    create_preventivo,
    delete_preventivo,
    update_preventivo,
    update_preventivo_status,
)
from openfatture.billing.application.preventivo_queries import (
    get_preventivo_details,
    search_preventivi,
)


def get_preventivo_tools() -> list[Tool]:
    """
    Get all preventivo-related tools.

    Returns:
        List of Tool instances
    """
    return [
        Tool(
            name="search_preventivi",
            risk=ToolRisk.READ,
            description=(
                "List quotes (preventivi) filtered by status, client and year, newest first. "
                "Each result has preventivo_id, numero (number/year), data_emissione, "
                "data_scadenza, cliente and cliente_id, imponibile, iva, totale, stato, "
                "validita_giorni and righe_count; has_more is true when the limit was reached. "
                "Use get_preventivo_details for the lines of one quote."
            ),
            category="preventivi",
            parameters=[
                ToolParameter(
                    name="stato",
                    type=ToolParameterType.STRING,
                    description="Quote status; convertito means already turned into an invoice; omit for any status",
                    required=False,
                    enum=["bozza", "inviato", "accettato", "rifiutato", "scaduto", "convertito"],
                ),
                ToolParameter(
                    name="cliente_id",
                    type=ToolParameterType.INTEGER,
                    description="Client ID (from search_clients); omit for all clients",
                    required=False,
                ),
                ToolParameter(
                    name="anno",
                    type=ToolParameterType.INTEGER,
                    description="Quote year (4 digits, 2000-2100); omit for all years",
                    required=False,
                ),
                ToolParameter(
                    name="limit",
                    type=ToolParameterType.INTEGER,
                    description="Maximum number of quotes returned, 1-100; default 20",
                    required=False,
                    default=20,
                ),
            ],
            func=search_preventivi,
            examples=[
                "search_preventivi()",
                "search_preventivi(stato='inviato', anno=2025)",
                "search_preventivi(cliente_id=5, limit=10)",
            ],
            tags=["search", "preventivo", "quote"],
        ),
        Tool(
            name="get_preventivo_details",
            risk=ToolRisk.READ,
            description=(
                "Return one quote in full: numero, dates (emissione, scadenza), "
                "validita_giorni, cliente (id, denominazione, partita_iva, email), imponibile, "
                "iva, totale, stato, note, condizioni, the lines (numero_riga, descrizione, "
                "quantita, prezzo_unitario, unita_misura, aliquota_iva, natura and amounts) and "
                "fattura_id when it was converted to an invoice. Returns an error when the quote "
                "does not exist."
            ),
            category="preventivi",
            parameters=[
                ToolParameter(
                    name="preventivo_id",
                    type=ToolParameterType.INTEGER,
                    description="Quote ID (preventivo_id from search_preventivi)",
                    required=True,
                ),
            ],
            func=get_preventivo_details,
            examples=["get_preventivo_details(preventivo_id=123)"],
            tags=["preventivo", "details", "quote"],
        ),
        Tool(
            name="create_preventivo",
            risk=ToolRisk.MUTATE,
            description=(
                "Create a quote (preventivo) in BOZZA status for an existing client, with its "
                "lines, numbered progressively in the current year and dated today; the expiry "
                "date is today plus validita_giorni. Totals are computed from the lines with the "
                "invoice rounding rules. Returns preventivo_id, numero, data_emissione, "
                "data_scadenza, totale and stato. Fails when there are no lines, a line lacks "
                "descrizione, quantita or prezzo_unitario, a line has an inconsistent VAT rate "
                "and natura, or the client does not exist. Lines cannot be edited afterwards: "
                "only notes, conditions and validity, through update_preventivo."
            ),
            category="preventivi",
            parameters=[
                ToolParameter(
                    name="cliente_id",
                    type=ToolParameterType.INTEGER,
                    description="Client ID (from search_clients)",
                    required=True,
                ),
                ToolParameter(
                    name="righe",
                    type=ToolParameterType.ARRAY,
                    description="Quote lines, at least one, numbered in the order given",
                    required=True,
                    items={
                        "type": "object",
                        "properties": {
                            "descrizione": {
                                "type": "string",
                                "description": "Line description as printed on the quote",
                            },
                            "quantita": {
                                "type": "number",
                                "description": "Quantity in unita_misura (decimals allowed)",
                            },
                            "prezzo_unitario": {
                                "type": "number",
                                "description": "Unit price in euros, VAT excluded",
                            },
                            "aliquota_iva": {
                                "type": "number",
                                "description": "VAT rate percentage; omit for the cedente default (0% in the forfettario regime, else 22%)",
                            },
                            "natura": {
                                "type": "string",
                                "description": "VAT natura, valid only with a 0% rate; defaults to N2.2 in the forfettario regime",
                            },
                            "unita_misura": {
                                "type": "string",
                                "description": "Unit of measure, e.g. ore, giorni, servizio; default 'ore'",
                            },
                        },
                        "required": ["descrizione", "quantita", "prezzo_unitario"],
                    },
                ),
                ToolParameter(
                    name="validita_giorni",
                    type=ToolParameterType.INTEGER,
                    description="Days the quote stays valid, 1-365; default 30",
                    required=False,
                    default=30,
                ),
                ToolParameter(
                    name="note",
                    type=ToolParameterType.STRING,
                    description="Free-text notes; they are copied to the invoice on conversion",
                    required=False,
                ),
                ToolParameter(
                    name="condizioni",
                    type=ToolParameterType.STRING,
                    description="Terms and conditions printed on the quote (payment, delivery, scope)",
                    required=False,
                ),
            ],
            func=create_preventivo,
            requires_confirmation=True,
            examples=[
                """create_preventivo(
                cliente_id=5,
                righe=[{"descrizione": "Web consulting", "quantita": 8, "prezzo_unitario": 80, "aliquota_iva": 22}],
                validita_giorni=30
            )"""
            ],
            tags=["create", "preventivo", "quote", "write"],
        ),
        Tool(
            name="update_preventivo_status",
            risk=ToolRisk.MUTATE,
            description=(
                "Set the status of a quote to any of the listed values, for example inviato when "
                "it was sent to the client or accettato when the client agreed. No transition "
                "order is enforced; only a converted quote (convertito) is refused. Returns "
                "preventivo_id and new_status; fails when the quote is not found. To turn an "
                "accepted quote into an invoice use convert_preventivo_to_invoice, which sets "
                "convertito itself."
            ),
            category="preventivi",
            parameters=[
                ToolParameter(
                    name="preventivo_id",
                    type=ToolParameterType.INTEGER,
                    description="Quote ID",
                    required=True,
                ),
                ToolParameter(
                    name="new_status",
                    type=ToolParameterType.STRING,
                    description="Target status of the quote",
                    required=True,
                    enum=["bozza", "inviato", "accettato", "rifiutato", "scaduto"],
                ),
            ],
            func=update_preventivo_status,
            requires_confirmation=True,
            examples=[
                "update_preventivo_status(preventivo_id=123, new_status='inviato')",
                "update_preventivo_status(preventivo_id=456, new_status='accettato')",
            ],
            tags=["update", "preventivo", "status", "write"],
        ),
        Tool(
            name="update_preventivo",
            risk=ToolRisk.MUTATE,
            description=(
                "Change the notes, conditions or validity of a quote in BOZZA status; only the "
                "fields passed and different from the current values are changed. A new "
                "validita_giorni moves data_scadenza to the issue date plus that many days. "
                "Returns preventivo_id, numero, changes and the new data_scadenza; when nothing "
                "differs it succeeds with no changes. Fails when the quote is not found or not "
                "in BOZZA. Lines, client and amounts cannot be changed."
            ),
            category="preventivi",
            parameters=[
                ToolParameter(
                    name="preventivo_id",
                    type=ToolParameterType.INTEGER,
                    description="Quote ID",
                    required=True,
                ),
                ToolParameter(
                    name="note",
                    type=ToolParameterType.STRING,
                    description="New notes, replacing the current ones; omit to keep them",
                    required=False,
                ),
                ToolParameter(
                    name="condizioni",
                    type=ToolParameterType.STRING,
                    description="New terms and conditions, replacing the current ones; omit to keep them",
                    required=False,
                ),
                ToolParameter(
                    name="validita_giorni",
                    type=ToolParameterType.INTEGER,
                    description="New validity in days from the issue date, 1-365; omit to keep it",
                    required=False,
                ),
            ],
            func=update_preventivo,
            requires_confirmation=True,
            examples=[
                "update_preventivo(preventivo_id=123, note='Updated notes')",
                "update_preventivo(preventivo_id=456, validita_giorni=45)",
            ],
            tags=["update", "preventivo", "write"],
        ),
        Tool(
            name="delete_preventivo",
            risk=ToolRisk.MUTATE,
            description=(
                "Delete a quote in BOZZA status and its lines. Irreversible. Returns "
                "preventivo_id and numero. Fails when the quote is not found, is in any other "
                "status, or is linked to an invoice. To withdraw a quote already sent, set it "
                "to rifiutato or scaduto with update_preventivo_status instead."
            ),
            category="preventivi",
            parameters=[
                ToolParameter(
                    name="preventivo_id",
                    type=ToolParameterType.INTEGER,
                    description="Quote ID",
                    required=True,
                ),
            ],
            func=delete_preventivo,
            requires_confirmation=True,
            examples=["delete_preventivo(preventivo_id=123)"],
            tags=["delete", "preventivo", "write", "critical"],
        ),
        Tool(
            name="convert_preventivo_to_invoice",
            risk=ToolRisk.MUTATE,
            description=(
                "Create an invoice from a quote and mark the quote convertito. Irreversible: the "
                "quote can no longer be changed or converted again. The invoice is a TD01 in "
                "BOZZA status for the same client, numbered in the current year and dated "
                "today, with the quote's lines and notes; totals are recomputed. Returns "
                "fattura_id, fattura_numero and totale. Fails when the quote is not found, "
                "already converted, scaduto, or past its data_scadenza. The invoice can then be "
                "edited like any draft (update_invoice, create_riga)."
            ),
            category="preventivi",
            parameters=[
                ToolParameter(
                    name="preventivo_id",
                    type=ToolParameterType.INTEGER,
                    description="Quote ID",
                    required=True,
                ),
            ],
            func=convert_preventivo_to_invoice,
            requires_confirmation=True,
            examples=["convert_preventivo_to_invoice(preventivo_id=123)"],
            tags=["convert", "preventivo", "invoice", "write", "critical"],
        ),
    ]
