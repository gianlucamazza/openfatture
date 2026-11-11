"""Preventivo (quote/estimate) write use-cases (application layer)."""

from typing import Any

from pydantic import validate_call

from openfatture.billing.preventivi.service import PreventivoService
from openfatture.platform.config import get_settings
from openfatture.platform.errors import describe_error
from openfatture.platform.logging import get_logger
from openfatture.platform.security import validate_integer_input
from openfatture.storage.database.models import Preventivo, StatoPreventivo
from openfatture.storage.session import db_session

logger = get_logger(__name__)


@validate_call
def create_preventivo(
    cliente_id: int,
    righe: list[dict[str, Any]],
    validita_giorni: int = 30,
    note: str | None = None,
    condizioni: str | None = None,
) -> dict[str, Any]:
    """
    Create a new preventivo (quote/estimate).

    Args:
        cliente_id: Client ID
        righe: List of line items, each with keys:
               - descrizione (str, required)
               - quantita (float, required)
               - prezzo_unitario (float, required)
               - aliquota_iva (float, cedente default: 0% for forfettario, else 22%)
               - natura (str, required with a 0% rate; N2.2 by default for forfettario)
               - unita_misura (str, default "ore")
        validita_giorni: Validity period in days (default 30)
        note: Optional notes
        condizioni: Optional terms and conditions

    Returns:
        Dictionary with creation result
    """
    # Validate inputs
    cliente_id = validate_integer_input(cliente_id, min_value=1)
    validita_giorni = validate_integer_input(validita_giorni, min_value=1, max_value=365)

    if not righe or len(righe) == 0:
        return {
            "success": False,
            "error": "At least one line item (riga) is required",
        }

    # Validate righe structure
    for idx, riga in enumerate(righe):
        required_fields = ["descrizione", "quantita", "prezzo_unitario"]
        missing = [f for f in required_fields if f not in riga]
        if missing:
            return {
                "success": False,
                "error": f"Riga {idx + 1}: missing required fields: {missing}",
            }

    with db_session() as db:
        try:
            settings = get_settings()
            service = PreventivoService(settings=settings)

            preventivo, error = service.create_preventivo(
                db=db,
                cliente_id=cliente_id,
                righe=righe,
                validita_giorni=validita_giorni,
                note=note,
                condizioni=condizioni,
            )

            if error:
                return {"success": False, "error": error}

            # Mypy type narrowing: if no error, preventivo must not be None
            assert preventivo is not None

            logger.info(
                "preventivo_created",
                preventivo_id=preventivo.id,
                numero=f"{preventivo.numero}/{preventivo.anno}",
                cliente_id=cliente_id,
                totale=float(preventivo.totale),
            )

            return {
                "success": True,
                "preventivo_id": preventivo.id,
                "numero": f"{preventivo.numero}/{preventivo.anno}",
                "data_emissione": preventivo.data_emissione.isoformat(),
                "data_scadenza": preventivo.data_scadenza.isoformat(),
                "totale": float(preventivo.totale),
                "stato": preventivo.stato.value,
                "message": f"Preventivo {preventivo.numero}/{preventivo.anno} created successfully",
            }

        except Exception as e:
            logger.error("create_preventivo_failed", error=str(e))
            return {"success": False, "error": describe_error(e)}


@validate_call
def update_preventivo_status(
    preventivo_id: int,
    new_status: str,
) -> dict[str, Any]:
    """
    Update preventivo status.

    Args:
        preventivo_id: Preventivo ID
        new_status: New status (bozza, inviato, accettato, rifiutato, scaduto)

    Returns:
        Dictionary with update result
    """
    # Validate inputs
    preventivo_id = validate_integer_input(preventivo_id, min_value=1)

    # Validate status
    try:
        status_enum = StatoPreventivo(new_status.lower())
    except ValueError:
        return {
            "success": False,
            "error": f"Invalid status: {new_status}. Valid: bozza, inviato, accettato, rifiutato, scaduto",
        }

    with db_session() as db:
        try:
            settings = get_settings()
            service = PreventivoService(settings=settings)

            success, error = service.update_stato(
                db=db,
                preventivo_id=preventivo_id,
                nuovo_stato=status_enum,
            )

            if not success:
                return {"success": False, "error": error}

            logger.info(
                "preventivo_status_updated",
                preventivo_id=preventivo_id,
                new_status=new_status,
            )

            return {
                "success": True,
                "preventivo_id": preventivo_id,
                "new_status": new_status,
                "message": f"Preventivo {preventivo_id} status updated to {new_status}",
            }

        except Exception as e:
            logger.error("update_preventivo_status_failed", error=str(e))
            return {"success": False, "error": describe_error(e)}


