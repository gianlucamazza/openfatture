"""Invoice write use-cases (application layer)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from openfatture.platform.logging import get_logger
from openfatture.platform.security import validate_integer_input
from openfatture.storage.database.base import get_session
from openfatture.storage.database.models import (
    Cliente,
    Fattura,
    RigaFattura,
    StatoFattura,
    TipoDocumento,
)

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

    from openfatture.cli.lifespan import get_event_bus
    from openfatture.events import InvoiceCreatedEvent

    # Validate inputs
    cliente_id = validate_integer_input(cliente_id, min_value=1)
    if anno is not None:
        anno = validate_integer_input(anno, min_value=2000, max_value=2100)

    db = get_session()
    try:
        # Check client exists
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not cliente:
            return {"error": f"Cliente {cliente_id} non trovato"}

        # Set defaults
        if anno is None:
            anno = datetime.now().year

        if numero is None:
            # Auto-generate numero
            ultimo = (
                db.query(Fattura)
                .filter(Fattura.anno == anno)
                .order_by(Fattura.numero.desc())
                .first()
            )
            if ultimo:
                try:
                    numero = str(int(ultimo.numero) + 1)
                except ValueError:
                    numero = "1"
            else:
                numero = "1"

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
        event_bus = get_event_bus()
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
        return {"error": str(e)}
    finally:
        db.close()


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

    db = get_session()
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
        return {"error": str(e)}
    finally:
        db.close()


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

    db = get_session()
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
        return {"error": str(e)}
    finally:
        db.close()


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

    db = get_session()
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

        # Check valid state transitions
        current_status = fattura.stato

        # Define allowed transitions
        allowed_transitions = {
            StatoFattura.BOZZA: [StatoFattura.DA_INVIARE, StatoFattura.BOZZA],
            StatoFattura.DA_INVIARE: [StatoFattura.BOZZA, StatoFattura.DA_INVIARE],
            # Other statuses cannot be changed manually (managed by SDI notifications)
        }

        if current_status not in allowed_transitions:
            return {
                "error": f"Invoice in status '{current_status.value}' cannot have status changed manually. Status is managed by SDI notifications."
            }

        if new_status_enum not in allowed_transitions[current_status]:
            return {
                "error": f"Invalid transition from '{current_status.value}' to '{new_status_enum.value}'. "
                f"Allowed: {', '.join([s.value for s in allowed_transitions[current_status]])}"
            }

        # If moving to DA_INVIARE, verify invoice is complete
        if new_status_enum == StatoFattura.DA_INVIARE:
            if not fattura.righe:
                return {
                    "error": "Cannot mark invoice as DA_INVIARE: no line items. Add at least one riga first."
                }

            if not fattura.cliente:
                return {"error": "Cannot mark invoice as DA_INVIARE: no client associated."}

        # Update status
        old_status = current_status.value
        fattura.stato = new_status_enum
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
        return {"error": str(e)}
    finally:
        db.close()


def create_riga(
    fattura_id: int,
    descrizione: str,
    quantita: float,
    prezzo_unitario: float,
    aliquota_iva: float = 22.0,
    unita_misura: str = "ore",
) -> dict[str, Any]:
    """
    Add line item to invoice.

    Args:
        fattura_id: Invoice ID
        descrizione: Item description
        quantita: Quantity
        prezzo_unitario: Unit price (€)
        aliquota_iva: VAT rate (%) - default 22%
        unita_misura: Unit of measure - default "ore"

    Returns:
        Dictionary with result or error
    """
    # Validate inputs
    fattura_id = validate_integer_input(fattura_id, min_value=1)

    db = get_session()
    try:
        # Check invoice exists and is editable
        fattura = db.query(Fattura).filter(Fattura.id == fattura_id).first()
        if not fattura:
            return {"error": f"Invoice {fattura_id} not found"}

        if fattura.stato not in [StatoFattura.BOZZA, StatoFattura.DA_INVIARE]:
            return {
                "error": f"Cannot modify invoice in status '{fattura.stato.value}'. Only BOZZA or DA_INVIARE can be edited."
            }

        # Get next riga number
        max_riga = (
            db.query(RigaFattura)
            .filter(RigaFattura.fattura_id == fattura_id)
            .order_by(RigaFattura.numero_riga.desc())
            .first()
        )
        numero_riga = (max_riga.numero_riga + 1) if max_riga else 1

        # Calculate totals
        quantita_dec = Decimal(str(quantita))
        prezzo_dec = Decimal(str(prezzo_unitario))
        aliquota_dec = Decimal(str(aliquota_iva))

        imponibile = quantita_dec * prezzo_dec
        iva = imponibile * aliquota_dec / Decimal("100")
        totale = imponibile + iva

        # Create riga
        riga = RigaFattura(
            fattura_id=fattura_id,
            numero_riga=numero_riga,
            descrizione=descrizione,
            quantita=quantita_dec,
            prezzo_unitario=prezzo_dec,
            aliquota_iva=aliquota_dec,
            unita_misura=unita_misura,
            imponibile=imponibile,
            iva=iva,
            totale=totale,
        )

        db.add(riga)

        # Update invoice totals
        fattura.imponibile += imponibile
        fattura.iva += iva
        fattura.totale += totale

        db.commit()
        db.refresh(riga)

        logger.info(
            "riga_created",
            fattura_id=fattura_id,
            riga_id=riga.id,
            numero_riga=numero_riga,
        )

        return {
            "success": True,
            "riga_id": riga.id,
            "numero_riga": numero_riga,
            "descrizione": descrizione,
            "imponibile": float(imponibile),
            "iva": float(iva),
            "totale": float(totale),
            "invoice_totale": float(fattura.totale),
            "message": f"Line item #{numero_riga} added. Invoice total: €{fattura.totale:.2f}",
        }

    except Exception as e:
        db.rollback()
        logger.error("create_riga_failed", error=str(e))
        return {"error": str(e)}
    finally:
        db.close()


def update_riga(
    riga_id: int,
    descrizione: str | None = None,
    quantita: float | None = None,
    prezzo_unitario: float | None = None,
    aliquota_iva: float | None = None,
    unita_misura: str | None = None,
) -> dict[str, Any]:
    """
    Update line item in invoice.

    Args:
        riga_id: Line item ID
        descrizione: Item description
        quantita: Quantity
        prezzo_unitario: Unit price (€)
        aliquota_iva: VAT rate (%)
        unita_misura: Unit of measure

    Returns:
        Dictionary with result or error
    """
    # Validate input
    riga_id = validate_integer_input(riga_id, min_value=1)

    db = get_session()
    try:
        # Get riga
        riga = db.query(RigaFattura).filter(RigaFattura.id == riga_id).first()
        if not riga:
            return {"error": f"Line item {riga_id} not found"}

        # Get invoice
        fattura = db.query(Fattura).filter(Fattura.id == riga.fattura_id).first()
        if not fattura:
            return {"error": f"Invoice for line item {riga_id} not found"}

        # Check invoice is editable
        if fattura.stato not in [StatoFattura.BOZZA, StatoFattura.DA_INVIARE]:
            return {
                "error": f"Cannot modify line item in invoice with status '{fattura.stato.value}'. Only BOZZA or DA_INVIARE can be edited."
            }

        # Store old totals to subtract from invoice
        old_imponibile = riga.imponibile
        old_iva = riga.iva
        old_totale = riga.totale

        # Track changes
        changes = []

        # Update fields if provided
        if descrizione is not None and descrizione != riga.descrizione:
            riga.descrizione = descrizione
            changes.append("descrizione")

        if quantita is not None and Decimal(str(quantita)) != riga.quantita:
            riga.quantita = Decimal(str(quantita))
            changes.append("quantita")

        if prezzo_unitario is not None and Decimal(str(prezzo_unitario)) != riga.prezzo_unitario:
            riga.prezzo_unitario = Decimal(str(prezzo_unitario))
            changes.append("prezzo_unitario")

        if aliquota_iva is not None and Decimal(str(aliquota_iva)) != riga.aliquota_iva:
            riga.aliquota_iva = Decimal(str(aliquota_iva))
            changes.append("aliquota_iva")

        if unita_misura is not None and unita_misura != riga.unita_misura:
            riga.unita_misura = unita_misura
            changes.append("unita_misura")

        if not changes:
            return {
                "success": True,
                "riga_id": riga_id,
                "message": "No changes made (all fields same as current values)",
            }

        # Recalculate totals if numeric fields changed
        if any(f in changes for f in ["quantita", "prezzo_unitario", "aliquota_iva"]):
            riga.imponibile = riga.quantita * riga.prezzo_unitario
            riga.iva = riga.imponibile * riga.aliquota_iva / Decimal("100")
            riga.totale = riga.imponibile + riga.iva

            # Update invoice totals (subtract old, add new)
            fattura.imponibile = fattura.imponibile - old_imponibile + riga.imponibile
            fattura.iva = fattura.iva - old_iva + riga.iva
            fattura.totale = fattura.totale - old_totale + riga.totale

        db.commit()
        db.refresh(riga)
        db.refresh(fattura)

        logger.info(
            "riga_updated",
            riga_id=riga_id,
            fattura_id=fattura.id,
            numero_riga=riga.numero_riga,
            changes=changes,
        )

        return {
            "success": True,
            "riga_id": riga.id,
            "numero_riga": riga.numero_riga,
            "descrizione": riga.descrizione,
            "changes": changes,
            "imponibile": float(riga.imponibile),
            "iva": float(riga.iva),
            "totale": float(riga.totale),
            "invoice_totale": float(fattura.totale),
            "message": f"Line item #{riga.numero_riga} updated. Invoice total: €{fattura.totale:.2f}",
        }

    except Exception as e:
        db.rollback()
        logger.error("update_riga_failed", riga_id=riga_id, error=str(e))
        return {"error": str(e)}
    finally:
        db.close()


def delete_riga(
    riga_id: int,
) -> dict[str, Any]:
    """
    Delete line item from invoice.

    CRITICAL: This operation is irreversible. Updates invoice totals automatically.

    Args:
        riga_id: Line item ID to delete

    Returns:
        Dictionary with deletion result
    """
    # Validate input
    riga_id = validate_integer_input(riga_id, min_value=1)

    db = get_session()
    try:
        # Get riga
        riga = db.query(RigaFattura).filter(RigaFattura.id == riga_id).first()
        if not riga:
            return {"error": f"Line item {riga_id} not found"}

        # Get invoice
        fattura = db.query(Fattura).filter(Fattura.id == riga.fattura_id).first()
        if not fattura:
            return {"error": f"Invoice for line item {riga_id} not found"}

        # Check invoice is editable
        if fattura.stato not in [StatoFattura.BOZZA, StatoFattura.DA_INVIARE]:
            return {
                "error": f"Cannot delete line item in invoice with status '{fattura.stato.value}'. Only BOZZA or DA_INVIARE can be edited."
            }

        # Store info for response
        numero_riga = riga.numero_riga
        descrizione = riga.descrizione
        riga_totale = riga.totale

        # Update invoice totals (subtract this riga)
        fattura.imponibile -= riga.imponibile
        fattura.iva -= riga.iva
        fattura.totale -= riga.totale

        # Delete riga
        db.delete(riga)
        db.commit()
        db.refresh(fattura)

        logger.warning(
            "riga_deleted",
            riga_id=riga_id,
            fattura_id=fattura.id,
            numero_riga=numero_riga,
            descrizione=descrizione,
        )

        return {
            "success": True,
            "riga_id": riga_id,
            "numero_riga": numero_riga,
            "descrizione": descrizione,
            "riga_totale": float(riga_totale),
            "invoice_totale": float(fattura.totale),
            "message": f"Line item #{numero_riga} deleted. Invoice total: €{fattura.totale:.2f}",
        }

    except Exception as e:
        db.rollback()
        logger.error("delete_riga_failed", riga_id=riga_id, error=str(e))
        return {"error": str(e)}
    finally:
        db.close()
