"""Tools for client operations.

Adapters over ``billing.application.client_queries`` (reads) and
``billing.application.client_commands`` (writes).
"""

from typing import Any

from pydantic import validate_call

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
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
            description="Search for clients by name, partita IVA, or codice fiscale",
            category="clients",
            parameters=[
                ToolParameter(
                    name="query",
                    type=ToolParameterType.STRING,
                    description="Search query (name, P.IVA, or CF)",
                    required=False,
                ),
                ToolParameter(
                    name="limit",
                    type=ToolParameterType.INTEGER,
                    description="Maximum number of results",
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
            description="Get detailed information about a specific client",
            category="clients",
            parameters=[
                ToolParameter(
                    name="cliente_id",
                    type=ToolParameterType.INTEGER,
                    description="Client ID",
                    required=True,
                ),
            ],
            func=get_client_details,
            examples=["get_client_details(cliente_id=1)"],
            tags=["details", "view"],
        ),
        Tool(
            name="get_client_stats",
            description="Get statistics about all clients",
            category="clients",
            parameters=[],
            func=get_client_stats,
            examples=["get_client_stats()"],
            tags=["stats", "analytics"],
        ),
        # WRITE tools
        Tool(
            name="create_client",
            description="Create a new client. Requires at least partita_iva or codice_fiscale.",
            category="clients",
            parameters=[
                ToolParameter(
                    name="denominazione",
                    type=ToolParameterType.STRING,
                    description="Client name or company name (required)",
                    required=True,
                ),
                ToolParameter(
                    name="partita_iva",
                    type=ToolParameterType.STRING,
                    description="VAT number (Partita IVA) - 11 digits",
                    required=False,
                ),
                ToolParameter(
                    name="codice_fiscale",
                    type=ToolParameterType.STRING,
                    description="Tax code (Codice Fiscale) - 16 characters",
                    required=False,
                ),
                ToolParameter(
                    name="email",
                    type=ToolParameterType.STRING,
                    description="Email address",
                    required=False,
                ),
                ToolParameter(
                    name="pec",
                    type=ToolParameterType.STRING,
                    description="PEC email address",
                    required=False,
                ),
                ToolParameter(
                    name="indirizzo",
                    type=ToolParameterType.STRING,
                    description="Street address",
                    required=False,
                ),
                ToolParameter(
                    name="cap",
                    type=ToolParameterType.STRING,
                    description="Postal code",
                    required=False,
                ),
                ToolParameter(
                    name="comune",
                    type=ToolParameterType.STRING,
                    description="City/Municipality",
                    required=False,
                ),
                ToolParameter(
                    name="provincia",
                    type=ToolParameterType.STRING,
                    description="Province (2 letters, e.g. MI, RM)",
                    required=False,
                ),
                ToolParameter(
                    name="nazione",
                    type=ToolParameterType.STRING,
                    description="Country code (default IT)",
                    required=False,
                    default="IT",
                ),
                ToolParameter(
                    name="codice_destinatario",
                    type=ToolParameterType.STRING,
                    description="SDI recipient code (7 characters)",
                    required=False,
                ),
                ToolParameter(
                    name="telefono",
                    type=ToolParameterType.STRING,
                    description="Phone number",
                    required=False,
                ),
                ToolParameter(
                    name="note",
                    type=ToolParameterType.STRING,
                    description="Additional notes",
                    required=False,
                ),
            ],
            func=create_client,
            requires_confirmation=True,
            examples=[
                "create_client(denominazione='Acme Corp', partita_iva='12345678901', email='info@acme.com')",
                "create_client(denominazione='Mario Rossi', codice_fiscale='RSSMRA80A01H501X', pec='mario@pec.it')",
            ],
            tags=["write", "create"],
        ),
        Tool(
            name="update_client",
            description="Update client information. Only provided fields will be updated.",
            category="clients",
            parameters=[
                ToolParameter(
                    name="cliente_id",
                    type=ToolParameterType.INTEGER,
                    description="Client ID (required)",
                    required=True,
                ),
                ToolParameter(
                    name="denominazione",
                    type=ToolParameterType.STRING,
                    description="Client name",
                    required=False,
                ),
                ToolParameter(
                    name="partita_iva",
                    type=ToolParameterType.STRING,
                    description="VAT number",
                    required=False,
                ),
                ToolParameter(
                    name="codice_fiscale",
                    type=ToolParameterType.STRING,
                    description="Tax code",
                    required=False,
                ),
                ToolParameter(
                    name="email",
                    type=ToolParameterType.STRING,
                    description="Email",
                    required=False,
                ),
                ToolParameter(
                    name="pec",
                    type=ToolParameterType.STRING,
                    description="PEC email",
                    required=False,
                ),
                ToolParameter(
                    name="indirizzo",
                    type=ToolParameterType.STRING,
                    description="Street address",
                    required=False,
                ),
                ToolParameter(
                    name="cap",
                    type=ToolParameterType.STRING,
                    description="Postal code",
                    required=False,
                ),
                ToolParameter(
                    name="comune",
                    type=ToolParameterType.STRING,
                    description="City",
                    required=False,
                ),
                ToolParameter(
                    name="provincia",
                    type=ToolParameterType.STRING,
                    description="Province (2 letters)",
                    required=False,
                ),
                ToolParameter(
                    name="nazione",
                    type=ToolParameterType.STRING,
                    description="Country code",
                    required=False,
                ),
                ToolParameter(
                    name="codice_destinatario",
                    type=ToolParameterType.STRING,
                    description="SDI recipient code",
                    required=False,
                ),
                ToolParameter(
                    name="telefono",
                    type=ToolParameterType.STRING,
                    description="Phone number",
                    required=False,
                ),
                ToolParameter(
                    name="note",
                    type=ToolParameterType.STRING,
                    description="Notes",
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
            description="Delete client from database. CRITICAL: Cannot delete clients with invoices.",
            category="clients",
            parameters=[
                ToolParameter(
                    name="cliente_id",
                    type=ToolParameterType.INTEGER,
                    description="Client ID to delete",
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
