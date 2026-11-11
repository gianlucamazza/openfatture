"""AI tool adapters over `openfatture.billing.application.prodotto_ops`."""

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType, ToolRisk
from openfatture.billing.application.prodotto_ops import (
    create_prodotto,
    delete_prodotto,
    get_prodotto_details,
    search_prodotti,
    update_prodotto,
)


def get_prodotto_tools() -> list[Tool]:
    """
    Get all product/service catalog tools.

    Returns:
        List of Tool instances
    """
    return [
        Tool(
            name="search_prodotti",
            risk=ToolRisk.READ,
            description=(
                "List catalogue entries (products and services with a default price) ordered by "
                "code, filtered by exact category, type, and case-insensitive partial matches "
                "on code or description. Each result has prodotto_id, codice, descrizione, "
                "prezzo_unitario, aliquota_iva, unita_misura, categoria and is_servizio; "
                "has_more is true when the limit was reached. Invoice and quote lines are not "
                "linked to the catalogue: pass the price, VAT rate and unit found here to "
                "create_riga or create_preventivo."
            ),
            category="prodotti",
            parameters=[
                ToolParameter(
                    name="categoria",
                    type=ToolParameterType.STRING,
                    description="Category, exact and case-sensitive match; omit for all categories",
                    required=False,
                ),
                ToolParameter(
                    name="is_servizio",
                    type=ToolParameterType.BOOLEAN,
                    description="true for services only, false for goods only; omit for both",
                    required=False,
                ),
                ToolParameter(
                    name="codice_contains",
                    type=ToolParameterType.STRING,
                    description="Text contained in the code, case-insensitive",
                    required=False,
                ),
                ToolParameter(
                    name="descrizione_contains",
                    type=ToolParameterType.STRING,
                    description="Text contained in the description, case-insensitive",
                    required=False,
                ),
                ToolParameter(
                    name="limit",
                    type=ToolParameterType.INTEGER,
                    description="Maximum number of entries returned, 1-100; default 20",
                    required=False,
                    default=20,
                ),
            ],
            func=search_prodotti,
            examples=[
                "search_prodotti()",
                "search_prodotti(categoria='Consulting', is_servizio=True)",
                "search_prodotti(codice_contains='WEB', limit=10)",
            ],
            tags=["search", "prodotto", "catalog"],
        ),
        Tool(
            name="get_prodotto_details",
            risk=ToolRisk.READ,
            description=(
                "Return one catalogue entry with codice, descrizione, prezzo_unitario, "
                "aliquota_iva, unita_misura, categoria, is_servizio and note, plus usage_stats: "
                "times_used (invoice lines referencing it) and the five most recent of those "
                "invoices. Returns an error when the entry does not exist."
            ),
            category="prodotti",
            parameters=[
                ToolParameter(
                    name="prodotto_id",
                    type=ToolParameterType.INTEGER,
                    description="Catalogue entry ID (prodotto_id from search_prodotti)",
                    required=True,
                ),
            ],
            func=get_prodotto_details,
            examples=["get_prodotto_details(prodotto_id=1)"],
            tags=["prodotto", "details", "catalog"],
        ),
        Tool(
            name="create_prodotto",
            risk=ToolRisk.MUTATE,
            description=(
                "Add a product or service to the catalogue with its default price, VAT rate and "
                "unit. Returns prodotto_id, codice, descrizione, prezzo_unitario and "
                "aliquota_iva. Fails when the code already exists (the error gives the existing "
                "ID) or a value is out of range. The catalogue is a reference list: it does not "
                "change any invoice or quote."
            ),
            category="prodotti",
            parameters=[
                ToolParameter(
                    name="codice",
                    type=ToolParameterType.STRING,
                    description="Unique catalogue code, 1-50 characters (e.g. WEB-CONS)",
                    required=True,
                ),
                ToolParameter(
                    name="descrizione",
                    type=ToolParameterType.STRING,
                    description="Description used on lines, 1-500 characters",
                    required=True,
                ),
                ToolParameter(
                    name="prezzo_unitario",
                    type=ToolParameterType.NUMBER,
                    description="Default unit price in euros, VAT excluded, greater than 0",
                    required=True,
                ),
                ToolParameter(
                    name="aliquota_iva",
                    type=ToolParameterType.NUMBER,
                    description="VAT rate percentage, 0-100; default 22. No natura is stored, so a 0% rate needs one on each line",
                    required=False,
                    default=22.0,
                ),
                ToolParameter(
                    name="unita_misura",
                    type=ToolParameterType.STRING,
                    description="Unit of measure, at most 10 characters (e.g. ore, giorni, pz); default 'ore'",
                    required=False,
                    default="ore",
                ),
                ToolParameter(
                    name="categoria",
                    type=ToolParameterType.STRING,
                    description="Category for grouping and filtering, at most 100 characters",
                    required=False,
                ),
                ToolParameter(
                    name="is_servizio",
                    type=ToolParameterType.BOOLEAN,
                    description="true for a service, false for goods; default true",
                    required=False,
                    default=True,
                ),
                ToolParameter(
                    name="note",
                    type=ToolParameterType.STRING,
                    description="Free-text internal notes",
                    required=False,
                ),
            ],
            func=create_prodotto,
            requires_confirmation=True,
            examples=[
                'create_prodotto(codice="WEB-CONS", descrizione="Web consulting hourly rate", prezzo_unitario=80.0)',
                'create_prodotto(codice="GDPR-AUD", descrizione="GDPR audit service", prezzo_unitario=150.0, categoria="Compliance", aliquota_iva=22.0)',
            ],
            tags=["create", "prodotto", "catalog", "write"],
        ),
        Tool(
            name="update_prodotto",
            risk=ToolRisk.MUTATE,
            description=(
                "Change the fields passed on a catalogue entry; the code cannot be changed. "
                "Returns prodotto_id, codice and the list of fields set. Fails when the entry "
                "is not found, no field is given, or a value is out of range (same limits as "
                "create_prodotto). Existing invoice and quote lines keep their own prices."
            ),
            category="prodotti",
            parameters=[
                ToolParameter(
                    name="prodotto_id",
                    type=ToolParameterType.INTEGER,
                    description="Catalogue entry ID",
                    required=True,
                ),
                ToolParameter(
                    name="descrizione",
                    type=ToolParameterType.STRING,
                    description="New description, 1-500 characters; omit to keep it",
                    required=False,
                ),
                ToolParameter(
                    name="prezzo_unitario",
                    type=ToolParameterType.NUMBER,
                    description="New unit price in euros, VAT excluded, greater than 0; omit to keep it",
                    required=False,
                ),
                ToolParameter(
                    name="aliquota_iva",
                    type=ToolParameterType.NUMBER,
                    description="New VAT rate percentage, 0-100; omit to keep it",
                    required=False,
                ),
                ToolParameter(
                    name="unita_misura",
                    type=ToolParameterType.STRING,
                    description="New unit of measure, at most 10 characters; omit to keep it",
                    required=False,
                ),
                ToolParameter(
                    name="categoria",
                    type=ToolParameterType.STRING,
                    description="New category, at most 100 characters; omit to keep it",
                    required=False,
                ),
                ToolParameter(
                    name="is_servizio",
                    type=ToolParameterType.BOOLEAN,
                    description="true for a service, false for goods; omit to keep it",
                    required=False,
                ),
                ToolParameter(
                    name="note",
                    type=ToolParameterType.STRING,
                    description="New notes, replacing the current ones; omit to keep them",
                    required=False,
                ),
            ],
            func=update_prodotto,
            requires_confirmation=True,
            examples=[
                "update_prodotto(prodotto_id=1, prezzo_unitario=90.0)",
                'update_prodotto(prodotto_id=2, descrizione="Updated description", categoria="New Category")',
            ],
            tags=["update", "prodotto", "catalog", "write"],
        ),
        Tool(
            name="delete_prodotto",
            risk=ToolRisk.MUTATE,
            description=(
                "Delete a catalogue entry. Irreversible. Returns prodotto_id, codice, "
                "descrizione, was_used and usage_count. An entry referenced by invoice lines is "
                "refused (the error reports usage_count) unless force is true; with force the "
                "lines stay unchanged and only lose the reference. Fails when the entry is not "
                "found."
            ),
            category="prodotti",
            parameters=[
                ToolParameter(
                    name="prodotto_id",
                    type=ToolParameterType.INTEGER,
                    description="Catalogue entry ID",
                    required=True,
                ),
                ToolParameter(
                    name="force",
                    type=ToolParameterType.BOOLEAN,
                    description="Also delete an entry referenced by invoice lines; default false refuses it",
                    required=False,
                    default=False,
                ),
            ],
            func=delete_prodotto,
            requires_confirmation=True,
            examples=[
                "delete_prodotto(prodotto_id=5)",
                "delete_prodotto(prodotto_id=10, force=True)",
            ],
            tags=["delete", "prodotto", "catalog", "write", "critical"],
        ),
    ]
