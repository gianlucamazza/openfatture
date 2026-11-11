"""Invoice write use-cases (application layer)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from openfatture.billing.application.numbering import next_numero
from openfatture.platform.errors import describe_error
from openfatture.platform.logging import get_logger
from openfatture.platform.security import validate_integer_input
from openfatture.storage.database.models import (
    Cliente,
    Fattura,
    RigaFattura,
    StatoFattura,
    TipoDocumento,
)
from openfatture.storage.session import db_session

logger = get_logger(__name__)


def create_invoice(
    cliente_id: int,
    anno: int | None = None,
    numero: str | None = None,
    data_emissione: str | None = None,
    tipo_documento: str = "TD01",
    note: str | None = None,
) -> dict[str, Any]:
    """
    Create a new invoice.

    Args:
        cliente_id: Client ID
        anno: Year (current year if None)
        numero: Invoice number (auto-generated if None)
        data_emissione: Issue date YYYY-MM-DD (today if None)
        tipo_documento: Document type (default TD01 - Fattura)
        note: Optional notes

    Returns:
        Dictionary with invoice details or error
    """
    from datetime import datetime

    from openfatture.events import InvoiceCreatedEvent, get_global_event_bus

    # Validate inputs
    cliente_id = validate_integer_input(cliente_id, min_value=1)
    if anno is not None:
        anno = validate_integer_input(anno, min_value=2000, max_value=2100)

    with db_session() as db:
        try:
            # Check client exists
            cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
            if not cliente:
                return {"error": f"Cliente {cliente_id} non trovato"}

            # Set defaults
            if anno is None:
                anno = datetime.now().year

            if numero is None:
                numero = next_numero(db, Fattura, anno)
            elif (
                db.query(Fattura.id).filter(Fattura.numero == numero, Fattura.anno == anno).first()
            ):
                return {
                    "error": f"Invoice number {numero}/{anno} is already used; "
                    f"omit the number to use the next one ({next_numero(db, Fattura, anno)})"
                }

            if data_emissione is None:
                data_emissione_date = datetime.now().date()
            else:
                try:
                    data_emissione_date = datetime.fromisoformat(data_emissione).date()
                except ValueError:
                    return {"error": f"Invalid date format: {data_emissione}. Use YYYY-MM-DD"}

            # Validate tipo_documento
            try:
                tipo_doc_enum = TipoDocumento(tipo_documento)
            except ValueError:
                return {"error": f"Invalid tipo_documento: {tipo_documento}"}

            # Create invoice
            fattura = Fattura(
                numero=numero,
                anno=anno,
                data_emissione=data_emissione_date,
                cliente_id=cliente_id,
                tipo_documento=tipo_doc_enum,
                stato=StatoFattura.BOZZA,
                note=note,
                imponibile=Decimal("0"),
                iva=Decimal("0"),
                totale=Decimal("0"),
            )

            db.add(fattura)
            db.commit()
            db.refresh(fattura)

            # Publish event
            event_bus = get_global_event_bus()
            if event_bus:
                event_bus.publish(
                    InvoiceCreatedEvent(
                        invoice_id=fattura.id,
                        invoice_number=f"{fattura.numero}/{fattura.anno}",
                        client_id=fattura.cliente_id,
                        client_name=cliente.denominazione,
                        total_amount=fattura.totale,
                    )
                )

            logger.info("invoice_created", invoice_id=fattura.id, numero=numero, anno=anno)

            return {
                "success": True,
                "invoice_id": fattura.id,
                "numero": fattura.numero,
                "anno": fattura.anno,
                "cliente": cliente.denominazione,
                "stato": fattura.stato.value,
                "message": f"Invoice {numero}/{anno} created successfully. Add line items with create_riga.",
            }

        except Exception as e:
            db.rollback()
            logger.error("create_invoice_failed", error=str(e))
            return {"error": describe_error(e)}


def update_invoice(
    fattura_id: int,
    data_emissione: str | None = None,
    tipo_documento: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    """
    Update invoice information (only BOZZA status).

    Args:
        fattura_id: Invoice ID to update
        data_emissione: New issue date YYYY-MM-DD (optional)
        tipo_documento: New document type (optional)
        note: New notes (optional)

    Returns:
        Dictionary with update result
    """
    from datetime import datetime

    # Validate input
    fattura_id = validate_integer_input(fattura_id, min_value=1)

    with db_session() as db:
        try:
            # Get invoice
            fattura = db.query(Fattura).filter(Fattura.id == fattura_id).first()
            if not fattura:
                return {"error": f"Invoice {fattura_id} not found"}

            # Only BOZZA invoices can be updated
            if fattura.stato != StatoFattura.BOZZA:
                return {
                    "error": f"Cannot update invoice in status '{fattura.stato.value}'. Only BOZZA invoices can be modified."
                }

            # Track changes
            changes = []

            # Update data_emissione if provided
            if data_emissione is not None:
                try:
                    data_emissione_date = datetime.fromisoformat(data_emissione).date()
                    fattura.data_emissione = data_emissione_date
                    changes.append("data_emissione")
                except ValueError:
                    return {"error": f"Invalid date format: {data_emissione}. Use YYYY-MM-DD"}

            # Update tipo_documento if provided
            if tipo_documento is not None:
                try:
                    tipo_doc_enum = TipoDocumento(tipo_documento)
                    fattura.tipo_documento = tipo_doc_enum
                    changes.append("tipo_documento")
                except ValueError:
                    return {"error": f"Invalid tipo_documento: {tipo_documento}"}

            # Update note if provided
            if note is not None:
                fattura.note = note
                changes.append("note")

            if not changes:
                return {"error": "No fields to update (all parameters are None)"}

            db.commit()
            db.refresh(fattura)

            logger.info(
                "invoice_updated",
                fattura_id=fattura_id,
                numero=f"{fattura.numero}/{fattura.anno}",
                changes=changes,
            )

            return {
                "success": True,
                "invoice_id": fattura.id,
                "numero": f"{fattura.numero}/{fattura.anno}",
                "changes": changes,
                "message": f"Invoice {fattura.numero}/{fattura.anno} updated ({len(changes)} fields)",
            }

        except Exception as e:
            db.rollback()
            logger.error("update_invoice_failed", fattura_id=fattura_id, error=str(e))
            return {"error": describe_error(e)}


def delete_invoice(
    fattura_id: int,
    force: bool = False,
) -> dict[str, Any]:
    """
    Delete invoice from database (only BOZZA status).

    CRITICAL: This operation is irreversible. Use with caution.

    Args:
        fattura_id: Invoice ID to delete
        force: Force deletion even if invoice has line items (default False)

    Returns:
        Dictionary with deletion result
    """
    # Validate input
    fattura_id = validate_integer_input(fattura_id, min_value=1)

    with db_session() as db:
        try:
            # Get invoice
            fattura = db.query(Fattura).filter(Fattura.id == fattura_id).first()
            if not fattura:
                return {"error": f"Invoice {fattura_id} not found"}

            # Only BOZZA invoices can be deleted
            if fattura.stato != StatoFattura.BOZZA:
                return {
                    "error": f"Cannot delete invoice in status '{fattura.stato.value}'. Only BOZZA invoices can be deleted."
                }

            # Check if invoice has line items
            righe_count = db.query(RigaFattura).filter(RigaFattura.fattura_id == fattura_id).count()

            if righe_count > 0 and not force:
                return {
                    "error": f"Invoice has {righe_count} line items. Use force=True to delete anyway.",
                    "righe_count": righe_count,
                }

            # Store info for response
            numero = fattura.numero
            anno = fattura.anno
            cliente_nome = fattura.cliente.denominazione if fattura.cliente else "Unknown"

            # Delete line items first (cascade should handle this, but explicit is safer)
            if righe_count > 0 and force:
                db.query(RigaFattura).filter(RigaFattura.fattura_id == fattura_id).delete()

            # Delete invoice
            db.delete(fattura)
            db.commit()

            logger.warning(
                "invoice_deleted",
                fattura_id=fattura_id,
                numero=f"{numero}/{anno}",
                righe_count=righe_count,
                forced=force,
            )

            return {
                "success": True,
                "invoice_id": fattura_id,
                "numero": f"{numero}/{anno}",
                "cliente": cliente_nome,
                "righe_deleted": righe_count,
                "message": f"Invoice {numero}/{anno} deleted"
                + (f" ({righe_count} line items removed)" if righe_count > 0 else ""),
            }

        except Exception as e:
            db.rollback()
            logger.error("delete_invoice_failed", fattura_id=fattura_id, error=str(e))
            return {"error": describe_error(e)}


def update_invoice_status(
    fattura_id: int,
    new_status: str,
) -> dict[str, Any]:
    """
    Update invoice status (workflow: BOZZA DA_INVIARE).

    Args:
        fattura_id: Invoice ID
        new_status: New status (bozza, da_inviare)

    Returns:
        Dictionary with status update result
    """
    # Validate input
    fattura_id = validate_integer_input(fattura_id, min_value=1)

    with db_session() as db:
        try:
            # Get invoice
            fattura = db.query(Fattura).filter(Fattura.id == fattura_id).first()
            if not fattura:
                return {"error": f"Invoice {fattura_id} not found"}

            # Validate new status
            try:
                new_status_enum = StatoFattura(new_status)
            except ValueError:
                valid_statuses = [s.value for s in StatoFattura]
                return {
                    "error": f"Invalid status: {new_status}. Valid values: {', '.join(valid_statuses)}"
                }

            from openfatture.billing.application.invoice_status import (
                change_status,
                validate_manual_transition,
            )

            validate_manual_transition(fattura, new_status_enum)
            if fattura.stato == new_status_enum:
                return {
                    "success": True,
                    "invoice_id": fattura.id,
                    "old_status": fattura.stato.value,
                    "new_status": new_status_enum.value,
                    "message": "Status unchanged",
                }

            # Update status
            old_status = fattura.stato.value
            change_status(db, fattura, new_status_enum)
            db.commit()
            db.refresh(fattura)

            logger.info(
                "invoice_status_updated",
                fattura_id=fattura_id,
                numero=f"{fattura.numero}/{fattura.anno}",
                old_status=old_status,
                new_status=new_status_enum.value,
            )

            return {
                "success": True,
                "invoice_id": fattura.id,
                "numero": f"{fattura.numero}/{fattura.anno}",
                "old_status": old_status,
                "new_status": new_status_enum.value,
                "message": f"Invoice {fattura.numero}/{fattura.anno} status changed: {old_status} {new_status_enum.value}",
            }

        except Exception as e:
            db.rollback()
            logger.error("update_invoice_status_failed", fattura_id=fattura_id, error=str(e))
            return {
                "error": describe_error(e),
                "error_code": "state_conflict"
                if type(e).__name__ == "InvoiceStateConflict"
                else "invalid_transition",
            }
