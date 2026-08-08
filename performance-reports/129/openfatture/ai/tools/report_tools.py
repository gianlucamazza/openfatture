"""AI tool adapters over `openfatture.billing.application.report_queries`."""

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
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
            description="Generate VAT (IVA) report for a year or quarter. Returns imponibile, IVA, revenue totals and breakdown by VAT rate.",
            category="reports",
            parameters=[
                ToolParameter(
                    name="anno",
                    type=ToolParameterType.INTEGER,
                    description="Year (current year if not specified)",
                    required=False,
                ),
                ToolParameter(
                    name="trimestre",
                    type=ToolParameterType.STRING,
                    description="Quarter (Q1, Q2, Q3, Q4) - full year if not specified",
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
            description="Generate client revenue report (top clients by revenue for a year)",
            category="reports",
            parameters=[
                ToolParameter(
                    name="anno",
                    type=ToolParameterType.INTEGER,
                    description="Year (current year if not specified)",
                    required=False,
                ),
                ToolParameter(
                    name="limit",
                    type=ToolParameterType.INTEGER,
                    description="Maximum number of clients to return (default 20)",
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
            description="Get overdue and upcoming payment due dates. Returns overdue, due soon (within window), and upcoming payments.",
            category="reports",
            parameters=[
                ToolParameter(
                    name="window_days",
                    type=ToolParameterType.INTEGER,
                    description='Number of days to consider "due soon" (default 14)',
                    required=False,
                    default=14,
                ),
                ToolParameter(
                    name="max_results",
                    type=ToolParameterType.INTEGER,
                    description="Maximum number of upcoming payments to return (default 20)",
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
