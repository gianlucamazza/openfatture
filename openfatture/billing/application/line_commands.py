"""Invoice line (riga) write use-cases (application layer)."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from openfatture.billing.application.totals import recompute_invoice, resolve_vat
from openfatture.platform.config import get_settings
from openfatture.platform.errors import describe_error
from openfatture.platform.logging import get_logger
from openfatture.platform.security import validate_integer_input
from openfatture.storage.database.models import Fattura, RigaFattura, StatoFattura
from openfatture.storage.session import db_session

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = get_logger(__name__)


def create_riga(
    fattura_id: int,
    descrizione: str,
    quantita: float,
    prezzo_unitario: float,
    aliquota_iva: float | None = None,
    unita_misura: str = "ore",
    natura: str | None = None,
) -> dict[str, Any]:
    """
    Add line item to invoice.

    Args:
        fattura_id: Invoice ID
        descrizione: Item description
        quantita: Quantity
        prezzo_unitario: Unit price (€)
        aliquota_iva: VAT rate (%); default 0% (N2.2) for the forfettario
            regime, 22% otherwise
        unita_misura: Unit of measure - default "ore"
        natura: VAT natura, required with a 0% rate (N2.2 by default for
            the forfettario regime, N1 for the re-charged stamp duty)

    Returns:
        Dictionary with result or error
    """
    # Validate inputs
    fattura_id = validate_integer_input(fattura_id, min_value=1)
    try:
        aliquota_dec, natura = resolve_vat(
            aliquota_iva, natura, get_settings().cedente_regime_fiscale
        )
    except ValueError as e:
        return {"error": str(e)}

    with db_session() as db:
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

            # Create riga (amounts set by recompute_invoice)
            riga = RigaFattura(
                fattura_id=fattura_id,
                numero_riga=numero_riga,
                descrizione=descrizione,
                quantita=quantita_dec,
                prezzo_unitario=prezzo_dec,
                aliquota_iva=aliquota_dec,
                natura=natura,
                unita_misura=unita_misura,
                imponibile=Decimal("0"),
                iva=Decimal("0"),
                totale=Decimal("0"),
            )

            db.add(riga)
            fattura.righe.append(riga)
            recompute_invoice(fattura)
            imponibile, iva, totale = riga.imponibile, riga.iva, riga.totale

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
            return {"error": describe_error(e)}


def update_riga(
    riga_id: int,
    descrizione: str | None = None,
    quantita: float | None = None,
    prezzo_unitario: float | None = None,
    aliquota_iva: float | None = None,
    unita_misura: str | None = None,
    natura: str | None = None,
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
        natura: VAT natura (required with a 0% rate)

    Returns:
        Dictionary with result or error
    """
    # Validate input
    riga_id = validate_integer_input(riga_id, min_value=1)

    with db_session() as db:
        try:
            loaded = _load_editable_line(db, riga_id)
            if isinstance(loaded, str):
                return {"error": loaded}
            riga, fattura = loaded

            changes = _apply_line_fields(riga, descrizione, quantita, prezzo_unitario)
            vat_changes = _apply_line_vat(riga, aliquota_iva, natura)
            if isinstance(vat_changes, str):
                return {"error": vat_changes}
            changes += vat_changes
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
            if not _PRICE_FIELDS.isdisjoint(changes):
                recompute_invoice(fattura)

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
            return _updated_line_result(riga, fattura, changes)

        except Exception as e:
            db.rollback()
            logger.error("update_riga_failed", riga_id=riga_id, error=str(e))
            return {"error": describe_error(e)}


_PRICE_FIELDS = frozenset({"quantita", "prezzo_unitario", "aliquota_iva", "natura"})


def _load_editable_line(db: Session, riga_id: int) -> tuple[RigaFattura, Fattura] | str:
    """The line and its invoice when the invoice is still editable, else an error."""
    riga = db.query(RigaFattura).filter(RigaFattura.id == riga_id).first()
    if not riga:
        return f"Line item {riga_id} not found"
    fattura = db.query(Fattura).filter(Fattura.id == riga.fattura_id).first()
    if not fattura:
        return f"Invoice for line item {riga_id} not found"
    if fattura.stato not in [StatoFattura.BOZZA, StatoFattura.DA_INVIARE]:
        return f"Cannot modify line item in invoice with status '{fattura.stato.value}'. Only BOZZA or DA_INVIARE can be edited."
    return riga, fattura


def _apply_line_fields(
    riga: RigaFattura,
    descrizione: str | None,
    quantita: float | None,
    prezzo_unitario: float | None,
) -> list[str]:
    """Set description, quantity and price when they differ; return what changed."""
    changes = []
    if descrizione is not None and descrizione != riga.descrizione:
        riga.descrizione = descrizione
        changes.append("descrizione")
    if quantita is not None and Decimal(str(quantita)) != riga.quantita:
        riga.quantita = Decimal(str(quantita))
        changes.append("quantita")
    if prezzo_unitario is not None and Decimal(str(prezzo_unitario)) != riga.prezzo_unitario:
        riga.prezzo_unitario = Decimal(str(prezzo_unitario))
        changes.append("prezzo_unitario")
    return changes


def _apply_line_vat(
    riga: RigaFattura, aliquota_iva: float | None, natura: str | None
) -> list[str] | str:
    """Set rate and natura when requested; return what changed or the VAT error."""
    if aliquota_iva is None and natura is None:
        return []
    new_rate = riga.aliquota_iva if aliquota_iva is None else aliquota_iva
    new_natura = natura
    if new_natura is None and aliquota_iva is not None and Decimal(str(aliquota_iva)) == 0:
        new_natura = riga.natura
    try:
        rate, resolved = resolve_vat(new_rate, new_natura, get_settings().cedente_regime_fiscale)
    except ValueError as e:
        return str(e)
    changes = []
    if rate != riga.aliquota_iva:
        riga.aliquota_iva = rate
        changes.append("aliquota_iva")
    if resolved != riga.natura:
        riga.natura = resolved
        changes.append("natura")
    return changes


def _updated_line_result(riga: RigaFattura, fattura: Fattura, changes: list[str]) -> dict[str, Any]:
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

    with db_session() as db:
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
            fattura.righe.remove(riga)
            recompute_invoice(fattura)

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
            return {"error": describe_error(e)}
