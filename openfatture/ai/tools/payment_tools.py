"""AI tool adapters over `openfatture.payment.application.tool_ops`."""

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType, ToolRisk
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
            risk=ToolRisk.READ,
            description=(
                "Return how much of one invoice has been collected: invoice_number, total_amount, "
                "payment_status (no_payment_record, unpaid, partially_paid or fully_paid), "
                "amount_paid, outstanding, unscheduled_amount (part of the total not covered by "
                "installments), collection_statement (latest owner declaration or null) and "
                "payments, the installments with payment_id, importo, importo_pagato, "
                "saldo_residuo, stato, data_scadenza, data_pagamento, modalita and overdue. "
                "amount_paid includes ledger allocations made without an installment. "
                "no_payment_record means nothing is recorded, not that the invoice is unpaid. Use "
                "search_payments to list installments across invoices and get_collections for the "
                "receipts and allocations behind these amounts. Returns an error when the invoice "
                "does not exist."
            ),
            category="payments",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Numeric invoice id",
                    required=True,
                ),
            ],
            func=get_payment_status,
            examples=["get_payment_status(fattura_id=123)"],
            tags=["payment", "status"],
        ),
        Tool(
            name="search_payments",
            risk=ToolRisk.READ,
            description=(
                "List payment installments (scadenze) across all invoices, latest due date first. "
                "Each row has payment_id, fattura_id, invoice_number, cliente, importo, "
                "importo_pagato, saldo_residuo, stato, data_scadenza, data_pagamento, modalita "
                "and overdue; the result also has count and has_more. stato is the stored "
                "installment status and can lag behind the calendar, so rely on overdue for "
                "current lateness. Use get_payment_status for the full picture of a single "
                "invoice, including money allocated without an installment."
            ),
            category="payments",
            parameters=[
                ToolParameter(
                    name="stato",
                    type=ToolParameterType.STRING,
                    description=(
                        "Stored installment status to keep: da_pagare (nothing received), "
                        "pagato_parziale, pagato or scaduto; omit for all"
                    ),
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
            risk=ToolRisk.READ,
            description=(
                "List imported bank movements, newest first. Each row has transaction_id (UUID), "
                "account_id, account_name, date, amount in EUR (positive incoming, negative "
                "outgoing), description, reference, counterparty, status, matched_payment_id, "
                "match_confidence and match_type; the result also has count and has_more. "
                "Movements that are only partly allocated have status partially_matched. Use the "
                "transaction_id "
                "with reconcile_payment or record_bank_collection."
            ),
            category="payments",
            parameters=[
                ToolParameter(
                    name="description",
                    type=ToolParameterType.STRING,
                    description=(
                        "Case-insensitive substring of the movement description; omit for all"
                    ),
                    required=False,
                ),
                ToolParameter(
                    name="status",
                    type=ToolParameterType.STRING,
                    description=(
                        "unmatched (not allocated), partially_matched, matched (fully allocated) "
                        "or ignored; omit for all statuses"
                    ),
                    required=False,
                    enum=["unmatched", "partially_matched", "matched", "ignored"],
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
            risk=ToolRisk.READ,
            description=(
                "Return totals over all payment installments: by_status (count per stored "
                "status), total_payments, total_amount_due, total_amount_paid, total_outstanding, "
                "overdue_count and overdue_amount (installments past their due date and not in "
                "status pagato), all over installments only; outstanding_without_installments is "
                "what no installment covers (for example invoices without installments), and "
                "invoices_outstanding is the whole amount still to be collected. Amounts are EUR "
                "floats. Use get_due_dates for the outstanding amounts by invoice and due date."
            ),
            category="payments",
            parameters=[],
            func=get_payment_stats,
            examples=["get_payment_stats()"],
            tags=["stats", "analytics", "payment"],
        ),
        Tool(
            name="reconcile_payment",
            risk=ToolRisk.MUTATE,
            description=(
                "Allocate an imported bank movement to one installment through the collection "
                "ledger. It registers the movement as a bank receipt when needed, then allocates "
                "the smaller of the receipt's available amount and the installment's "
                "saldo_residuo, updating the installment and setting the movement to matched or "
                "partially_matched. Only incoming EUR movements in status unmatched or "
                "partially_matched and installments not yet fully paid are accepted; otherwise, "
                "or when either id does not exist, it returns an error. Returns transaction_id, "
                "payment_id, status, match_type and match_confidence. Each call allocates again "
                "while money remains available. To split one movement across invoices, or "
                "allocate to an invoice without installments, use record_bank_collection followed "
                "by allocate_collection or allocate_collection_batch."
            ),
            category="payments",
            parameters=[
                ToolParameter(
                    name="transaction_id",
                    type=ToolParameterType.STRING,
                    description=(
                        "Bank movement UUID, the transaction_id from search_bank_transactions"
                    ),
                    required=True,
                ),
                ToolParameter(
                    name="payment_id",
                    type=ToolParameterType.INTEGER,
                    description=(
                        "Installment id (payment_id from get_payment_status or search_payments)"
                    ),
                    required=True,
                ),
                ToolParameter(
                    name="match_type",
                    type=ToolParameterType.STRING,
                    description=(
                        "How the match was found, stored as metadata only (default manual, "
                        "for a match chosen by the user)"
                    ),
                    required=False,
                    enum=["manual", "exact", "fuzzy", "iban", "date_window"],
                    default="manual",
                ),
                ToolParameter(
                    name="confidence",
                    type=ToolParameterType.NUMBER,
                    description=(
                        "Confidence from 0.0 to 1.0 stored as metadata; omit for a user-chosen "
                        "match"
                    ),
                    required=False,
                ),
            ],
            func=reconcile_payment,
            requires_confirmation=True,
            examples=[
                "reconcile_payment(transaction_id='uuid-here', payment_id=123)",
                "reconcile_payment(transaction_id='uuid', payment_id=456, match_type='fuzzy', "
                "confidence=0.85)",
            ],
            tags=["write", "reconcile", "payment"],
        ),
        Tool(
            name="create_manual_payment",
            risk=ToolRisk.MUTATE,
            description=(
                "Add a payment installment (scadenza) to an invoice and return payment_id, "
                "fattura_id, importo, importo_pagato, saldo_residuo and stato. The installments "
                "of an invoice cannot add up to more than its total. When importo_pagato is above "
                "0 it also records a manual receipt in the collection ledger and allocates it to "
                "the new installment. Returns an error for an unknown invoice or an invalid "
                "amount. Each call creates a new installment, so a retry creates a duplicate. To "
                "record money received against an existing invoice or installment use "
                "record_collection, the ledger tool for receipts."
            ),
            category="payments",
            parameters=[
                ToolParameter(
                    name="fattura_id",
                    type=ToolParameterType.INTEGER,
                    description="Numeric invoice id the installment belongs to",
                    required=True,
                ),
                ToolParameter(
                    name="importo",
                    type=ToolParameterType.NUMBER,
                    description="Installment amount in EUR, positive, up to 2 decimals",
                    required=True,
                ),
                ToolParameter(
                    name="data_scadenza",
                    type=ToolParameterType.STRING,
                    description=(
                        "Due date YYYY-MM-DD as stated on the invoice or by the user; omit "
                        "when unknown and the installment has no due date"
                    ),
                    required=False,
                ),
                ToolParameter(
                    name="importo_pagato",
                    type=ToolParameterType.NUMBER,
                    description=(
                        "EUR already received for this installment, from 0 to importo, up "
                        "to 2 decimals (default 0); above 0 it records a manual ledger receipt"
                    ),
                    required=False,
                    default=0.0,
                ),
                ToolParameter(
                    name="data_pagamento",
                    type=ToolParameterType.STRING,
                    description=(
                        "Date the money was received, YYYY-MM-DD; used only when "
                        "importo_pagato is above 0, as the receipt date"
                    ),
                    required=False,
                ),
                ToolParameter(
                    name="modalita",
                    type=ToolParameterType.STRING,
                    description=(
                        "Payment method label stored on the installment, free text such as "
                        "bonifico, contanti or carta (default bonifico)"
                    ),
                    required=False,
                    default="bonifico",
                ),
            ],
            func=create_manual_payment,
            requires_confirmation=True,
            examples=[
                "create_manual_payment(fattura_id=123, importo=1000, data_scadenza='2025-02-15')",
                "create_manual_payment(fattura_id=456, importo=500, data_scadenza='2025-03-01', "
                "importo_pagato=500, data_pagamento='2025-01-20')",
            ],
            tags=["write", "create", "payment"],
        ),
        Tool(
            name="update_payment",
            risk=ToolRisk.MUTATE,
            description=(
                "Change an installment and return its importo, importo_pagato, saldo_residuo and "
                "recalculated stato. importo_pagato is the cumulative amount received: raising it "
                "records a manual receipt and allocation for the difference, lowering it reverses "
                "manual allocations newest first. Allocations that came from bank movements "
                "cannot be lowered this way; use reverse_collection on their entries. importo "
                "cannot go below the amount already received, nor push the invoice's installments "
                "above the invoice total. Because importo_pagato is a target total, repeating the "
                "same call does not record money twice. Returns an error when the installment "
                "does not exist or a check fails."
            ),
            category="payments",
            parameters=[
                ToolParameter(
                    name="payment_id",
                    type=ToolParameterType.INTEGER,
                    description=(
                        "Installment id (payment_id from get_payment_status or search_payments)"
                    ),
                    required=True,
                ),
                ToolParameter(
                    name="importo",
                    type=ToolParameterType.NUMBER,
                    description="New installment amount in EUR, positive, up to 2 decimals",
                    required=False,
                ),
                ToolParameter(
                    name="importo_pagato",
                    type=ToolParameterType.NUMBER,
                    description=(
                        "New cumulative EUR received for the installment, from 0 to importo, "
                        "up to 2 decimals"
                    ),
                    required=False,
                ),
                ToolParameter(
                    name="data_scadenza",
                    type=ToolParameterType.STRING,
                    description="New due date YYYY-MM-DD; an empty string clears it",
                    required=False,
                ),
                ToolParameter(
                    name="data_pagamento",
                    type=ToolParameterType.STRING,
                    description=(
                        "Payment date YYYY-MM-DD stored on the installment and used as the "
                        "receipt date when importo_pagato rises; an empty string clears it"
                    ),
                    required=False,
                ),
                ToolParameter(
                    name="modalita",
                    type=ToolParameterType.STRING,
                    description="New payment method label, free text",
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
            risk=ToolRisk.MUTATE,
            description=(
                "Permanently delete an installment that has no collection history and return "
                "payment_id. Irreversible. Refused when the installment has an amount received, "
                "any ledger entry (reversed allocations still count) or a linked bank movement; "
                "returns an error when it does not exist."
            ),
            category="payments",
            parameters=[
                ToolParameter(
                    name="payment_id",
                    type=ToolParameterType.INTEGER,
                    description="Installment id to delete",
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
            risk=ToolRisk.MUTATE,
            description=(
                "Import an OFX or QFX bank statement into the named bank account, creating the "
                "account (currency EUR) when it does not exist. Movements whose bank reference "
                "(FITID) is already stored for that account are skipped. Returns account_id, "
                "account_name, imported, skipped and total_transactions. Imported movements "
                "settle nothing by themselves; allocate them with reconcile_payment or "
                "record_bank_collection. Returns an error when the file does not exist, has "
                "another extension or cannot be parsed."
            ),
            category="payments",
            parameters=[
                ToolParameter(
                    name="file_path",
                    type=ToolParameterType.STRING,
                    description=(
                        "Path to a .ofx or .qfx file, absolute or relative to the current "
                        "working directory"
                    ),
                    required=True,
                ),
                ToolParameter(
                    name="account_name",
                    type=ToolParameterType.STRING,
                    description=(
                        "Bank account to import into, matched by exact name and created when "
                        "missing (default Main Account)"
                    ),
                    required=False,
                    default="Main Account",
                ),
            ],
            func=import_bank_transactions,
            requires_confirmation=True,
            examples=[
                "import_bank_transactions(file_path='/path/to/statement.ofx')",
                "import_bank_transactions(file_path='/path/to/statement.qfx', "
                "account_name='Business Account')",
            ],
            tags=["write", "import", "bank", "transaction"],
        ),
    ]
