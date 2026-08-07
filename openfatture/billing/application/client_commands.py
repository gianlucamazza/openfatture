"""Client write use-cases (application layer)."""

from __future__ import annotations

from typing import Any

from openfatture.platform.logging import get_logger
from openfatture.platform.security import validate_integer_input
from openfatture.storage.database.base import get_session
from openfatture.storage.database.models import Cliente, Fattura

logger = get_logger(__name__)


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
    from openfatture.events import ClientCreatedEvent

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
    from openfatture.events import ClientUpdatedEvent

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
    from openfatture.events import ClientDeletedEvent

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
