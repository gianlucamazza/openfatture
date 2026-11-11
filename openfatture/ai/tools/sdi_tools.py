"""AI tool adapters over `openfatture.sdi.application.tool_ops`."""

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType, ToolRisk
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
            risk=ToolRisk.READ,
            description=(
                "List the SDI receipts that have been applied to invoices, newest first. "
                "Each entry has notification_id, fattura_id, fattura_numero, tipo_notifica "
                "with tipo_descrizione, descrizione (the SDI message), data_ricezione and "
                "xml_path; has_more=true means the limit was reached. Receipts that were "
                "imported but not applied (unmatched, duplicate, out of order, unparsable) "
                "are not listed; they appear in the `openfatture fattura sdi-journal` "
                "command. For the current SDI state of one invoice use "
                "check_invoice_sdi_status."
            ),
            category="sdi",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Only receipts of this invoice ID; all invoices when omitted",
                    required=False,
                ),
                ToolParameter(
                    name="tipo_notifica",
                    type=ToolParameterType.STRING,
                    description=(
                        "Only this receipt type: RC delivered, NS discarded by SDI, MC not "
                        "delivered, DT deadline passed, AT transmission certificate, NE/EC "
                        "recipient outcome; all types when omitted"
                    ),
                    required=False,
                    enum=["RC", "NS", "MC", "DT", "AT", "NE", "EC"],
                ),
                ToolParameter(
                    name="limit",
                    type=ToolParameterType.INTEGER,
                    description="Maximum entries returned, 1-100 (default 20)",
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
            risk=ToolRisk.READ,
            description=(
                "Details of one applied SDI receipt by the notification_id returned by "
                "list_sdi_notifications: tipo_notifica, tipo_descrizione, descrizione, "
                "data_ricezione, xml_path and the related invoice (fattura_id, numero, "
                "data_emissione, stato, cliente, totale). xml_content holds the file text "
                "only when xml_path is set and the file is readable, otherwise null. An "
                "unknown ID returns an error."
            ),
            category="sdi",
            parameters=[
                ToolParameter(
                    name="notification_id",
                    type=ToolParameterType.INTEGER,
                    description="notification_id from list_sdi_notifications (not an invoice ID)",
                    required=True,
                ),
            ],
            func=get_sdi_notification_details,
            examples=["get_sdi_notification_details(notification_id=5)"],
            tags=["sdi", "notifications", "details"],
        ),
        Tool(
            name="check_invoice_sdi_status",
            risk=ToolRisk.READ,
            description=(
                "SDI state of one invoice: stato_fattura, a derived sdi_status, "
                "notifications_count, the timeline of applied receipts (newest first: data, "
                "tipo, descrizione, messaggio) and latest_notification. sdi_status follows "
                "the latest receipt (delivered_successfully, rejected_validation_error, "
                "delivery_failed, transmitted_to_sdi, accepted_by_recipient, "
                "rejected_by_recipient, outcome_received, deadline_passed); without receipts "
                "it is draft, ready_to_send, sent_awaiting_response or unknown. It reads only "
                "the database; it does not query SDI or the PEC mailbox. An unknown invoice "
                "returns an error. Use it to answer whether an invoice was delivered or "
                "rejected; use process_sdi_notification_file only to import a new receipt file."
            ),
            category="sdi",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID (fattura_id)",
                    required=True,
                ),
            ],
            func=check_invoice_sdi_status,
            examples=["check_invoice_sdi_status(fattura_id=123)"],
            tags=["sdi", "status", "invoice"],
        ),
        Tool(
            name="process_sdi_notification_file",
            risk=ToolRisk.MUTATE,
            description=(
                "Import one SDI receipt XML file (RC, NS, MC, DT, AT, NE/EC) received from "
                "SDI: the receipt is stored as evidence, matched to its invoice by SDI "
                "identifier or by the submitted file name, and, when the transition is "
                "allowed, the invoice status, SDI number and delivery date are updated and "
                "a journal entry is added. Returns success, the notification (tipo, "
                "messaggio, data_ricezione) and the invoice (id, numero, stato). success=false "
                "with an error covers a missing or non-.xml file, an unparsable receipt, no "
                "matching invoice, an ambiguous or conflicting match, and outcomes such as "
                "out_of_order or conflict, where the invoice is left unchanged. Importing "
                "the same receipt again changes nothing. An unmatched receipt is resolved by "
                "a person with `openfatture fattura associate-receipt`, not by this tool. "
                "To read the state of an invoice use check_invoice_sdi_status instead."
            ),
            category="sdi",
            parameters=[
                ToolParameter(
                    name="xml_path",
                    type=ToolParameterType.STRING,
                    description="Path of the receipt .xml file, absolute or relative to the current directory",
                    required=True,
                ),
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description=(
                        "Invoice ID whose data is returned in the result when the receipt "
                        "is processed; it does not choose or force the association, which "
                        "always comes from the receipt"
                    ),
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
