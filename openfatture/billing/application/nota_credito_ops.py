"""Nota di credito (credit note) operations — application layer."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from openfatture.platform.logging import get_logger
from openfatture.platform.security import validate_integer_input
from openfatture.storage.database.base import get_session
from openfatture.storage.database.models import (
    Fattura,
    RigaFattura,
    StatoFattura,
    TipoDocumento,
)

logger = get_logger(__name__)


def create_nota_credito_from_fattura(
    fattura_id: int,
    note: str | None = None,
    full_refund: bool = True,
    line_items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Create a nota di credito (TD04) from an existing invoice.

    This implements a real credit note workflow with FatturaPA linkage:
    - Loads source invoice (must exist)
    - Creates new invoice with TipoDocumento.TD04
    - Copies cliente from source invoice
    - Copies line items with positive amounts (TD04 standard practice)
    - Sets FatturaPA DatiFattureCollegate linkage
    - Leaves status BOZZA; does not auto-send to SDI

    Args:
        fattura_id: Source invoice ID to create credit note from
        note: Optional notes for the credit note
        full_refund: If True, copies all lines from source; if False, use line_items
        line_items: List of dicts with {numero_riga, quantita} to specify partial refund
                    (only used when full_refund=False)

    Returns:
        Dictionary with nota di credito details or error

    Example full refund:
        create_nota_credito_from_fattura(fattura_id=123, note="Storno completo")

    Example partial refund:
        create_nota_credito_from_fattura(
            fattura_id=123,
            full_refund=False,
            line_items=[{"numero_riga": 1, "quantita": 2.0}],
            note="Storno parziale"
        )
    """
    from datetime import datetime

    from openfatture.cli.lifespan import get_event_bus
    from openfatture.events import InvoiceCreatedEvent

    # Validate input
    fattura_id = validate_integer_input(fattura_id, min_value=1)

    db = get_session()
    try:
        # Load source invoice
        source_fattura = db.query(Fattura).filter(Fattura.id == fattura_id).first()
        if not source_fattura:
            return {"error": f"Source invoice {fattura_id} not found"}

        # Source invoice must have lines
        if not source_fattura.righe:
            return {"error": f"Source invoice {fattura_id} has no line items to refund"}

        # Generate numero for nota di credito (next available in current year)
        anno = datetime.now().year
        ultimo = (
            db.query(Fattura).filter(Fattura.anno == anno).order_by(Fattura.numero.desc()).first()
        )
        if ultimo:
            try:
                numero = str(int(ultimo.numero) + 1)
            except ValueError:
                numero = "1"
        else:
            numero = "1"

        # Create nota di credito (TD04)
        nota_credito = Fattura(
            numero=numero,
            anno=anno,
            data_emissione=datetime.now().date(),
            cliente_id=source_fattura.cliente_id,
            tipo_documento=TipoDocumento.TD04,
            stato=StatoFattura.BOZZA,
            note=note,
            # Link to source invoice (DatiFattureCollegate)
            fattura_collegata_id=source_fattura.id,
            fattura_collegata_numero=f"{source_fattura.numero}/{source_fattura.anno}",
            fattura_collegata_data=source_fattura.data_emissione,
            # Amounts will be calculated from lines
            imponibile=Decimal("0"),
            iva=Decimal("0"),
            totale=Decimal("0"),
        )

        db.add(nota_credito)
        db.flush()  # Get nota_credito.id for line items

        # Copy line items from source invoice
        # TD04 standard practice: use positive amounts (not negative)
        total_imponibile = Decimal("0")
        total_iva = Decimal("0")
        total_totale = Decimal("0")

        if full_refund:
            # Copy all lines
            for source_riga in source_fattura.righe:
                riga = RigaFattura(
                    fattura_id=nota_credito.id,
                    numero_riga=source_riga.numero_riga,
                    descrizione=source_riga.descrizione,
                    quantita=source_riga.quantita,
                    prezzo_unitario=source_riga.prezzo_unitario,
                    unita_misura=source_riga.unita_misura,
                    aliquota_iva=source_riga.aliquota_iva,
                    natura=source_riga.natura,
                    imponibile=source_riga.imponibile,
                    iva=source_riga.iva,
                    totale=source_riga.totale,
                )
                db.add(riga)
                total_imponibile += riga.imponibile
                total_iva += riga.iva
                total_totale += riga.totale
        else:
            # Partial refund: copy only specified lines with adjusted quantities
            if not line_items:
                return {"error": "line_items required when full_refund=False"}

            # Build map of source lines by numero_riga
            source_lines_map = {riga.numero_riga: riga for riga in source_fattura.righe}

            for item in line_items:
                numero_riga = item.get("numero_riga")
                quantita = Decimal(str(item.get("quantita", 0)))

                if numero_riga not in source_lines_map:
                    return {"error": f"Line {numero_riga} not found in source invoice {fattura_id}"}

                source_riga = source_lines_map[numero_riga]

                # Validate quantity
                if quantita <= 0 or quantita > source_riga.quantita:
                    return {
                        "error": f"Invalid quantity {quantita} for line {numero_riga} (source has {source_riga.quantita})"
                    }

                # Calculate amounts for partial quantity
                imponibile = source_riga.prezzo_unitario * quantita
                iva = imponibile * source_riga.aliquota_iva / Decimal("100")
                totale = imponibile + iva

                riga = RigaFattura(
                    fattura_id=nota_credito.id,
                    numero_riga=source_riga.numero_riga,
                    descrizione=source_riga.descrizione,
                    quantita=quantita,
                    prezzo_unitario=source_riga.prezzo_unitario,
                    unita_misura=source_riga.unita_misura,
                    aliquota_iva=source_riga.aliquota_iva,
                    natura=source_riga.natura,
                    imponibile=imponibile,
                    iva=iva,
                    totale=totale,
                )
                db.add(riga)
                total_imponibile += imponibile
                total_iva += iva
                total_totale += totale

        # Update nota di credito totals
        nota_credito.imponibile = total_imponibile
        nota_credito.iva = total_iva
        nota_credito.totale = total_totale

        db.commit()
        db.refresh(nota_credito)

        # Publish event
        event_bus = get_event_bus()
        if event_bus:
            event_bus.publish(
                InvoiceCreatedEvent(
                    invoice_id=nota_credito.id,
                    invoice_number=f"{nota_credito.numero}/{nota_credito.anno}",
                    client_id=nota_credito.cliente_id,
                    client_name=source_fattura.cliente.denominazione,
                    total_amount=nota_credito.totale,
                )
            )

        logger.info(
            "nota_credito_created",
            nota_credito_id=nota_credito.id,
            source_invoice_id=fattura_id,
            numero=numero,
            anno=anno,
            totale=float(nota_credito.totale),
            full_refund=full_refund,
        )

        return {
            "success": True,
            "nota_credito_id": nota_credito.id,
            "numero": nota_credito.numero,
            "anno": nota_credito.anno,
            "tipo_documento": "TD04",
            "cliente": source_fattura.cliente.denominazione,
            "stato": nota_credito.stato.value,
            "totale": float(nota_credito.totale),
            "source_invoice": {
                "id": source_fattura.id,
                "numero": f"{source_fattura.numero}/{source_fattura.anno}",
                "data": source_fattura.data_emissione.isoformat(),
            },
            "message": f"Nota di credito {numero}/{anno} created successfully (TD04) linked to invoice {source_fattura.numero}/{source_fattura.anno}",
        }

    except ValueError as e:
        db.rollback()
        logger.error("create_nota_credito_validation_error", error=str(e))
        return {"error": str(e)}
    except Exception as e:
        db.rollback()
        logger.error("create_nota_credito_failed", error=str(e))
        return {"error": f"Failed to create nota di credito: {str(e)}"}
    finally:
        db.close()
