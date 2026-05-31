"""Invoice SDI tools (XML validation and PEC sending)."""

from typing import Any

from pydantic import validate_call

from openfatture.storage.database.models import (
    Fattura,
    StatoFattura,
)
from openfatture.utils.logging import get_logger
from openfatture.utils.security import validate_integer_input

from . import _db

logger = get_logger(__name__)


@validate_call
def validate_invoice_xml(fattura_id: int) -> dict[str, Any]:
    """
    Validate FatturaPA XML for invoice.

    Args:
        fattura_id: Invoice ID

    Returns:
        Dictionary with validation result
    """
    from openfatture.core.fatture.service import InvoiceService
    from openfatture.utils.config import get_settings

    # Validate input
    fattura_id = validate_integer_input(fattura_id, min_value=1)

    db = _db.get_session()
    try:
        fattura = db.query(Fattura).filter(Fattura.id == fattura_id).first()
        if not fattura:
            return {"error": f"Invoice {fattura_id} not found"}

        # Check has righe
        if not fattura.righe:
            return {"error": "Invoice has no line items. Add at least one riga first."}

        settings = get_settings()
        service = InvoiceService(settings)

        # Generate and validate XML
        xml_content, error = service.generate_xml(fattura, validate=True)

        if error:
            logger.warning("invoice_xml_validation_failed", fattura_id=fattura_id, error=error)
            return {
                "success": False,
                "valid": False,
                "error": error,
                "invoice_number": f"{fattura.numero}/{fattura.anno}",
            }

        # Update database with xml_path
        db.commit()

        logger.info("invoice_xml_validated", fattura_id=fattura_id)

        return {
            "success": True,
            "valid": True,
            "invoice_id": fattura_id,
            "invoice_number": f"{fattura.numero}/{fattura.anno}",
            "xml_path": fattura.xml_path,
            "message": f"XML validated successfully for invoice {fattura.numero}/{fattura.anno}",
        }

    except Exception as e:
        logger.error("validate_invoice_xml_failed", fattura_id=fattura_id, error=str(e))
        return {"error": str(e)}
    finally:
        db.close()


@validate_call
def send_invoice_to_sdi(fattura_id: int, signed: bool = False) -> dict[str, Any]:
    """
    Send invoice to SDI via PEC.

    CRITICAL: This action cannot be undone. Invoice will be sent to SDI.

    Args:
        fattura_id: Invoice ID
        signed: Whether XML is digitally signed (default False)

    Returns:
        Dictionary with send result
    """
    from openfatture.cli.lifespan import get_event_bus
    from openfatture.core.events import InvoiceSentEvent
    from openfatture.core.fatture.service import InvoiceService
    from openfatture.utils.config import get_settings
    from openfatture.utils.email.sender import TemplatePECSender

    # Validate input
    fattura_id = validate_integer_input(fattura_id, min_value=1)

    db = _db.get_session()
    try:
        fattura = db.query(Fattura).filter(Fattura.id == fattura_id).first()
        if not fattura:
            return {"error": f"Invoice {fattura_id} not found"}

        # Check invoice is ready to send
        if fattura.stato not in [StatoFattura.BOZZA, StatoFattura.DA_INVIARE]:
            return {
                "error": f"Invoice in status '{fattura.stato.value}' cannot be sent. Must be BOZZA or DA_INVIARE."
            }

        if not fattura.righe:
            return {"error": "Invoice has no line items"}

        settings = get_settings()
        service = InvoiceService(settings)

        # Step 1: Generate/validate XML if not exists
        if not fattura.xml_path:
            xml_content, error = service.generate_xml(fattura, validate=True)
            if error:
                return {"error": f"XML validation failed: {error}"}

        # Step 2: Send via PEC
        xml_path = service.get_xml_path(fattura)
        sender = TemplatePECSender(settings=settings, locale=settings.locale)

        success, error = sender.send_invoice_to_sdi(fattura, xml_path, signed=signed)

        if not success:
            return {"error": f"Failed to send invoice: {error}"}

        # Step 3: Update status
        fattura.stato = StatoFattura.INVIATA
        from datetime import datetime

        fattura.data_invio_sdi = datetime.now()

        db.commit()

        # Publish event
        event_bus = get_event_bus()
        if event_bus:
            event_bus.publish(
                InvoiceSentEvent(
                    invoice_id=fattura.id,
                    invoice_number=f"{fattura.numero}/{fattura.anno}",
                    recipient=fattura.cliente.codice_destinatario or settings.sdi_pec_address,
                    pec_address=settings.sdi_pec_address,
                    xml_path=str(xml_path),
                    signed=signed,
                )
            )

        logger.info("invoice_sent_to_sdi", fattura_id=fattura_id, signed=signed)

        return {
            "success": True,
            "invoice_id": fattura_id,
            "invoice_number": f"{fattura.numero}/{fattura.anno}",
            "stato": fattura.stato.value,
            "data_invio": fattura.data_invio_sdi.isoformat() if fattura.data_invio_sdi else None,
            "sdi_address": settings.sdi_pec_address,
            "message": f"Invoice {fattura.numero}/{fattura.anno} sent to SDI successfully via PEC",
        }

    except Exception as e:
        db.rollback()
        logger.error("send_invoice_to_sdi_failed", fattura_id=fattura_id, error=str(e))
        return {"error": str(e)}
    finally:
        db.close()
