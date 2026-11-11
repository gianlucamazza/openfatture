"""Tools for client operations.

Adapters over ``billing.application.client_queries`` (reads) and
``billing.application.client_commands`` (writes).
"""

from typing import Any

from pydantic import validate_call

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType, ToolRisk
from openfatture.billing.application import client_queries
from openfatture.billing.application.client_commands import (
    create_client,
    delete_client,
    update_client,
)


@validate_call
def search_clients(
    query: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Search for clients."""
    return client_queries.search_clients(query=query, limit=limit)


@validate_call
def get_client_details(cliente_id: int) -> dict[str, Any]:
    """Get detailed information about a client."""
    return client_queries.get_client_details(cliente_id)


@validate_call
def get_client_stats() -> dict[str, Any]:
    """Get statistics about clients."""
    return client_queries.get_client_stats()


# Re-export write commands for tool registry
__all_writes = (create_client, update_client, delete_client)


def get_client_tools() -> list[Tool]:
    """
    Get all client-related tools.

    Returns:
        List of Tool instances
    """
    return [
        Tool(
            name="search_clients",
            risk=ToolRisk.READ,
            description=(
                "Find clients whose name, partita IVA or codice fiscale contains the query "
                "(case-insensitive substring), ordered by name. Returns count, has_more and "
                "clienti with id, denominazione, partita_iva, codice_fiscale, email and "
                "fatture_count. Use it to resolve a client id before get_client_details or "
                "any invoice operation; without a query it lists clients alphabetically."
            ),
            category="clients",
            parameters=[
                ToolParameter(
                    name="query",
                    type=ToolParameterType.STRING,
                    description=(
                        "Text matched as a substring of name, partita IVA or codice fiscale; "
                        "omit to list all clients"
                    ),
                    required=False,
                ),
                ToolParameter(
                    name="limit",
                    type=ToolParameterType.INTEGER,
                    description=(
                        "Maximum clients returned, 1 to 100 (default 10); has_more is true "
                        "when the page is full and more may exist"
                    ),
                    required=False,
                    default=10,
                ),
            ],
            func=search_clients,
            examples=[
                "search_clients(query='Rossi')",
                "search_clients(query='12345678901')",
                "search_clients(limit=5)",
            ],
            tags=["search", "query"],
        ),
        Tool(
            name="get_client_details",
            risk=ToolRisk.READ,
            description=(
                "Return one client's full record: identifiers, address (via, cap, comune, "
                "provincia, nazione), contacts (email, pec, telefono), fatture_count and the "
                "5 most recent invoices (id, numero, anno, data, importo, stato). Returns an "
                "error when the id does not exist; use search_clients to find the id."
            ),
            category="clients",
            parameters=[
                ToolParameter(
                    name="cliente_id",
                    type=ToolParameterType.INTEGER,
                    description="Numeric client id, as returned by search_clients",
                    required=True,
                ),
            ],
            func=get_client_details,
            examples=["get_client_details(cliente_id=1)"],
            tags=["details", "view"],
        ),
        Tool(
            name="get_client_stats",
            risk=ToolRisk.READ,
            description=(
                "Return client counts: totale_clienti and how many have a partita IVA "
                "(con_partita_iva), an email (con_email) and a PEC (con_pec). It does not "
                "return revenue; use generate_client_report for revenue by client."
            ),
            category="clients",
            parameters=[],
            func=get_client_stats,
            examples=["get_client_stats()"],
            tags=["stats", "analytics"],
        ),
        # WRITE tools
        Tool(
            name="create_client",
            risk=ToolRisk.MUTATE,
            description=(
                "Create a client and return client_id, denominazione, partita_iva and "
                "codice_fiscale. At least one of partita_iva or codice_fiscale is required. "
                "If a client with the same partita IVA or codice fiscale exists, nothing is "
                "created and the error carries existing_client_id. Field formats are stored "
                "as given and are not validated here."
            ),
            category="clients",
            parameters=[
                ToolParameter(
                    name="denominazione",
                    type=ToolParameterType.STRING,
                    description="Company name, or first and last name for a private person",
                    required=True,
                ),
                ToolParameter(
                    name="partita_iva",
                    type=ToolParameterType.STRING,
                    description="Italian partita IVA, 11 digits without the IT prefix",
                    required=False,
                ),
                ToolParameter(
                    name="codice_fiscale",
                    type=ToolParameterType.STRING,
                    description=(
                        "Codice fiscale: 16 alphanumeric characters for a person, or 11 digits "
                        "for a company"
                    ),
                    required=False,
                ),
                ToolParameter(
                    name="email",
                    type=ToolParameterType.STRING,
                    description="Ordinary email address",
                    required=False,
                ),
                ToolParameter(
                    name="pec",
                    type=ToolParameterType.STRING,
                    description=(
                        "Certified email (PEC) address; the SDI can deliver invoices to it "
                        "when there is no codice destinatario"
                    ),
                    required=False,
                ),
                ToolParameter(
                    name="indirizzo",
                    type=ToolParameterType.STRING,
                    description="Street and house number",
                    required=False,
                ),
                ToolParameter(
                    name="cap",
                    type=ToolParameterType.STRING,
                    description="Postal code (CAP), 5 digits for Italian addresses",
                    required=False,
                ),
                ToolParameter(
                    name="comune",
                    type=ToolParameterType.STRING,
                    description="Municipality (comune)",
                    required=False,
                ),
                ToolParameter(
                    name="provincia",
                    type=ToolParameterType.STRING,
                    description="Province code, 2 uppercase letters such as MI or RM",
                    required=False,
                ),
                ToolParameter(
                    name="nazione",
                    type=ToolParameterType.STRING,
                    description="ISO 3166-1 alpha-2 country code (default IT)",
                    required=False,
                    default="IT",
                ),
                ToolParameter(
                    name="codice_destinatario",
                    type=ToolParameterType.STRING,
                    description=(
                        "SDI codice destinatario, 7 alphanumeric characters; omit when the "
                        "client receives by PEC or has none"
                    ),
                    required=False,
                ),
                ToolParameter(
                    name="telefono",
                    type=ToolParameterType.STRING,
                    description="Phone number, free format",
                    required=False,
                ),
                ToolParameter(
                    name="note",
                    type=ToolParameterType.STRING,
                    description="Free-text internal notes about the client",
                    required=False,
                ),
            ],
            func=create_client,
            requires_confirmation=True,
            examples=[
                "create_client(denominazione='Acme Corp', partita_iva='12345678901', "
                "email='info@acme.com')",
                "create_client(denominazione='Mario Rossi', codice_fiscale='RSSMRA80A01H501X', "
                "pec='mario@pec.it')",
            ],
            tags=["write", "create"],
        ),
        Tool(
            name="update_client",
            risk=ToolRisk.MUTATE,
            description=(
                "Change fields of an existing client. Only the fields passed are written; "
                "omitted fields keep their value and a field cannot be cleared to empty. "
                "Returns client_id and changes, the list of fields that actually changed "
                "(empty with a no-change message when every value matches). Returns an "
                "error when the id does not exist. Unlike create_client it does not check "
                "for another client with the same partita IVA or codice fiscale."
            ),
            category="clients",
            parameters=[
                ToolParameter(
                    name="cliente_id",
                    type=ToolParameterType.INTEGER,
                    description="Numeric id of the client to change",
                    required=True,
                ),
                ToolParameter(
                    name="denominazione",
                    type=ToolParameterType.STRING,
                    description="New company or person name",
                    required=False,
                ),
                ToolParameter(
                    name="partita_iva",
                    type=ToolParameterType.STRING,
                    description="New partita IVA, 11 digits without the IT prefix",
                    required=False,
                ),
                ToolParameter(
                    name="codice_fiscale",
                    type=ToolParameterType.STRING,
                    description="New codice fiscale (16 characters, or 11 digits for a company)",
                    required=False,
                ),
                ToolParameter(
                    name="email",
                    type=ToolParameterType.STRING,
                    description="New ordinary email address",
                    required=False,
                ),
                ToolParameter(
                    name="pec",
                    type=ToolParameterType.STRING,
                    description="New certified email (PEC) address",
                    required=False,
                ),
                ToolParameter(
                    name="indirizzo",
                    type=ToolParameterType.STRING,
                    description="New street and house number",
                    required=False,
                ),
                ToolParameter(
                    name="cap",
                    type=ToolParameterType.STRING,
                    description="New postal code (CAP)",
                    required=False,
                ),
                ToolParameter(
                    name="comune",
                    type=ToolParameterType.STRING,
                    description="New municipality (comune)",
                    required=False,
                ),
                ToolParameter(
                    name="provincia",
                    type=ToolParameterType.STRING,
                    description="New province code, 2 uppercase letters",
                    required=False,
                ),
                ToolParameter(
                    name="nazione",
                    type=ToolParameterType.STRING,
                    description="New ISO 3166-1 alpha-2 country code",
                    required=False,
                ),
                ToolParameter(
                    name="codice_destinatario",
                    type=ToolParameterType.STRING,
                    description="New SDI codice destinatario, 7 alphanumeric characters",
                    required=False,
                ),
                ToolParameter(
                    name="telefono",
                    type=ToolParameterType.STRING,
                    description="New phone number, free format",
                    required=False,
                ),
                ToolParameter(
                    name="note",
                    type=ToolParameterType.STRING,
                    description="New internal notes; replaces the existing text",
                    required=False,
                ),
            ],
            func=update_client,
            requires_confirmation=True,
            examples=[
                "update_client(cliente_id=1, email='newemail@acme.com')",
                "update_client(cliente_id=5, pec='newpec@pec.it', telefono='+39 02 1234567')",
            ],
            tags=["write", "update"],
        ),
        Tool(
            name="delete_client",
            risk=ToolRisk.MUTATE,
            description=(
                "Permanently delete a client. Irreversible. Refused, with fatture_count in "
                "the error, when the client has any invoice; returns an error when the id "
                "does not exist. On success returns client_id and denominazione."
            ),
            category="clients",
            parameters=[
                ToolParameter(
                    name="cliente_id",
                    type=ToolParameterType.INTEGER,
                    description="Numeric id of the client to delete",
                    required=True,
                ),
            ],
            func=delete_client,
            requires_confirmation=True,
            examples=[
                "delete_client(cliente_id=5)",
            ],
            tags=["write", "delete", "critical"],
        ),
    ]
