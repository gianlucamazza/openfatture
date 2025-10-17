"""Tools for SDI (Sistema di Interscambio) notification management."""

from pathlib import Path
from typing import Any

from pydantic import validate_call

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
from openfatture.sdi.notifiche.processor import NotificationProcessor
from openfatture.storage.database.base import get_session
from openfatture.storage.database.models import Fattura, LogSDI, StatoFattura
from openfatture.utils.logging import get_logger
from openfatture.utils.security import validate_integer_input

logger = get_logger(__name__)


# =============================================================================
# READ Tools
# =============================================================================


@validate_call
def list_sdi_notifications(
    fattura_id: int | None = None,
    tipo_notifica: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """
    List SDI notifications with optional filters.

    Args:
        fattura_id: Filter by invoice ID (optional)
        tipo_notifica: Filter by notification type (RC/NS/MC/DT/AT/NE/EC) (optional)
        limit: Maximum results (default 20, max 100)

    Returns:
        Dictionary with notification list
    """
    # Validate inputs
    if fattura_id is not None:
        fattura_id = validate_integer_input(fattura_id, min_value=1)
    limit = validate_integer_input(limit, min_value=1, max_value=100)

    # Validate notification type
    valid_types = ["RC", "NS", "MC", "DT", "AT", "NE", "EC"]
    if tipo_notifica and tipo_notifica.upper() not in valid_types:
        return {
            "error": f"Invalid notification type: {tipo_notifica}. Valid: {', '.join(valid_types)}",
            "count": 0,
            "notifications": [],
        }

    db = get_session()
    try:
        # Build query
        query = db.query(LogSDI)

        if fattura_id:
            query = query.filter(LogSDI.fattura_id == fattura_id)

        if tipo_notifica:
            query = query.filter(LogSDI.tipo_notifica == tipo_notifica.upper())

        # Execute query with limit
        notifications = query.order_by(LogSDI.data_ricezione.desc()).limit(limit).all()

        # Format results
        results = []
        for n in notifications:
            results.append(
                {
                    "notification_id": n.id,
                    "fattura_id": n.fattura_id,
                    "fattura_numero": f"{n.fattura.numero}/{n.fattura.anno}" if n.fattura else None,
                    "tipo_notifica": n.tipo_notifica,
                    "tipo_descrizione": _get_notification_type_description(n.tipo_notifica),
                    "descrizione": n.descrizione,
                    "data_ricezione": n.data_ricezione.isoformat() if n.data_ricezione else None,
                    "xml_path": n.xml_path,
                }
            )

        return {
            "count": len(results),
            "notifications": results,
            "has_more": len(notifications) == limit,
        }

    except Exception as e:
        logger.error("list_sdi_notifications_failed", error=str(e))
        return {"error": str(e), "count": 0, "notifications": []}
    finally:
        db.close()


@validate_call
def get_sdi_notification_details(notification_id: int) -> dict[str, Any]:
    """
    Get detailed information about a specific SDI notification.

    Args:
        notification_id: Notification ID

    Returns:
        Dictionary with notification details
    """
    # Validate input
    notification_id = validate_integer_input(notification_id, min_value=1)

    db = get_session()
    try:
        notification = db.query(LogSDI).filter(LogSDI.id == notification_id).first()

        if not notification:
            return {"error": f"Notification {notification_id} not found"}

        # Get invoice details
        fattura_data = None
        if notification.fattura:
            f = notification.fattura
            fattura_data = {
                "fattura_id": f.id,
                "numero": f"{f.numero}/{f.anno}",
                "data_emissione": f.data_emissione.isoformat(),
                "stato": f.stato.value,
                "cliente": f.cliente.denominazione if f.cliente else None,
                "totale": float(f.totale),
            }

        # Read XML content if available
        xml_content = None
        if notification.xml_path:
            xml_path = Path(notification.xml_path)
            if xml_path.exists():
                try:
                    xml_content = xml_path.read_text(encoding="utf-8")
                except Exception as e:
                    xml_content = f"Error reading XML: {e}"

        return {
            "notification_id": notification.id,
            "tipo_notifica": notification.tipo_notifica,
            "tipo_descrizione": _get_notification_type_description(notification.tipo_notifica),
            "descrizione": notification.descrizione,
            "data_ricezione": (
                notification.data_ricezione.isoformat() if notification.data_ricezione else None
            ),
            "xml_path": notification.xml_path,
            "xml_content": xml_content,
            "fattura": fattura_data,
        }

    except Exception as e:
        logger.error(
            "get_sdi_notification_details_failed", notification_id=notification_id, error=str(e)
        )
        return {"error": str(e)}
    finally:
        db.close()


@validate_call
def check_invoice_sdi_status(fattura_id: int) -> dict[str, Any]:
    """
    Check SDI status for an invoice with notification history.

    Args:
        fattura_id: Invoice ID to check

    Returns:
        Dictionary with SDI status and notification history
    """
    # Validate input
    fattura_id = validate_integer_input(fattura_id, min_value=1)

    db = get_session()
    try:
        # Get invoice
        fattura = db.query(Fattura).filter(Fattura.id == fattura_id).first()

        if not fattura:
            return {"error": f"Fattura {fattura_id} not found"}

        # Get all notifications for this invoice
        notifications = (
            db.query(LogSDI)
            .filter(LogSDI.fattura_id == fattura_id)
            .order_by(LogSDI.data_ricezione.desc())
            .all()
        )

        # Format notification timeline
        timeline = []
        for n in notifications:
            timeline.append(
                {
                    "data": n.data_ricezione.isoformat() if n.data_ricezione else None,
                    "tipo": n.tipo_notifica,
                    "descrizione": _get_notification_type_description(n.tipo_notifica),
                    "messaggio": n.descrizione,
                }
            )

        # Determine overall SDI status
        sdi_status = _determine_sdi_status(fattura.stato, notifications)

        return {
            "fattura_id": fattura.id,
            "numero": f"{fattura.numero}/{fattura.anno}",
            "data_emissione": fattura.data_emissione.isoformat(),
            "stato_fattura": fattura.stato.value,
            "sdi_status": sdi_status,
            "notifications_count": len(notifications),
            "timeline": timeline,
            "latest_notification": timeline[0] if timeline else None,
        }

    except Exception as e:
        logger.error("check_invoice_sdi_status_failed", fattura_id=fattura_id, error=str(e))
        return {"error": str(e)}
    finally:
        db.close()


# =============================================================================
# WRITE Tools
# =============================================================================


@validate_call
def process_sdi_notification_file(
    xml_path: str,
    fattura_id: int | None = None,
) -> dict[str, Any]:
    """
    Process SDI notification XML file and update invoice status.

    This is a WRITE operation that updates invoice status based on notification.

    Args:
        xml_path: Path to SDI notification XML file
        fattura_id: Optional invoice ID to associate (for manual processing)

    Returns:
        Dictionary with processing result
    """
    # Validate inputs
    if fattura_id is not None:
        fattura_id = validate_integer_input(fattura_id, min_value=1)

    xml_file = Path(xml_path)
    if not xml_file.exists():
        return {"success": False, "error": f"File not found: {xml_path}"}

    if not xml_file.suffix.lower() == ".xml":
        return {"success": False, "error": "File must be an XML file"}

    db = get_session()
    try:
        # Create processor
        processor = NotificationProcessor(db_session=db, email_sender=None)

        # Process file
        success, error, notification = processor.process_file(xml_file)

        if not success:
            return {"success": False, "error": error}

        if notification is None:
            return {"success": False, "error": "No notification data returned"}

        # Get updated invoice info
        fattura = db.query(Fattura).filter(Fattura.id == fattura_id).first() if fattura_id else None

        if not fattura and notification:
            # Try to find invoice from notification
            fattura = processor._find_invoice(notification)

        logger.info(
            "sdi_notification_processed",
            xml_path=str(xml_file),
            tipo_notifica=notification.tipo if notification else None,
            fattura_id=fattura.id if fattura else None,
        )

        return {
            "success": True,
            "notification": {
                "tipo": notification.tipo if notification else None,
                "messaggio": notification.messaggio if notification else None,
                "data_ricezione": (
                    notification.data_ricezione.isoformat()
                    if notification and notification.data_ricezione
                    else None
                ),
            },
            "fattura": (
                {
                    "id": fattura.id,
                    "numero": f"{fattura.numero}/{fattura.anno}",
                    "stato": fattura.stato.value,
                }
                if fattura
                else None
            ),
            "message": f"Notification processed: {notification.tipo if notification else 'unknown'}",
        }

    except Exception as e:
        db.rollback()
        logger.error("process_sdi_notification_file_failed", xml_path=str(xml_file), error=str(e))
        return {"success": False, "error": str(e)}
    finally:
        db.close()


# =============================================================================
# Helper Functions
# =============================================================================


def _get_notification_type_description(tipo: str) -> str:
    """Get human-readable description for notification type."""
    descriptions = {
        "AT": "Attestazione di trasmissione - Invoice sent to SDI",
        "RC": "Ricevuta di consegna - Invoice delivered to recipient",
        "NS": "Notifica di scarto - Invoice rejected by SDI (validation errors)",
        "MC": "Mancata consegna - Delivery failed (recipient issue)",
        "NE": "Notifica di esito - Outcome notification from recipient",
        "DT": "Decorrenza termini - Deadline notification",
        "EC": "Esito committente - Recipient acceptance/rejection",
    }
    return descriptions.get(tipo.upper(), f"Unknown notification type: {tipo}")


def _determine_sdi_status(stato: StatoFattura, notifications: list[LogSDI]) -> str:
    """Determine overall SDI status from invoice status and notifications."""
    # Check for latest notification
    if not notifications:
        if stato == StatoFattura.DA_INVIARE:
            return "ready_to_send"
        elif stato == StatoFattura.INVIATA:
            return "sent_awaiting_response"
        elif stato == StatoFattura.BOZZA:
            return "draft"
        return "unknown"

    latest = notifications[0]

    # Determine status based on latest notification
    if latest.tipo_notifica == "RC":
        return "delivered_successfully"
    elif latest.tipo_notifica == "NS":
        return "rejected_validation_error"
    elif latest.tipo_notifica == "MC":
        return "delivery_failed"
    elif latest.tipo_notifica == "AT":
        return "transmitted_to_sdi"
    elif latest.tipo_notifica in ["NE", "EC"]:
        if "accettata" in latest.descrizione.lower() or "EC01" in latest.descrizione:
            return "accepted_by_recipient"
        elif "rifiutata" in latest.descrizione.lower() or "EC02" in latest.descrizione:
            return "rejected_by_recipient"
        return "outcome_received"
    elif latest.tipo_notifica == "DT":
        return "deadline_passed"

    return "processing"


# =============================================================================
# Tool Definitions
# =============================================================================


def get_sdi_tools() -> list[Tool]:
    """
    Get all SDI notification tools.

    Returns:
        List of Tool instances
    """
    return [
        Tool(
            name="list_sdi_notifications",
            description="List SDI notifications with optional filters (invoice, type)",
            category="sdi",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Filter by invoice ID (optional)",
                    required=False,
                ),
                ToolParameter(
                    name="tipo_notifica",
                    type=ToolParameterType.STRING,
                    description="Filter by notification type (RC/NS/MC/DT/AT/NE/EC)",
                    required=False,
                    enum=["RC", "NS", "MC", "DT", "AT", "NE", "EC"],
                ),
                ToolParameter(
                    name="limit",
                    type=ToolParameterType.INTEGER,
                    description="Maximum results (default 20)",
                    required=False,
                    default=20,
                ),
            ],
            func=list_sdi_notifications,
            examples=[
                "list_sdi_notifications()",
                "list_sdi_notifications(fattura_id=123)",
                "list_sdi_notifications(tipo_notifica='RC', limit=10)",
            ],
            tags=["sdi", "notifications", "search"],
        ),
        Tool(
            name="get_sdi_notification_details",
            description="Get detailed information about a specific SDI notification including XML content",
            category="sdi",
            parameters=[
                ToolParameter(
                    name="notification_id",
                    type=ToolParameterType.INTEGER,
                    description="Notification ID",
                    required=True,
                ),
            ],
            func=get_sdi_notification_details,
            examples=["get_sdi_notification_details(notification_id=5)"],
            tags=["sdi", "notifications", "details"],
        ),
        Tool(
            name="check_invoice_sdi_status",
            description="Check SDI status for an invoice with complete notification timeline",
            category="sdi",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID to check",
                    required=True,
                ),
            ],
            func=check_invoice_sdi_status,
            examples=["check_invoice_sdi_status(fattura_id=123)"],
            tags=["sdi", "status", "invoice"],
        ),
        Tool(
            name="process_sdi_notification_file",
            description="Process SDI notification XML file and update invoice status (WRITE operation)",
            category="sdi",
            parameters=[
                ToolParameter(
                    name="xml_path",
                    type=ToolParameterType.STRING,
                    description="Path to SDI notification XML file",
                    required=True,
                ),
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Optional invoice ID for manual association",
                    required=False,
                ),
            ],
            func=process_sdi_notification_file,
            requires_confirmation=True,
            examples=[
                "process_sdi_notification_file(xml_path='notifications/RC_IT01234567890_00001.xml')",
                "process_sdi_notification_file(xml_path='notifications/NS_IT01234567890_00001.xml', fattura_id=123)",
            ],
            tags=["sdi", "notifications", "process", "write"],
        ),
    ]
