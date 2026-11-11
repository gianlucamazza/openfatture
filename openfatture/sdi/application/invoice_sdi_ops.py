"""Invoice SDI operations: FatturaPA XML and PEC sending."""

from pathlib import Path
from typing import Any

from pydantic import validate_call

from openfatture.platform.errors import describe_error
from openfatture.platform.logging import get_logger
from openfatture.platform.security import validate_integer_input
from openfatture.storage.database.models import (
    Fattura,
    StatoFattura,
)
from openfatture.storage.session import db_session

logger = get_logger(__name__)


@validate_call
def generate_invoice_xml(fattura_id: int) -> dict[str, Any]:
    """Generate the FatturaPA XML of an invoice, validated against the XSD.

    The file is written to the archive (``archivio/xml``, named as SDI
    requires) only when it is valid, and the invoice records its path: it is
    the file that ``sign_invoice_xml`` signs and that a portal or
    intermediary receives.
    """
    from openfatture.billing.fatture.service import InvoiceService
    from openfatture.exceptions import XMLValidationError
    from openfatture.platform.config import get_settings

    fattura_id = validate_integer_input(fattura_id, min_value=1)
    with db_session() as db:
        try:
            fattura = db.get(Fattura, fattura_id)
            if fattura is None:
                return {"error": f"Invoice {fattura_id} not found"}
            if not fattura.righe:
                return {"error": "Invoice has no line items. Add at least one riga first."}
            number = f"{fattura.numero}/{fattura.anno}"
            try:
                _content, error = InvoiceService(get_settings()).generate_xml(
                    fattura, validate=True
                )
            except XMLValidationError as exc:
                error = str(exc)
            if error:
                db.rollback()
                return {"success": False, "valid": False, "error": error, "invoice_number": number}
            db.commit()
            logger.info("invoice_xml_generated", fattura_id=fattura_id)
            return {
                "success": True,
                "valid": True,
                "invoice_id": fattura_id,
                "invoice_number": number,
                "xml_path": fattura.xml_path,
                "message": f"Valid XML written for invoice {number}",
            }
        except Exception as e:
            db.rollback()
            logger.error("generate_invoice_xml_failed", fattura_id=fattura_id, error=str(e))
            return {"error": describe_error(e)}


def _prepare_transmission(fattura: Fattura, service: Any, signed: bool) -> Path | str:
    """Return the file to transmit, or an error message.

    Unsigned: the XML is regenerated from the current invoice and validated
    against the FatturaPA schema. Signed: the stored ``.p7m`` is sent only if
    the XML it was made from is still valid and identical to what the current
    invoice data produces (an edit after signing requires signing again).
    """
    from openfatture.exceptions import XMLValidationError
    from openfatture.sdi.validator.xsd_validator import FatturaPAValidator
    from openfatture.sdi.xml_builder.fatturapa import FatturaPABuilder

    if not signed:
        try:
            _content, error = service.generate_xml(fattura, validate=True)
        except XMLValidationError as exc:
            return f"XML validation failed: {exc}"
        if error:
            return f"XML validation failed: {error}"
        return Path(service.get_xml_path(fattura))

    signed_path = Path(fattura.xml_firmato_path) if fattura.xml_firmato_path else None
    if signed_path is None or not signed_path.exists():
        return "No signed XML for this invoice: sign it first (sign_invoice_xml)"
    xml_file = Path(fattura.xml_path) if fattura.xml_path else None
    if xml_file is None or not xml_file.exists():
        return "The XML that was signed is missing: generate and sign it again"
    stored = xml_file.read_text(encoding="utf-8")
    valid, error = FatturaPAValidator().validate(stored)
    if not valid:
        return f"XML validation failed: {error}"
    current = FatturaPABuilder(service.settings).build(fattura)
    if current.strip() != stored.strip():
        return "The invoice changed after signing: generate the XML and sign it again"
    return signed_path


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
    from openfatture.billing.fatture.service import InvoiceService
    from openfatture.events import InvoiceSentEvent, get_global_event_bus
    from openfatture.platform.config import get_settings
    from openfatture.sdi.email.sender import TemplatePECSender

    # Validate input
    fattura_id = validate_integer_input(fattura_id, min_value=1)

    with db_session() as db:
        try:
            fattura = db.query(Fattura).filter(Fattura.id == fattura_id).first()
            if not fattura:
                return {"error": f"Invoice {fattura_id} not found"}

            # Check if invoice was issued elsewhere
            if getattr(fattura, "issued_elsewhere", False):
                logger.warning(
                    "sdi_send_blocked_issued_elsewhere",
                    fattura_id=fattura_id,
                    numero=fattura.numero,
                    anno=fattura.anno,
                )
                return {
                    "error": (
                        f"Cannot send invoice {fattura.numero}/{fattura.anno} to SDI: "
                        "This invoice was issued elsewhere and is stored for reference only. "
                        "SDI submission is blocked to prevent duplicate submissions."
                    )
                }

            # Check invoice is ready to send
            if fattura.stato not in [StatoFattura.BOZZA, StatoFattura.DA_INVIARE]:
                return {
                    "error": f"Invoice in status '{fattura.stato.value}' cannot be sent. Must be BOZZA or DA_INVIARE."
                }

            if not fattura.righe:
                return {"error": "Invoice has no line items"}

            settings = get_settings()
            service = InvoiceService(settings)

            # Step 1: never transmit XML that was not validated against the
            # current invoice data (it may predate edits or skip validation).
            prepared = _prepare_transmission(fattura, service, signed)
            if isinstance(prepared, str):
                return {"error": prepared}
            xml_path = prepared

            # Step 2: Send via PEC
            sender = TemplatePECSender(settings=settings, locale=settings.locale)

            success, error = sender.send_invoice_to_sdi(fattura, xml_path, signed=signed)

            if not success:
                return {"error": f"Failed to send invoice: {error}"}

            # Publish event
            event_bus = get_global_event_bus()
            if event_bus:
                try:
                    event_bus.publish(
                        InvoiceSentEvent(
                            invoice_id=fattura.id,
                            invoice_number=f"{fattura.numero}/{fattura.anno}",
                            recipient=fattura.cliente.codice_destinatario
                            or settings.sdi_pec_address,
                            pec_address=settings.sdi_pec_address,
                            xml_path=str(xml_path),
                            signed=signed,
                        )
                    )

                except Exception as exc:
                    logger.warning("sdi_post_commit_event_failed", error=str(exc))

            logger.info("invoice_sent_to_sdi", fattura_id=fattura_id, signed=signed)

            return {
                "success": True,
                "invoice_id": fattura_id,
                "invoice_number": f"{fattura.numero}/{fattura.anno}",
                "stato": fattura.stato.value,
                "data_invio": fattura.data_invio_sdi.isoformat()
                if fattura.data_invio_sdi
                else None,
                "sdi_address": settings.sdi_pec_address,
                "message": f"Invoice {fattura.numero}/{fattura.anno} sent to SDI successfully via PEC",
            }

        except Exception as e:
            db.rollback()
            logger.error("send_invoice_to_sdi_failed", fattura_id=fattura_id, error=str(e))
            return {"error": describe_error(e)}
