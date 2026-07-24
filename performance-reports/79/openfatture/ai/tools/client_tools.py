"""Tools for client operations."""

from typing import Any

from pydantic import validate_call
from sqlalchemy.orm import selectinload

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
from openfatture.storage.database.base import get_session
from openfatture.storage.database.models import Cliente, Fattura
from openfatture.utils.logging import get_logger
from openfatture.utils.security import sanitize_sql_like_input, validate_integer_input

logger = get_logger(__name__)


# =============================================================================
# Client Query Tools
# =============================================================================


@validate_call
def search_clients(
    query: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    # Sanitize and validate inputs
    if query is not None:
        query = sanitize_sql_like_input(query)

    limit = validate_integer_input(limit, min_value=1, max_value=100)
    """
    Search for clients.

    Args:
        query: Search in client name, P.IVA, or CF
        limit: Maximum results

    Returns:
        Dictionary with search results
    """
    db = get_session()
    try:
        # Build query
        db_query = db.query(Cliente)

        if query:
            query_lower = f"%{query.lower()}%"
            db_query = db_query.filter(
                (Cliente.denominazione.ilike(query_lower))
                | (Cliente.partita_iva.ilike(query_lower))
                | (Cliente.codice_fiscale.ilike(query_lower))
            )

        # Order by name
        db_query = db_query.order_by(Cliente.denominazione)

        # Get results
        clienti = db_query.limit(limit).all()

        # Format results
        results = []
        for c in clienti:
            results.append(
                {
                    "id": c.id,
                    "denominazione": c.denominazione,
                    "partita_iva": c.partita_iva or "",
                    "codice_fiscale": c.codice_fiscale or "",
                    "email": c.email or "",
                    "fatture_count": len(c.fatture),
                }
            )

        return {
            "count": len(results),
            "clienti": results,
            "has_more": len(clienti) == limit,
        }

    except Exception as e:
        logger.error("search_clients_failed", error=str(e))
        return {"error": str(e), "count": 0, "clienti": []}

    finally:
        db.close()


@validate_call
def get_client_details(cliente_id: int) -> dict[str, Any]:
    # Validate input
    cliente_id = validate_integer_input(cliente_id, min_value=1)
    """
    Get detailed information about a client.

    Args:
        cliente_id: Client ID

    Returns:
        Dictionary with client details
    """
    db = get_session()
    try:
        # Use selectinload to avoid N+1 queries when accessing fatture relationship
        cliente = (
            db.query(Cliente)
            .options(selectinload(Cliente.fatture))
            .filter(Cliente.id == cliente_id)
            .first()
        )

        if cliente is None:
            return {"error": f"Cliente {cliente_id} non trovato"}

        # Format details
        details = {
            "id": cliente.id,
            "denominazione": cliente.denominazione,
            "partita_iva": cliente.partita_iva or "",
            "codice_fiscale": cliente.codice_fiscale or "",
            "indirizzo": {
                "via": cliente.indirizzo or "",
                "cap": cliente.cap or "",
                "comune": cliente.comune or "",
                "provincia": cliente.provincia or "",
                "nazione": cliente.nazione or "IT",
            },
            "contatti": {
                "email": cliente.email or "",
                "pec": cliente.pec or "",
                "telefono": cliente.telefono or "",
            },
            "fatture_count": len(cliente.fatture),
        }

        # Add recent invoices
        fatture_recenti = (
            sorted(cliente.fatture, key=lambda f: f.data_emissione, reverse=True)[:5]
            if cliente.fatture
            else []
        )

        details["fatture_recenti"] = [
            {
                "id": f.id,
                "numero": f.numero,
                "anno": f.anno,
                "data": f.data_emissione.isoformat(),
                "importo": float(f.totale),
                "stato": f.stato.value,
            }
            for f in fatture_recenti
        ]

        return details

    except Exception as e:
        logger.error("get_client_details_failed", cliente_id=cliente_id, error=str(e))
        return {"error": str(e)}

    finally:
        db.close()


@validate_call
def get_client_stats() -> dict[str, Any]:
    """
    Get statistics about clients.

    Returns:
        Dictionary with client stats
    """
    db = get_session()
    try:
        stats = {
            "totale_clienti": db.query(Cliente).count(),
            "con_partita_iva": db.query(Cliente).filter(Cliente.partita_iva.isnot(None)).count(),
            "con_email": db.query(Cliente).filter(Cliente.email.isnot(None)).count(),
            "con_pec": db.query(Cliente).filter(Cliente.pec.isnot(None)).count(),
        }

        return stats

    except Exception as e:
        logger.error("get_client_stats_failed", error=str(e))
        return {"error": str(e)}

    finally:
        db.close()


# =============================================================================
# Client WRITE Tools
# =============================================================================


@validate_call
def create_client(
    denominazione: str,
    partita_iva: str | None = None,
    codice_fiscale: str | None = None,
    email: str | None = None,
    pec: str | None = None,
    indirizzo: str | None = None,
    cap: str | None = None,
    comune: str | None = None,
    provincia: str | None = None,
    nazione: str = "IT",
    codice_destinatario: str | None = None,
    telefono: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    """
    Create a new client.

    Args:
        denominazione: Client name/company name (required)
        partita_iva: VAT number (Partita IVA)
        codice_fiscale: Tax code (Codice Fiscale)
        email: Email address
        pec: PEC email address
        indirizzo: Street address
        cap: Postal code
        comune: City/Municipality
        provincia: Province (2 letters)
        nazione: Country code (default IT)
        codice_destinatario: SDI recipient code
        telefono: Phone number
        note: Notes

    Returns:
        Dictionary with client details or error
    """
    from openfatture.cli.lifespan import get_event_bus
    from openfatture.core.events import ClientCreatedEvent

    db = get_session()
    try:
        # Validate: at least one of partita_iva or codice_fiscale required
        if not partita_iva and not codice_fiscale:
            return {"error": "Either partita_iva or codice_fiscale is required"}

        # Check if client already exists
        existing = None
        if partita_iva:
            existing = db.query(Cliente).filter(Cliente.partita_iva == partita_iva).first()
        if not existing and codice_fiscale:
            existing = db.query(Cliente).filter(Cliente.codice_fiscale == codice_fiscale).first()

        if existing:
            return {
                "error": f"Client with this P.IVA/CF already exists (ID: {existing.id})",
                "existing_client_id": existing.id,
            }

        # Create client
        cliente = Cliente(
            denominazione=denominazione,
            partita_iva=partita_iva,
            codice_fiscale=codice_fiscale,
            email=email,
            pec=pec,
            indirizzo=indirizzo,
            cap=cap,
            comune=comune,
            provincia=provincia,
            nazione=nazione,
            codice_destinatario=codice_destinatario,
            telefono=telefono,
            note=note,
        )

        db.add(cliente)
        db.commit()
        db.refresh(cliente)

        # Publish event
        event_bus = get_event_bus()
        if event_bus:
            event_bus.publish(
                ClientCreatedEvent(
                    client_id=cliente.id,
                    client_name=cliente.denominazione,
                    partita_iva=cliente.partita_iva,
                )
            )

        logger.info("client_created", client_id=cliente.id, denominazione=denominazione)

        return {
            "success": True,
            "client_id": cliente.id,
            "denominazione": cliente.denominazione,
            "partita_iva": cliente.partita_iva or "",
            "codice_fiscale": cliente.codice_fiscale or "",
            "message": f"Client '{denominazione}' created successfully with ID {cliente.id}",
        }

    except Exception as e:
        db.rollback()
        logger.error("create_client_failed", error=str(e))
        return {"error": str(e)}
    finally:
        db.close()


@validate_call
def update_client(
    cliente_id: int,
    denominazione: str | None = None,
    partita_iva: str | None = None,
    codice_fiscale: str | None = None,
    email: str | None = None,
    pec: str | None = None,
    indirizzo: str | None = None,
    cap: str | None = None,
    comune: str | None = None,
    provincia: str | None = None,
    nazione: str | None = None,
    codice_destinatario: str | None = None,
    telefono: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    """
    Update client information.

    Args:
        cliente_id: Client ID (required)
        denominazione: Client name/company name
        partita_iva: VAT number
        codice_fiscale: Tax code
        email: Email address
        pec: PEC email
        indirizzo: Street address
        cap: Postal code
        comune: City
        provincia: Province (2 letters)
        nazione: Country code
        codice_destinatario: SDI recipient code
        telefono: Phone
        note: Notes

    Returns:
        Dictionary with result or error
    """
    from openfatture.cli.lifespan import get_event_bus
    from openfatture.core.events import ClientUpdatedEvent

    # Validate input
    cliente_id = validate_integer_input(cliente_id, min_value=1)

    db = get_session()
    try:
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not cliente:
            return {"error": f"Client {cliente_id} not found"}

        # Track changes
        changes = []

        # Update fields if provided
        if denominazione is not None and denominazione != cliente.denominazione:
            cliente.denominazione = denominazione
            changes.append("denominazione")

        if partita_iva is not None and partita_iva != cliente.partita_iva:
            cliente.partita_iva = partita_iva
            changes.append("partita_iva")

        if codice_fiscale is not None and codice_fiscale != cliente.codice_fiscale:
            cliente.codice_fiscale = codice_fiscale
            changes.append("codice_fiscale")

        if email is not None and email != cliente.email:
            cliente.email = email
            changes.append("email")

        if pec is not None and pec != cliente.pec:
            cliente.pec = pec
            changes.append("pec")

        if indirizzo is not None and indirizzo != cliente.indirizzo:
            cliente.indirizzo = indirizzo
            changes.append("indirizzo")

        if cap is not None and cap != cliente.cap:
            cliente.cap = cap
            changes.append("cap")

        if comune is not None and comune != cliente.comune:
            cliente.comune = comune
            changes.append("comune")

        if provincia is not None and provincia != cliente.provincia:
            cliente.provincia = provincia
            changes.append("provincia")

        if nazione is not None and nazione != cliente.nazione:
            cliente.nazione = nazione
            changes.append("nazione")

        if codice_destinatario is not None and codice_destinatario != cliente.codice_destinatario:
            cliente.codice_destinatario = codice_destinatario
            changes.append("codice_destinatario")

        if telefono is not None and telefono != cliente.telefono:
            cliente.telefono = telefono
            changes.append("telefono")

        if note is not None and note != cliente.note:
            cliente.note = note
            changes.append("note")

        if not changes:
            return {
                "success": True,
                "client_id": cliente_id,
                "message": "No changes made (all fields same as current values)",
            }

        db.commit()
        db.refresh(cliente)

        # Publish event
        event_bus = get_event_bus()
        if event_bus:
            event_bus.publish(
                ClientUpdatedEvent(
                    client_id=cliente.id,
                    client_name=cliente.denominazione,
                    updated_fields=changes,
                )
            )

        logger.info("client_updated", client_id=cliente_id, changes=changes)

        return {
            "success": True,
            "client_id": cliente_id,
            "denominazione": cliente.denominazione,
            "changes": changes,
            "message": f"Client updated successfully. Changed fields: {', '.join(changes)}",
        }

    except Exception as e:
        db.rollback()
        logger.error("update_client_failed", cliente_id=cliente_id, error=str(e))
        return {"error": str(e)}
    finally:
        db.close()


@validate_call
def delete_client(
    cliente_id: int,
) -> dict[str, Any]:
    """
    Delete client from database.

    CRITICAL: This operation is irreversible. Clients with associated invoices cannot be deleted.

    Args:
        cliente_id: Client ID to delete

    Returns:
        Dictionary with deletion result
    """
    from openfatture.cli.lifespan import get_event_bus
    from openfatture.core.events import ClientDeletedEvent

    # Validate input
    cliente_id = validate_integer_input(cliente_id, min_value=1)

    db = get_session()
    try:
        # Get client
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not cliente:
            return {"error": f"Client {cliente_id} not found"}

        # Check if client has invoices
        fatture_count = db.query(Fattura).filter(Fattura.cliente_id == cliente_id).count()

        if fatture_count > 0:
            return {
                "error": f"Cannot delete client with {fatture_count} invoices. Delete invoices first or archive the client instead.",
                "fatture_count": fatture_count,
                "success": False,
            }

        # Store info for response
        denominazione = cliente.denominazione
        partita_iva = cliente.partita_iva

        # Delete client
        db.delete(cliente)
        db.commit()

        # Publish event
        event_bus = get_event_bus()
        if event_bus:
            event_bus.publish(
                ClientDeletedEvent(
                    client_id=cliente_id,
                    client_name=denominazione,
                )
            )

        logger.warning(
            "client_deleted",
            cliente_id=cliente_id,
            denominazione=denominazione,
            partita_iva=partita_iva,
        )

        return {
            "success": True,
            "client_id": cliente_id,
            "denominazione": denominazione,
            "message": f"Client '{denominazione}' (ID: {cliente_id}) deleted successfully",
        }

    except Exception as e:
        db.rollback()
        logger.error("delete_client_failed", cliente_id=cliente_id, error=str(e))
        return {"error": str(e), "success": False}
    finally:
        db.close()


# =============================================================================
# Tool Definitions
# =============================================================================


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
