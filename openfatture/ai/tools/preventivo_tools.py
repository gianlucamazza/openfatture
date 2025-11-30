"""Tools for preventivo (quote/estimate) management."""

from typing import Any

from pydantic import validate_call

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
from openfatture.core.preventivi.service import PreventivoService
from openfatture.storage.database.base import get_session
from openfatture.storage.database.models import Preventivo, StatoPreventivo
from openfatture.utils.config import get_settings
from openfatture.utils.logging import get_logger
from openfatture.utils.security import validate_integer_input

logger = get_logger(__name__)


# =============================================================================
# READ Tools
# =============================================================================


@validate_call
def search_preventivi(
    stato: str | None = None,
    cliente_id: int | None = None,
    anno: int | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Search preventivi with filters.

    Args:
        stato: Filter by status (bozza, inviato, accettato, rifiutato, scaduto, convertito)
        cliente_id: Filter by client ID
        anno: Filter by year
        limit: Maximum results (default 20, max 100)

    Returns:
        Dictionary with search results
    """
    # Validate inputs
    if cliente_id is not None:
        cliente_id = validate_integer_input(cliente_id, min_value=1)
    if anno is not None:
        anno = validate_integer_input(anno, min_value=2000, max_value=2100)
    limit = validate_integer_input(limit, min_value=1, max_value=100)

    db = get_session()
    try:
        # Parse status if provided
        stato_enum = None
        if stato:
            try:
                stato_enum = StatoPreventivo(stato.lower())
            except ValueError:
                return {
                    "error": f"Invalid status: {stato}. Valid: bozza, inviato, accettato, rifiutato, scaduto, convertito",
                    "count": 0,
                    "preventivi": [],
                }

        # Use service to list preventivi
        settings = get_settings()
        service = PreventivoService(settings=settings)

        preventivi = service.list_preventivi(
            db=db,
            stato=stato_enum,
            cliente_id=cliente_id,
            anno=anno,
            limit=limit,
        )

        # Format results
        results = []
        for p in preventivi:
            results.append(
                {
                    "preventivo_id": p.id,
                    "numero": f"{p.numero}/{p.anno}",
                    "data_emissione": p.data_emissione.isoformat(),
                    "data_scadenza": p.data_scadenza.isoformat(),
                    "cliente": p.cliente.denominazione if p.cliente else None,
                    "cliente_id": p.cliente_id,
                    "imponibile": float(p.imponibile),
                    "iva": float(p.iva),
                    "totale": float(p.totale),
                    "stato": p.stato.value,
                    "validita_giorni": p.validita_giorni,
                    "righe_count": len(p.righe) if p.righe else 0,
                }
            )

        return {
            "count": len(results),
            "preventivi": results,
            "has_more": len(preventivi) == limit,
        }

    except Exception as e:
        logger.error("search_preventivi_failed", error=str(e))
        return {"error": str(e), "count": 0, "preventivi": []}
    finally:
        db.close()


@validate_call
def get_preventivo_details(preventivo_id: int) -> dict[str, Any]:
    """
    Get detailed information about a preventivo.

    Args:
        preventivo_id: Preventivo ID

    Returns:
        Dictionary with preventivo details
    """
    # Validate input
    preventivo_id = validate_integer_input(preventivo_id, min_value=1)

    db = get_session()
    try:
        preventivo = db.query(Preventivo).filter(Preventivo.id == preventivo_id).first()

        if not preventivo:
            return {"error": f"Preventivo {preventivo_id} not found"}

        # Format righe
        righe = []
        for riga in preventivo.righe:
            righe.append(
                {
                    "numero_riga": riga.numero_riga,
                    "descrizione": riga.descrizione,
                    "quantita": float(riga.quantita),
                    "prezzo_unitario": float(riga.prezzo_unitario),
                    "unita_misura": riga.unita_misura,
                    "aliquota_iva": float(riga.aliquota_iva),
                    "imponibile": float(riga.imponibile),
                    "iva": float(riga.iva),
                    "totale": float(riga.totale),
                }
            )

        return {
            "preventivo_id": preventivo.id,
            "numero": f"{preventivo.numero}/{preventivo.anno}",
            "anno": preventivo.anno,
            "data_emissione": preventivo.data_emissione.isoformat(),
            "data_scadenza": preventivo.data_scadenza.isoformat(),
            "cliente_id": preventivo.cliente_id,
            "cliente": (
                {
                    "id": preventivo.cliente.id,
                    "denominazione": preventivo.cliente.denominazione,
                    "partita_iva": preventivo.cliente.partita_iva,
                    "email": preventivo.cliente.email,
                }
                if preventivo.cliente
                else None
            ),
            "imponibile": float(preventivo.imponibile),
            "iva": float(preventivo.iva),
            "totale": float(preventivo.totale),
            "stato": preventivo.stato.value,
            "validita_giorni": preventivo.validita_giorni,
            "note": preventivo.note,
            "condizioni": preventivo.condizioni,
            "righe": righe,
            "fattura_id": preventivo.fattura.id if preventivo.fattura else None,
        }

    except Exception as e:
        logger.error("get_preventivo_details_failed", preventivo_id=preventivo_id, error=str(e))
        return {"error": str(e)}
    finally:
        db.close()


# =============================================================================
# WRITE Tools
# =============================================================================


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
               - aliquota_iva (float, default 22.0)
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

    db = get_session()
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
        return {"success": False, "error": str(e)}
    finally:
        db.close()


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

    db = get_session()
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
        return {"success": False, "error": str(e)}
    finally:
        db.close()


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

    db = get_session()
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
            preventivo.data_scadenza = preventivo.data_emissione + timedelta(days=validita_giorni)
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
        return {"success": False, "error": str(e)}
    finally:
        db.close()


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

    db = get_session()
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
        return {"success": False, "error": str(e)}
    finally:
        db.close()


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

    db = get_session()
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
        return {"success": False, "error": str(e)}
    finally:
        db.close()


# =============================================================================
# Tool Definitions
# =============================================================================


def get_preventivo_tools() -> list[Tool]:
    """
    Get all preventivo-related tools.

    Returns:
        List of Tool instances
    """
    return [
        Tool(
            name="search_preventivi",
            description="Search preventivi (quotes) with optional filters (status, client, year)",
            category="preventivi",
            parameters=[
                ToolParameter(
                    name="stato",
                    type=ToolParameterType.STRING,
                    description="Filter by status",
                    required=False,
                    enum=["bozza", "inviato", "accettato", "rifiutato", "scaduto", "convertito"],
                ),
                ToolParameter(
                    name="cliente_id",
                    type=ToolParameterType.INTEGER,
                    description="Filter by client ID",
                    required=False,
                ),
                ToolParameter(
                    name="anno",
                    type=ToolParameterType.INTEGER,
                    description="Filter by year",
                    required=False,
                ),
                ToolParameter(
                    name="limit",
                    type=ToolParameterType.INTEGER,
                    description="Maximum results (default 20)",
                    required=False,
                    default=20,
                ),
            ],
            func=search_preventivi,
            examples=[
                "search_preventivi()",
                "search_preventivi(stato='inviato', anno=2025)",
                "search_preventivi(cliente_id=5, limit=10)",
            ],
            tags=["search", "preventivo", "quote"],
        ),
        Tool(
            name="get_preventivo_details",
            description="Get detailed information about a specific preventivo including line items",
            category="preventivi",
            parameters=[
                ToolParameter(
                    name="preventivo_id",
                    type=ToolParameterType.INTEGER,
                    description="Preventivo ID",
                    required=True,
                ),
            ],
            func=get_preventivo_details,
            examples=["get_preventivo_details(preventivo_id=123)"],
            tags=["preventivo", "details", "quote"],
        ),
        Tool(
            name="create_preventivo",
            description="Create a new preventivo (quote/estimate) with line items",
            category="preventivi",
            parameters=[
                ToolParameter(
                    name="cliente_id",
                    type=ToolParameterType.INTEGER,
                    description="Client ID",
                    required=True,
                ),
                ToolParameter(
                    name="righe",
                    type=ToolParameterType.ARRAY,
                    description="List of line items (each with descrizione, quantita, prezzo_unitario, aliquota_iva, unita_misura)",
                    required=True,
                    items={
                        "type": "object",
                        "properties": {
                            "descrizione": {
                                "type": "string",
                                "description": "Line item description",
                            },
                            "quantita": {
                                "type": "number",
                                "description": "Quantity",
                            },
                            "prezzo_unitario": {
                                "type": "number",
                                "description": "Unit price",
                            },
                            "aliquota_iva": {
                                "type": "number",
                                "description": "VAT rate percentage (default 22.0)",
                            },
                            "unita_misura": {
                                "type": "string",
                                "description": "Unit of measure (default 'ore')",
                            },
                        },
                        "required": ["descrizione", "quantita", "prezzo_unitario"],
                    },
                ),
                ToolParameter(
                    name="validita_giorni",
                    type=ToolParameterType.INTEGER,
                    description="Validity period in days (default 30)",
                    required=False,
                    default=30,
                ),
                ToolParameter(
                    name="note",
                    type=ToolParameterType.STRING,
                    description="Optional notes",
                    required=False,
                ),
                ToolParameter(
                    name="condizioni",
                    type=ToolParameterType.STRING,
                    description="Optional terms and conditions",
                    required=False,
                ),
            ],
            func=create_preventivo,
            requires_confirmation=True,
            examples=[
                """create_preventivo(
                cliente_id=5,
                righe=[{"descrizione": "Web consulting", "quantita": 8, "prezzo_unitario": 80, "aliquota_iva": 22}],
                validita_giorni=30
            )"""
            ],
            tags=["create", "preventivo", "quote", "write"],
        ),
        Tool(
            name="update_preventivo_status",
            description="Update preventivo status (bozza, inviato, accettato, rifiutato, scaduto)",
            category="preventivi",
            parameters=[
                ToolParameter(
                    name="preventivo_id",
                    type=ToolParameterType.INTEGER,
                    description="Preventivo ID",
                    required=True,
                ),
                ToolParameter(
                    name="new_status",
                    type=ToolParameterType.STRING,
                    description="New status",
                    required=True,
                    enum=["bozza", "inviato", "accettato", "rifiutato", "scaduto"],
                ),
            ],
            func=update_preventivo_status,
            requires_confirmation=True,
            examples=[
                "update_preventivo_status(preventivo_id=123, new_status='inviato')",
                "update_preventivo_status(preventivo_id=456, new_status='accettato')",
            ],
            tags=["update", "preventivo", "status", "write"],
        ),
        Tool(
            name="update_preventivo",
            description="Update preventivo fields (note, condizioni, validita_giorni). Only BOZZA status can be edited.",
            category="preventivi",
            parameters=[
                ToolParameter(
                    name="preventivo_id",
                    type=ToolParameterType.INTEGER,
                    description="Preventivo ID",
                    required=True,
                ),
                ToolParameter(
                    name="note",
                    type=ToolParameterType.STRING,
                    description="Notes",
                    required=False,
                ),
                ToolParameter(
                    name="condizioni",
                    type=ToolParameterType.STRING,
                    description="Terms and conditions",
                    required=False,
                ),
                ToolParameter(
                    name="validita_giorni",
                    type=ToolParameterType.INTEGER,
                    description="Validity period in days (updates data_scadenza)",
                    required=False,
                ),
            ],
            func=update_preventivo,
            requires_confirmation=True,
            examples=[
                "update_preventivo(preventivo_id=123, note='Updated notes')",
                "update_preventivo(preventivo_id=456, validita_giorni=45)",
            ],
            tags=["update", "preventivo", "write"],
        ),
        Tool(
            name="delete_preventivo",
            description="CRITICAL: Delete preventivo from database. Only BOZZA status and non-converted preventivi can be deleted.",
            category="preventivi",
            parameters=[
                ToolParameter(
                    name="preventivo_id",
                    type=ToolParameterType.INTEGER,
                    description="Preventivo ID to delete",
                    required=True,
                ),
            ],
            func=delete_preventivo,
            requires_confirmation=True,
            examples=["delete_preventivo(preventivo_id=123)"],
            tags=["delete", "preventivo", "write", "critical"],
        ),
        Tool(
            name="convert_preventivo_to_invoice",
            description="CRITICAL: Convert preventivo to fattura (cannot be undone). Creates new invoice from quote.",
            category="preventivi",
            parameters=[
                ToolParameter(
                    name="preventivo_id",
                    type=ToolParameterType.INTEGER,
                    description="Preventivo ID to convert",
                    required=True,
                ),
            ],
            func=convert_preventivo_to_invoice,
            requires_confirmation=True,
            examples=["convert_preventivo_to_invoice(preventivo_id=123)"],
            tags=["convert", "preventivo", "invoice", "write", "critical"],
        ),
    ]