@validate_call
def update_preventivo(
    preventivo_id: int,
    note: str | None = None,
    condizioni: str | None = None,
    validita_giorni: int | None = None,
) -> dict[str, Any]:
    """
    Update preventivo information (only BOZZA status).

    Args:
        preventivo_id: Preventivo ID
        note: Notes
        condizioni: Terms and conditions
        validita_giorni: Validity period in days (updates data_scadenza)

    Returns:
        Dictionary with update result
    """
    from datetime import timedelta

    # Validate inputs
    preventivo_id = validate_integer_input(preventivo_id, min_value=1)
    if validita_giorni is not None:
        validita_giorni = validate_integer_input(validita_giorni, min_value=1, max_value=365)

    with db_session() as db:
        try:
            preventivo = db.query(Preventivo).filter(Preventivo.id == preventivo_id).first()
            if not preventivo:
                return {"success": False, "error": f"Preventivo {preventivo_id} not found"}

            # Only BOZZA can be updated
            if preventivo.stato != StatoPreventivo.BOZZA:
                return {
                    "success": False,
                    "error": f"Cannot update preventivo in status '{preventivo.stato.value}'. Only BOZZA can be edited.",
                }

            # Track changes
            changes = []

            if note is not None and note != preventivo.note:
                preventivo.note = note
                changes.append("note")

            if condizioni is not None and condizioni != preventivo.condizioni:
                preventivo.condizioni = condizioni
                changes.append("condizioni")

            if validita_giorni is not None and validita_giorni != preventivo.validita_giorni:
                preventivo.validita_giorni = validita_giorni
                # Update data_scadenza based on new validity period
                preventivo.data_scadenza = preventivo.data_emissione + timedelta(
                    days=validita_giorni
                )
                changes.append("validita_giorni")
                changes.append("data_scadenza")

            if not changes:
                return {
                    "success": True,
                    "preventivo_id": preventivo_id,
                    "message": "No changes made (all fields same as current values)",
                }

            db.commit()
            db.refresh(preventivo)

            logger.info("preventivo_updated", preventivo_id=preventivo_id, changes=changes)

            return {
                "success": True,
                "preventivo_id": preventivo_id,
                "numero": f"{preventivo.numero}/{preventivo.anno}",
                "changes": changes,
                "data_scadenza": (
                    preventivo.data_scadenza.isoformat() if "data_scadenza" in changes else None
                ),
                "message": f"Preventivo updated successfully. Changed fields: {', '.join(changes)}",
            }

        except Exception as e:
            db.rollback()
            logger.error("update_preventivo_failed", preventivo_id=preventivo_id, error=str(e))
            return {"success": False, "error": describe_error(e)}


@validate_call
def delete_preventivo(
    preventivo_id: int,
) -> dict[str, Any]:
    """
    Delete preventivo from database.

    CRITICAL: This operation is irreversible. Only BOZZA status and non-converted preventivi can be deleted.

    Args:
        preventivo_id: Preventivo ID to delete

    Returns:
        Dictionary with deletion result
    """
    # Validate input
    preventivo_id = validate_integer_input(preventivo_id, min_value=1)

    with db_session() as db:
        try:
            # Get preventivo
            preventivo = db.query(Preventivo).filter(Preventivo.id == preventivo_id).first()
            if not preventivo:
                return {"success": False, "error": f"Preventivo {preventivo_id} not found"}

            # Only BOZZA can be deleted
            if preventivo.stato != StatoPreventivo.BOZZA:
                return {
                    "success": False,
                    "error": f"Cannot delete preventivo in status '{preventivo.stato.value}'. Only BOZZA can be deleted.",
                }

            # Check if already converted to invoice
            if preventivo.fattura is not None:
                return {
                    "success": False,
                    "error": f"Cannot delete preventivo that has been converted to invoice (fattura_id: {preventivo.fattura.id})",
                }

            # Store info for response
            numero = f"{preventivo.numero}/{preventivo.anno}"
            cliente_name = preventivo.cliente.denominazione if preventivo.cliente else "Unknown"

            # Delete preventivo (cascade will delete righe)
            db.delete(preventivo)
            db.commit()

            logger.warning(
                "preventivo_deleted",
                preventivo_id=preventivo_id,
                numero=numero,
                cliente_name=cliente_name,
            )

            return {
                "success": True,
                "preventivo_id": preventivo_id,
                "numero": numero,
                "message": f"Preventivo {numero} deleted successfully",
            }

        except Exception as e:
            db.rollback()
            logger.error("delete_preventivo_failed", preventivo_id=preventivo_id, error=str(e))
            return {"success": False, "error": describe_error(e)}


@validate_call
def convert_preventivo_to_invoice(
    preventivo_id: int,
) -> dict[str, Any]:
    """
    Convert a preventivo (quote) to a fattura (invoice).

    CRITICAL: This creates a new invoice and marks preventivo as converted.
    Cannot be undone.

    Args:
        preventivo_id: Preventivo ID to convert

    Returns:
        Dictionary with conversion result including new fattura_id
    """
    # Validate input
    preventivo_id = validate_integer_input(preventivo_id, min_value=1)

    with db_session() as db:
        try:
            settings = get_settings()
            service = PreventivoService(settings=settings)

            fattura, error = service.converti_a_fattura(
                db=db,
                preventivo_id=preventivo_id,
            )

            if error:
                return {"success": False, "error": error}

            # Mypy type narrowing: if no error, fattura must not be None
            assert fattura is not None

            logger.info(
                "preventivo_converted_to_invoice",
                preventivo_id=preventivo_id,
                fattura_id=fattura.id,
                numero_fattura=f"{fattura.numero}/{fattura.anno}",
            )

            return {
                "success": True,
                "preventivo_id": preventivo_id,
                "fattura_id": fattura.id,
                "fattura_numero": f"{fattura.numero}/{fattura.anno}",
                "totale": float(fattura.totale),
                "message": f"Preventivo {preventivo_id} converted to invoice {fattura.numero}/{fattura.anno}",
            }

        except Exception as e:
            logger.error("convert_preventivo_to_invoice_failed", error=str(e))
            return {"success": False, "error": describe_error(e)}
