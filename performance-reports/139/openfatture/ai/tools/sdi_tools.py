"""AI tool adapters over `openfatture.sdi.application.tool_ops`."""

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
from openfatture.sdi.application.tool_ops import (
    check_invoice_sdi_status,
    get_sdi_notification_details,
    list_sdi_notifications,
    process_sdi_notification_file,
)


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
