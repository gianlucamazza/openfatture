"""Tools for invoice operations."""

from decimal import Decimal
from typing import Any, TypedDict

from pydantic import validate_call
from sqlalchemy.orm import selectinload

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
from openfatture.storage.database.base import get_session
from openfatture.storage.database.models import (
    Cliente,
    Fattura,
    RigaFattura,
    StatoFattura,
    TipoDocumento,
)
from openfatture.utils.logging import get_logger
from openfatture.utils.security import sanitize_sql_like_input, validate_integer_input

logger = get_logger(__name__)


class InvoiceStats(TypedDict):
    anno: int
    totale_fatture: int
    per_stato: dict[str, int]
    importo_totale: float


# =============================================================================
# Invoice Query Tools
# =============================================================================


@validate_call
def search_invoices(
    query: str | None = None,
    anno: int | None = None,
    stato: str | None = None,
    cliente_id: int | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    # Sanitize and validate inputs
    if query is not None:
        query = sanitize_sql_like_input(query)

    if anno is not None:
        anno = validate_integer_input(anno, min_value=2000, max_value=2100)

    if cliente_id is not None:
        cliente_id = validate_integer_input(cliente_id, min_value=1)

    limit = validate_integer_input(limit, min_value=1, max_value=100)
    """
    Search for invoices matching criteria.

    Args:
        query: Search in invoice number or notes
        anno: Filter by year
        stato: Filter by status
        cliente_id: Filter by client ID
        limit: Maximum results

    Returns:
        Dictionary with search results
    """
    db = get_session()
    try:
        # Build query with eager loading to avoid N+1 queries
        db_query = db.query(Fattura).options(selectinload(Fattura.cliente))

        if query:
            db_query = db_query.filter(
                (Fattura.numero.contains(query)) | (Fattura.note.contains(query))
            )

        if anno:
            db_query = db_query.filter(Fattura.anno == anno)

        if stato:
            try:
                stato_enum = StatoFattura(stato)
                db_query = db_query.filter(Fattura.stato == stato_enum)
            except ValueError:
                pass  # Invalid status, ignore

        if cliente_id:
            db_query = db_query.filter(Fattura.cliente_id == cliente_id)

        # Order by most recent
        db_query = db_query.order_by(Fattura.anno.desc(), Fattura.numero.desc())

        # Get results
        fatture = db_query.limit(limit).all()

        # Format results
        results = []
        for f in fatture:
            # Skip if cliente is None
            if f.cliente is None:
                continue

            results.append(
                {
                    "id": f.id,
                    "numero": f.numero,
                    "anno": f.anno,
                    "data": f.data_emissione.isoformat(),
                    "cliente": f.cliente.denominazione,
                    "importo": float(f.totale),
                    "stato": f.stato.value,
                }
            )

        return {
            "count": len(results),
            "fatture": results,
            "has_more": len(fatture) == limit,
        }

    except Exception as e:
        logger.error("search_invoices_failed", error=str(e))
        return {"error": str(e), "count": 0, "fatture": []}

    finally:
        db.close()


@validate_call
def get_invoice_details(fattura_id: int) -> dict[str, Any]:
    # Validate input
    fattura_id = validate_integer_input(fattura_id, min_value=1)
    """
    Get detailed information about an invoice.

    Args:
        fattura_id: Invoice ID

    Returns:
        Dictionary with invoice details
    """
    db = get_session()
    try:
        # Use selectinload to avoid N+1 queries when accessing relationships
        fattura = (
            db.query(Fattura)
            .options(selectinload(Fattura.cliente), selectinload(Fattura.righe))
            .filter(Fattura.id == fattura_id)
            .first()
        )

        if fattura is None:
            return {"error": f"Fattura {fattura_id} non trovata"}

        if fattura.cliente is None:
            return {"error": f"Fattura {fattura_id} has no associated cliente"}

        # Format details
        details = {
            "id": fattura.id,
            "numero": fattura.numero,
            "anno": fattura.anno,
            "data_emissione": fattura.data_emissione.isoformat(),
            "cliente": {
                "id": fattura.cliente.id,
                "denominazione": fattura.cliente.denominazione,
                "partita_iva": fattura.cliente.partita_iva,
            },
            "importi": {
                "imponibile": float(fattura.imponibile),
                "iva": float(fattura.iva),
                "totale": float(fattura.totale),
            },
            "stato": fattura.stato.value,
            "note": fattura.note or "",
            "righe_count": len(fattura.righe),
        }

        # Add lines if present
        if fattura.righe:
            details["righe"] = [
                {
                    "descrizione": r.descrizione,
                    "quantita": float(r.quantita),
                    "prezzo_unitario": float(r.prezzo_unitario),
                    "aliquota_iva": float(r.aliquota_iva),
                }
                for r in fattura.righe
            ]

        return details

    except Exception as e:
        logger.error("get_invoice_details_failed", fattura_id=fattura_id, error=str(e))
        return {"error": str(e)}

    finally:
        db.close()


@validate_call
def get_invoice_stats(anno: int | None = None) -> dict[str, Any]:
    """
    Get statistics about invoices.

    Args:
        anno: Filter by year (current year if None)

    Returns:
        Dictionary with stats
    """
    # Validate input after parameter validation
    if anno is not None:
        anno = validate_integer_input(anno, min_value=2000, max_value=2100)
    from datetime import datetime

    db = get_session()
    try:
        year = anno or datetime.now().year

        # Count by status
        per_stato: dict[str, int] = {}
        stats: InvoiceStats = {
            "anno": year,
            "totale_fatture": 0,
            "per_stato": per_stato,
            "importo_totale": 0.0,
        }

        for stato in StatoFattura:
            count = db.query(Fattura).filter(Fattura.anno == year, Fattura.stato == stato).count()
            per_stato[stato.value] = count
            stats["totale_fatture"] += count

        # Total amount
        fatture = db.query(Fattura).filter(Fattura.anno == year).all()
        stats["importo_totale"] = sum(float(f.totale) for f in fatture)

        return dict(stats)

    except Exception as e:
        logger.error("get_invoice_stats_failed", error=str(e))
        return {"error": str(e)}

    finally:
        db.close()


# =============================================================================
# Invoice WRITE Tools
# =============================================================================


@validate_call
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
    from openfatture.core.events import InvoiceCreatedEvent

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

    db = get_session()
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

    db = get_session()
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


@validate_call
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


@validate_call
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


@validate_call
def update_invoice_status(
    fattura_id: int,
    new_status: str,
) -> dict[str, Any]:
    """
    Update invoice status (workflow: BOZZA → DA_INVIARE).

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
            "message": f"Invoice {fattura.numero}/{fattura.anno} status changed: {old_status} → {new_status_enum.value}",
        }

    except Exception as e:
        db.rollback()
        logger.error("update_invoice_status_failed", fattura_id=fattura_id, error=str(e))
        return {"error": str(e)}
    finally:
        db.close()


# =============================================================================
# Tool Definitions
# =============================================================================


def get_invoice_tools() -> list[Tool]:
    """
    Get all invoice-related tools.

    Returns:
        List of Tool instances
    """
    return [
        Tool(
            name="search_invoices",
            description="Search for invoices by number, year, status, or client",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="query",
                    type=ToolParameterType.STRING,
                    description="Search query (numero or note)",
                    required=False,
                ),
                ToolParameter(
                    name="anno",
                    type=ToolParameterType.INTEGER,
                    description="Filter by year (e.g., 2025)",
                    required=False,
                ),
                ToolParameter(
                    name="stato",
                    type=ToolParameterType.STRING,
                    description="Filter by status",
                    required=False,
                    enum=["bozza", "da_inviare", "inviata", "accettata", "rifiutata"],
                ),
                ToolParameter(
                    name="cliente_id",
                    type=ToolParameterType.INTEGER,
                    description="Filter by client ID",
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
            func=search_invoices,
            examples=[
                "search_invoices(anno=2025)",
                "search_invoices(stato='da_inviare', limit=5)",
                "search_invoices(query='consulenza')",
            ],
            tags=["search", "query"],
        ),
        Tool(
            name="get_invoice_details",
            description="Get detailed information about a specific invoice",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID",
                    required=True,
                ),
            ],
            func=get_invoice_details,
            examples=["get_invoice_details(fattura_id=123)"],
            tags=["details", "view"],
        ),
        Tool(
            name="get_invoice_stats",
            description="Get statistics about invoices (count, totals by status)",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="anno",
                    type=ToolParameterType.INTEGER,
                    description="Year for statistics (current year if not specified)",
                    required=False,
                ),
            ],
            func=get_invoice_stats,
            examples=[
                "get_invoice_stats()",
                "get_invoice_stats(anno=2024)",
            ],
            tags=["stats", "analytics"],
        ),
        # WRITE tools
        Tool(
            name="create_invoice",
            description="Create a new invoice for a client. Returns invoice_id to add line items.",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="cliente_id",
                    type=ToolParameterType.INTEGER,
                    description="Client ID (required)",
                    required=True,
                ),
                ToolParameter(
                    name="anno",
                    type=ToolParameterType.INTEGER,
                    description="Year (current year if not specified)",
                    required=False,
                ),
                ToolParameter(
                    name="numero",
                    type=ToolParameterType.STRING,
                    description="Invoice number (auto-generated if not specified)",
                    required=False,
                ),
                ToolParameter(
                    name="data_emissione",
                    type=ToolParameterType.STRING,
                    description="Issue date YYYY-MM-DD (today if not specified)",
                    required=False,
                ),
                ToolParameter(
                    name="tipo_documento",
                    type=ToolParameterType.STRING,
                    description="Document type (default TD01 - Fattura)",
                    required=False,
                    enum=["TD01", "TD04", "TD06"],
                    default="TD01",
                ),
                ToolParameter(
                    name="note",
                    type=ToolParameterType.STRING,
                    description="Optional notes",
                    required=False,
                ),
            ],
            func=create_invoice,
            requires_confirmation=True,
            examples=[
                "create_invoice(cliente_id=1)",
                "create_invoice(cliente_id=5, note='Q1 2025 consulting')",
            ],
            tags=["write", "create"],
        ),
        Tool(
            name="create_riga",
            description="Add line item to invoice. Updates invoice totals automatically.",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID",
                    required=True,
                ),
                ToolParameter(
                    name="descrizione",
                    type=ToolParameterType.STRING,
                    description="Item description",
                    required=True,
                ),
                ToolParameter(
                    name="quantita",
                    type=ToolParameterType.NUMBER,
                    description="Quantity",
                    required=True,
                ),
                ToolParameter(
                    name="prezzo_unitario",
                    type=ToolParameterType.NUMBER,
                    description="Unit price in euros",
                    required=True,
                ),
                ToolParameter(
                    name="aliquota_iva",
                    type=ToolParameterType.NUMBER,
                    description="VAT rate percentage (default 22%)",
                    required=False,
                    default=22.0,
                ),
                ToolParameter(
                    name="unita_misura",
                    type=ToolParameterType.STRING,
                    description="Unit of measure (default 'ore')",
                    required=False,
                    default="ore",
                ),
            ],
            func=create_riga,
            requires_confirmation=True,
            examples=[
                "create_riga(fattura_id=123, descrizione='Web consulting', quantita=3, prezzo_unitario=150)",
                "create_riga(fattura_id=123, descrizione='Backend dev', quantita=8, prezzo_unitario=100, aliquota_iva=22)",
            ],
            tags=["write", "create"],
        ),
        Tool(
            name="update_riga",
            description="Update line item in invoice (only BOZZA or DA_INVIARE). Updates invoice totals automatically.",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="riga_id",
                    type=ToolParameterType.INTEGER,
                    description="Line item ID",
                    required=True,
                ),
                ToolParameter(
                    name="descrizione",
                    type=ToolParameterType.STRING,
                    description="Item description",
                    required=False,
                ),
                ToolParameter(
                    name="quantita",
                    type=ToolParameterType.NUMBER,
                    description="Quantity",
                    required=False,
                ),
                ToolParameter(
                    name="prezzo_unitario",
                    type=ToolParameterType.NUMBER,
                    description="Unit price in euros",
                    required=False,
                ),
                ToolParameter(
                    name="aliquota_iva",
                    type=ToolParameterType.NUMBER,
                    description="VAT rate percentage",
                    required=False,
                ),
                ToolParameter(
                    name="unita_misura",
                    type=ToolParameterType.STRING,
                    description="Unit of measure",
                    required=False,
                ),
            ],
            func=update_riga,
            requires_confirmation=True,
            examples=[
                "update_riga(riga_id=5, quantita=5)",
                "update_riga(riga_id=10, descrizione='Updated consulting', prezzo_unitario=200)",
            ],
            tags=["write", "update"],
        ),
        Tool(
            name="delete_riga",
            description="CRITICAL: Delete line item from invoice (only BOZZA or DA_INVIARE). Updates invoice totals automatically.",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="riga_id",
                    type=ToolParameterType.INTEGER,
                    description="Line item ID to delete",
                    required=True,
                ),
            ],
            func=delete_riga,
            requires_confirmation=True,
            examples=["delete_riga(riga_id=5)"],
            tags=["write", "delete", "critical"],
        ),
        Tool(
            name="validate_invoice_xml",
            description="Validate FatturaPA XML for invoice before sending to SDI",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID",
                    required=True,
                ),
            ],
            func=validate_invoice_xml,
            examples=["validate_invoice_xml(fattura_id=123)"],
            tags=["validation", "xml"],
        ),
        Tool(
            name="send_invoice_to_sdi",
            description="Send invoice to SDI via PEC. CRITICAL: Cannot be undone!",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID",
                    required=True,
                ),
                ToolParameter(
                    name="signed",
                    type=ToolParameterType.BOOLEAN,
                    description="Whether XML is digitally signed (default False)",
                    required=False,
                    default=False,
                ),
            ],
            func=send_invoice_to_sdi,
            requires_confirmation=True,
            examples=[
                "send_invoice_to_sdi(fattura_id=123)",
                "send_invoice_to_sdi(fattura_id=123, signed=True)",
            ],
            tags=["write", "send", "critical"],
        ),
        Tool(
            name="update_invoice",
            description="Update invoice information (only BOZZA status). Modify date, document type, or notes.",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID to update",
                    required=True,
                ),
                ToolParameter(
                    name="data_emissione",
                    type=ToolParameterType.STRING,
                    description="New issue date YYYY-MM-DD (optional)",
                    required=False,
                ),
                ToolParameter(
                    name="tipo_documento",
                    type=ToolParameterType.STRING,
                    description="New document type (optional)",
                    required=False,
                    enum=["TD01", "TD04", "TD06"],
                ),
                ToolParameter(
                    name="note",
                    type=ToolParameterType.STRING,
                    description="New notes (optional)",
                    required=False,
                ),
            ],
            func=update_invoice,
            requires_confirmation=True,
            examples=[
                "update_invoice(fattura_id=123, note='Updated description')",
                "update_invoice(fattura_id=456, data_emissione='2025-01-15', tipo_documento='TD01')",
            ],
            tags=["write", "update"],
        ),
        Tool(
            name="delete_invoice",
            description="CRITICAL: Delete invoice from database (only BOZZA status). Irreversible operation!",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID to delete",
                    required=True,
                ),
                ToolParameter(
                    name="force",
                    type=ToolParameterType.BOOLEAN,
                    description="Force deletion even if invoice has line items (default False)",
                    required=False,
                    default=False,
                ),
            ],
            func=delete_invoice,
            requires_confirmation=True,
            examples=[
                "delete_invoice(fattura_id=999)",
                "delete_invoice(fattura_id=999, force=True)",
            ],
            tags=["write", "delete", "critical"],
        ),
        Tool(
            name="update_invoice_status",
            description="Update invoice status (workflow: BOZZA ↔ DA_INVIARE). Validates invoice completeness.",
            category="invoices",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID",
                    required=True,
                ),
                ToolParameter(
                    name="new_status",
                    type=ToolParameterType.STRING,
                    description="New status (bozza or da_inviare)",
                    required=True,
                    enum=["bozza", "da_inviare"],
                ),
            ],
            func=update_invoice_status,
            requires_confirmation=True,
            examples=[
                "update_invoice_status(fattura_id=123, new_status='da_inviare')",
                "update_invoice_status(fattura_id=456, new_status='bozza')",
            ],
            tags=["write", "status", "workflow"],
        ),
    ]
