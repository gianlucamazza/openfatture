"""Invoice line item (riga) write tools."""

from decimal import Decimal
from typing import Any

from pydantic import validate_call

from openfatture.storage.database.models import (
    Fattura,
    RigaFattura,
    StatoFattura,
)
from openfatture.utils.logging import get_logger
from openfatture.utils.security import validate_integer_input

from . import _db

logger = get_logger(__name__)


@validate_call
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

    db = _db.get_session()
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


@validate_call
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

    db = _db.get_session()
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


@validate_call
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

    db = _db.get_session()
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
