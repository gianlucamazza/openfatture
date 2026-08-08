"""AI tool adapters over `openfatture.payment.application.tool_ops`."""

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
from openfatture.payment.application.tool_ops import (
    create_manual_payment,
    delete_payment,
    get_payment_stats,
    get_payment_status,
    import_bank_transactions,
    reconcile_payment,
    search_bank_transactions,
    search_payments,
    update_payment,
)


def get_payment_tools() -> list[Tool]:
    """
    Get all payment-related tools.

    Returns:
        List of Tool instances
    """
    return [
        Tool(
            name="get_payment_status",
            description="Get payment status and details for an invoice",
            category="payments",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID",
                    required=True,
                ),
            ],
            func=get_payment_status,
            examples=["get_payment_status(fattura_id=123)"],
            tags=["payment", "status"],
        ),
        Tool(
            name="search_payments",
            description="Search for payments with optional status filter",
            category="payments",
            parameters=[
                ToolParameter(
                    name="stato",
                    type=ToolParameterType.STRING,
                    description="Filter by status",
                    required=False,
                    enum=["da_pagare", "pagato_parziale", "pagato", "scaduto"],
                ),
                ToolParameter(
                    name="limit",
                    type=ToolParameterType.INTEGER,
                    description="Maximum number of results",
                    required=False,
                    default=20,
                ),
            ],
            func=search_payments,
            examples=[
                "search_payments()",
                "search_payments(stato='da_pagare', limit=10)",
            ],
            tags=["search", "payment"],
        ),
        Tool(
            name="search_bank_transactions",
            description="Search bank transactions by description or status",
            category="payments",
            parameters=[
                ToolParameter(
                    name="description",
                    type=ToolParameterType.STRING,
                    description="Search in transaction description",
                    required=False,
                ),
                ToolParameter(
                    name="status",
                    type=ToolParameterType.STRING,
                    description="Filter by status",
                    required=False,
                    enum=["unmatched", "matched", "ignored"],
                ),
                ToolParameter(
                    name="limit",
                    type=ToolParameterType.INTEGER,
                    description="Maximum number of results",
                    required=False,
                    default=20,
                ),
            ],
            func=search_bank_transactions,
            examples=[
                "search_bank_transactions(status='unmatched')",
                "search_bank_transactions(description='Bonifico', limit=10)",
            ],
            tags=["search", "bank", "transaction"],
        ),
        Tool(
            name="get_payment_stats",
            description="Get payment statistics (counts, amounts by status, overdue)",
            category="payments",
            parameters=[],
            func=get_payment_stats,
            examples=["get_payment_stats()"],
            tags=["stats", "analytics", "payment"],
        ),
        Tool(
            name="reconcile_payment",
            description="Manually reconcile a bank transaction to a payment. Requires transaction_id (UUID) and payment_id.",
            category="payments",
            parameters=[
                ToolParameter(
                    name="transaction_id",
                    type=ToolParameterType.STRING,
                    description="Bank transaction ID (UUID format)",
                    required=True,
                ),
                ToolParameter(
                    name="payment_id",
                    type=ToolParameterType.INTEGER,
                    description="Payment ID to match",
                    required=True,
                ),
                ToolParameter(
                    name="match_type",
                    type=ToolParameterType.STRING,
                    description="Type of match (default: manual)",
                    required=False,
                    enum=["manual", "exact", "fuzzy", "iban", "date_window"],
                    default="manual",
                ),
                ToolParameter(
                    name="confidence",
                    type=ToolParameterType.NUMBER,
                    description="Match confidence 0.0-1.0 (optional)",
                    required=False,
                ),
            ],
            func=reconcile_payment,
            requires_confirmation=True,
            examples=[
                "reconcile_payment(transaction_id='uuid-here', payment_id=123)",
                "reconcile_payment(transaction_id='uuid', payment_id=456, match_type='fuzzy', confidence=0.85)",
            ],
            tags=["write", "reconcile", "payment"],
        ),
        Tool(
            name="create_manual_payment",
            description="Manually create a payment record for an invoice. Used for manual payment tracking.",
            category="payments",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Invoice ID",
                    required=True,
                ),
                ToolParameter(
                    name="importo",
                    type=ToolParameterType.NUMBER,
                    description="Total amount due",
                    required=True,
                ),
                ToolParameter(
                    name="data_scadenza",
                    type=ToolParameterType.STRING,
                    description="Due date (YYYY-MM-DD)",
                    required=True,
                ),
                ToolParameter(
                    name="importo_pagato",
                    type=ToolParameterType.NUMBER,
                    description="Amount already paid (default 0)",
                    required=False,
                    default=0.0,
                ),
                ToolParameter(
                    name="data_pagamento",
                    type=ToolParameterType.STRING,
                    description="Payment date if already paid (YYYY-MM-DD)",
                    required=False,
                ),
                ToolParameter(
                    name="modalita",
                    type=ToolParameterType.STRING,
                    description="Payment method (default 'bonifico')",
                    required=False,
                    default="bonifico",
                ),
            ],
            func=create_manual_payment,
            requires_confirmation=True,
            examples=[
                "create_manual_payment(fattura_id=123, importo=1000, data_scadenza='2025-02-15')",
                "create_manual_payment(fattura_id=456, importo=500, data_scadenza='2025-03-01', importo_pagato=500, data_pagamento='2025-01-20')",
            ],
            tags=["write", "create", "payment"],
        ),
        Tool(
            name="update_payment",
            description="Update payment record details (amount, dates, payment method). Automatically recalculates status.",
            category="payments",
            parameters=[
                ToolParameter(
                    name="payment_id",
                    type=ToolParameterType.INTEGER,
                    description="Payment ID",
                    required=True,
                ),
                ToolParameter(
                    name="importo",
                    type=ToolParameterType.NUMBER,
                    description="Total amount due",
                    required=False,
                ),
                ToolParameter(
                    name="importo_pagato",
                    type=ToolParameterType.NUMBER,
                    description="Amount paid",
                    required=False,
                ),
                ToolParameter(
                    name="data_scadenza",
                    type=ToolParameterType.STRING,
                    description="Due date (YYYY-MM-DD)",
                    required=False,
                ),
                ToolParameter(
                    name="data_pagamento",
                    type=ToolParameterType.STRING,
                    description="Payment date (YYYY-MM-DD)",
                    required=False,
                ),
                ToolParameter(
                    name="modalita",
                    type=ToolParameterType.STRING,
                    description="Payment method",
                    required=False,
                ),
            ],
            func=update_payment,
            requires_confirmation=True,
            examples=[
                "update_payment(payment_id=5, importo_pagato=500)",
                "update_payment(payment_id=10, data_pagamento='2025-01-25', modalita='contanti')",
            ],
            tags=["write", "update", "payment"],
        ),
        Tool(
            name="delete_payment",
            description="CRITICAL: Delete payment record from database. Cannot delete if linked to bank transactions.",
            category="payments",
            parameters=[
                ToolParameter(
                    name="payment_id",
                    type=ToolParameterType.INTEGER,
                    description="Payment ID to delete",
                    required=True,
                ),
            ],
            func=delete_payment,
            requires_confirmation=True,
            examples=["delete_payment(payment_id=5)"],
            tags=["write", "delete", "payment", "critical"],
        ),
        Tool(
            name="import_bank_transactions",
            description="Import bank transactions from OFX/QFX bank statement file for payment reconciliation.",
            category="payments",
            parameters=[
                ToolParameter(
                    name="file_path",
                    type=ToolParameterType.STRING,
                    description="Path to OFX/QFX bank statement file",
                    required=True,
                ),
                ToolParameter(
                    name="account_name",
                    type=ToolParameterType.STRING,
                    description="Bank account name (default 'Main Account')",
                    required=False,
                    default="Main Account",
                ),
            ],
            func=import_bank_transactions,
            requires_confirmation=True,
            examples=[
                "import_bank_transactions(file_path='/path/to/statement.ofx')",
                "import_bank_transactions(file_path='/path/to/statement.qfx', account_name='Business Account')",
            ],
            tags=["write", "import", "bank", "transaction"],
        ),
    ]
