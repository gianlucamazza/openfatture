"""AI tool adapters over `openfatture.billing.application.report_queries`."""

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType, ToolRisk
from openfatture.billing.application.report_queries import (
    generate_client_report,
    generate_vat_report,
    get_due_dates,
)


def get_report_tools() -> list[Tool]:
    """
    Get all report-related tools.

    Returns:
        List of Tool instances
    """
    return [
        Tool(
            name="generate_vat_report",
            risk=ToolRisk.READ,
            description=(
                "VAT (IVA) totals of the issued documents of one year or quarter. Returns "
                "year, period, invoices_count, total_imponibile, total_iva, total_revenue "
                "and by_vat_rate (vat_rate, imponibile, iva summed from the invoice lines). "
                "Every document except local drafts is counted (drafts issued elsewhere are "
                "included), whatever its SDI status, and credit notes (TD04) are added as "
                "positive amounts, not subtracted. The year is the invoice year; the "
                "quarter filters by issue-date month. An empty period returns zero totals "
                "with a message. For counts per invoice status use get_invoice_stats; for "
                "collected, outstanding and overdue amounts use generate_invoice_summary_pdf."
            ),
            category="reports",
            parameters=[
                ToolParameter(
                    name="anno",
                    type=ToolParameterType.INTEGER,
                    description="Invoice year, 2000-2100; the current year when omitted",
                    required=False,
                ),
                ToolParameter(
                    name="trimestre",
                    type=ToolParameterType.STRING,
                    description=(
                        "Quarter by issue month: Q1 Jan-Mar, Q2 Apr-Jun, Q3 Jul-Sep, "
                        "Q4 Oct-Dec; the whole year when omitted"
                    ),
                    required=False,
                    enum=["Q1", "Q2", "Q3", "Q4"],
                ),
            ],
            func=generate_vat_report,
            examples=[
                "generate_vat_report()",
                "generate_vat_report(anno=2025)",
                "generate_vat_report(anno=2025, trimestre='Q1')",
            ],
            tags=["report", "vat", "iva", "tax"],
        ),
        Tool(
            name="generate_client_report",
            risk=ToolRisk.READ,
            description=(
                "Ranking of clients by invoiced amount in one year. Returns year, "
                "clients_count, total_revenue and clients (rank, client_id, client_name, "
                "invoices_count, total_revenue), highest first. It counts every document "
                "except local drafts, whatever its SDI status, and adds credit notes (TD04) "
                "as positive amounts; it says nothing about collections. A year without "
                "documents returns an empty list with a message. For one client's invoices "
                "use search_invoices with cliente_id."
            ),
            category="reports",
            parameters=[
                ToolParameter(
                    name="anno",
                    type=ToolParameterType.INTEGER,
                    description="Invoice year, 2000-2100; the current year when omitted",
                    required=False,
                ),
                ToolParameter(
                    name="limit",
                    type=ToolParameterType.INTEGER,
                    description="Number of top clients to return, 1-100 (default 20)",
                    required=False,
                    default=20,
                ),
            ],
            func=generate_client_report,
            examples=[
                "generate_client_report()",
                "generate_client_report(anno=2025)",
                "generate_client_report(anno=2024, limit=10)",
            ],
            tags=["report", "clients", "revenue"],
        ),
        Tool(
            name="get_due_dates",
            risk=ToolRisk.READ,
            description=(
                "Open payment instalments of every year grouped by due date relative to "
                "today: overdue, due_soon (within window_days), upcoming (later) and "
                "without_due_date. Each entry has invoice_ref (numero/anno), client_name, "
                "due_date, days_delta (negative when overdue), residual, paid, total and "
                "status; the result also has total_outstanding, overdue_total, "
                "due_soon_total, upcoming_total and hidden_upcoming (upcoming entries left "
                "out by max_results). Only scheduled payments with a residual are listed: "
                "has_outstanding=false means none, not that every invoice is collected, "
                "since amounts without a payment schedule do not appear. For one invoice "
                "use get_payment_status."
            ),
            category="reports",
            parameters=[
                ToolParameter(
                    name="window_days",
                    type=ToolParameterType.INTEGER,
                    description=(
                        "Days from today, 1-365, within which an instalment counts as "
                        "due_soon (default 14)"
                    ),
                    required=False,
                    default=14,
                ),
                ToolParameter(
                    name="max_results",
                    type=ToolParameterType.INTEGER,
                    description=(
                        "Maximum upcoming entries returned, 1-100 (default 20); overdue "
                        "and due_soon are never truncated"
                    ),
                    required=False,
                    default=20,
                ),
            ],
            func=get_due_dates,
            examples=[
                "get_due_dates()",
                "get_due_dates(window_days=21)",
                "get_due_dates(window_days=7, max_results=10)",
            ],
            tags=["report", "payment", "due", "overdue"],
        ),
    ]
