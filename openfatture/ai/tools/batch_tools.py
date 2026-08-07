"""AI tool adapters over `openfatture.billing.application.batch_ops`."""

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
from openfatture.billing.application.batch_ops import (
    bulk_update_invoices_status,
    export_clients_to_csv,
    export_invoices_to_csv,
    import_clients_from_csv,
    import_invoices_from_csv,
)


def get_batch_tools() -> list[Tool]:
    """
    Get all batch operation tools.

    Returns:
        List of Tool instances
    """
    return [
        Tool(
            name="export_invoices_to_csv",
            description="Export invoices to CSV file with optional filters (year, client)",
            category="batch",
            parameters=[
                ToolParameter(
                    name="output_path",
                    type=ToolParameterType.STRING,
                    description="Path to output CSV file",
                    required=True,
                ),
                ToolParameter(
                    name="anno",
                    type=ToolParameterType.INTEGER,
                    description="Filter by year (optional)",
                    required=False,
                ),
                ToolParameter(
                    name="cliente_id",
                    type=ToolParameterType.INTEGER,
                    description="Filter by client ID (optional)",
                    required=False,
                ),
                ToolParameter(
                    name="include_lines",
                    type=ToolParameterType.BOOLEAN,
                    description="Include invoice line items in separate rows",
                    required=False,
                    default=False,
                ),
            ],
            func=export_invoices_to_csv,
            examples=[
                "export_invoices_to_csv(output_path='invoices_2025.csv', anno=2025)",
                "export_invoices_to_csv(output_path='exports/all.csv', include_lines=True)",
            ],
            tags=["export", "csv", "batch", "invoice"],
        ),
        Tool(
            name="export_clients_to_csv",
            description="Export all clients to CSV file",
            category="batch",
            parameters=[
                ToolParameter(
                    name="output_path",
                    type=ToolParameterType.STRING,
                    description="Path to output CSV file",
                    required=True,
                ),
            ],
            func=export_clients_to_csv,
            examples=["export_clients_to_csv(output_path='clients.csv')"],
            tags=["export", "csv", "batch", "client"],
        ),
        Tool(
            name="import_invoices_from_csv",
            description="Import invoices from CSV file (creates new invoices as drafts)",
            category="batch",
            parameters=[
                ToolParameter(
                    name="csv_path",
                    type=ToolParameterType.STRING,
                    description="Path to CSV file to import",
                    required=True,
                ),
                ToolParameter(
                    name="default_cliente_id",
                    type=ToolParameterType.INTEGER,
                    description="Default client ID if not in CSV (optional)",
                    required=False,
                ),
            ],
            func=import_invoices_from_csv,
            requires_confirmation=True,
            examples=["import_invoices_from_csv(csv_path='invoices.csv')"],
            tags=["import", "csv", "batch", "invoice", "write"],
        ),
        Tool(
            name="import_clients_from_csv",
            description="Import clients from CSV file (creates new clients)",
            category="batch",
            parameters=[
                ToolParameter(
                    name="csv_path",
                    type=ToolParameterType.STRING,
                    description="Path to CSV file to import",
                    required=True,
                ),
            ],
            func=import_clients_from_csv,
            requires_confirmation=True,
            examples=["import_clients_from_csv(csv_path='clients.csv')"],
            tags=["import", "csv", "batch", "client", "write"],
        ),
        Tool(
            name="bulk_update_invoices_status",
            description="Bulk update invoice status for multiple invoices at once",
            category="batch",
            parameters=[
                ToolParameter(
                    name="anno",
                    type=ToolParameterType.INTEGER,
                    description="Year to filter invoices",
                    required=True,
                ),
                ToolParameter(
                    name="new_status",
                    type=ToolParameterType.STRING,
                    description="New status to set",
                    required=True,
                    enum=["bozza", "da_inviare", "inviata", "consegnata"],
                ),
                ToolParameter(
                    name="cliente_id",
                    type=ToolParameterType.INTEGER,
                    description="Optional client filter",
                    required=False,
                ),
            ],
            func=bulk_update_invoices_status,
            requires_confirmation=True,
            examples=[
                "bulk_update_invoices_status(anno=2024, new_status='da_inviare')",
                "bulk_update_invoices_status(anno=2025, new_status='consegnata', cliente_id=5)",
            ],
            tags=["bulk", "update", "invoice", "write"],
        ),
    ]
