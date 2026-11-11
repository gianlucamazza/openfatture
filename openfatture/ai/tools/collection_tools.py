"""Money ledger tools; write operations require the registry's human gate."""

import inspect
from collections.abc import Callable
from typing import Any

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType, ToolRisk
from openfatture.payment.application import collection_api as api


def get_collection_tools() -> list[Tool]:
    functions: list[Callable[..., Any]] = [
        api.get_collections,
        api.record_collection,
        api.allocate_collection,
        api.reverse_collection,
        api.declare_collection_status,
    ]
    descriptions = [
        "Read the collection ledger, the source of truth for money received. Returns receipts "
        "(id, amount, allocated, available, origin manual, bank or opening, date), entries "
        "(allocations with id, receipt_id, invoice_id, payment_id, amount, reverses_id and "
        "notes; a reversal has a negative amount and reverses_id set) and statements (owner "
        "declarations with id, invoice_id, value, source and declared_on). Amounts are EUR "
        "decimal strings. With invoice_id only that invoice's entries and statements and the "
        "receipts allocated to it are returned; without it the whole ledger is returned, "
        "unpaginated, including receipts with money still available. Use get_payment_status "
        "for a per-invoice summary with installments.",
        "Record money received outside a bank import as a manual receipt and, when invoice_id "
        "is given, allocate the whole amount to that invoice or one of its installments. "
        "Returns receipt_id, amount, allocated and available. The call is atomic: when the "
        "allocation fails (amount above the invoice or installment balance, unknown invoice, "
        "installment of another invoice) nothing is recorded. For money in an imported bank "
        "statement use record_bank_collection instead, so the same money is not counted twice. "
        "Repeating a request_id with the same parameters returns the first result without "
        "recording again; reusing it with different parameters is an error.",
        "Allocate part or all of a receipt's available money to an invoice, optionally to one "
        "of its installments, and return entry_id. Fails when the amount exceeds the "
        "receipt's available amount, the invoice's remaining balance or the installment's "
        "balance, when the installment belongs to another invoice, or when the receipt or "
        "invoice does not exist. To split one receipt across several invoices in one atomic "
        "step use allocate_collection_batch. Repeating a request_id with the same parameters "
        "returns the first result.",
        "Reverse all or part of an allocation entry, making that money available on its "
        "receipt again, and return entry_id of the new negative entry. It corrects the ledger "
        "and does not refund money to anyone. Only original positive allocations can be "
        "reversed, and the reversals of one entry cannot exceed its amount; installment "
        "balances and the status of a linked bank movement are updated. Repeating a request_id "
        "with the same parameters returns the first result.",
        "Record an owner declaration about an invoice's settlement, kept apart from money "
        "amounts: not_settled (the owner states it is unpaid) or unknown (the owner does not "
        "know). It records no receipt and changes no balance; it appears in get_collections "
        "statements and as collection_statement in get_payment_status. Returns statement_id. "
        "Fails for an unknown invoice, any other value or an empty source. Repeating a "
        "request_id with the same parameters returns the first result.",
    ]
    functions.extend([api.record_bank_collection, api.allocate_collection_batch])
    descriptions.extend(
        [
            "Register an imported bank movement as a bank receipt in the collection ledger so "
            "its money can be allocated with allocate_collection or allocate_collection_batch. "
            "Returns receipt_id, amount and available. Only positive (incoming) movements on EUR "
            "accounts are accepted; registering a movement that already has a receipt returns "
            "that receipt. It allocates nothing; for the one-step case of a movement paying one "
            "installment use reconcile_payment.",
            "Allocate one receipt across several invoices in a single transaction: every "
            "allocation is applied or none is. Each allocation is checked as in "
            "allocate_collection and together they cannot exceed the receipt's available "
            "amount. Returns entry_ids, ordered by invoice_id. Repeating a request_id with the "
            "same parameters returns the first result.",
        ]
    )
    request_id = (
        "Idempotency key chosen by the caller, up to 64 characters, not starting with "
        "'ledger:'; reuse the same value when retrying the same operation"
    )
    amount = "Amount in EUR as a positive decimal string, dot separator, up to 2 decimals"
    parameter_descriptions: dict[str, dict[str, str]] = {
        "get_collections": {
            "invoice_id": "Invoice to restrict the ledger to; omit for the whole ledger",
        },
        "record_collection": {
            "amount": amount,
            "request_id": request_id,
            "invoice_id": (
                "Invoice to allocate the whole amount to; omit to keep the receipt available "
                "for a later allocate_collection"
            ),
            "payment_id": "Installment of invoice_id to credit; requires invoice_id",
            "effective_date": (
                "Date the money was received, YYYY-MM-DD; omit when unknown and the receipt "
                "stays undated"
            ),
            "notes": "Free-text note stored on the receipt",
        },
        "allocate_collection": {
            "receipt_id": "Receipt id from get_collections, record_collection or "
            "record_bank_collection",
            "invoice_id": "Invoice receiving the allocation",
            "amount": amount,
            "request_id": request_id,
            "payment_id": (
                "Installment of invoice_id to credit; omit to allocate to the invoice without "
                "an installment"
            ),
        },
        "reverse_collection": {
            "entry_id": (
                "Id of the original allocation entry to reverse, from get_collections entries "
                "(positive amount, reverses_id null)"
            ),
            "amount": amount + "; at most the part of the entry not yet reversed",
            "reason": "Non-empty audit reason stored on the reversal entry",
            "request_id": request_id,
        },
        "declare_collection_status": {
            "invoice_id": "Invoice the declaration is about",
            "value": "not_settled or unknown; any other value is rejected",
            "source": "Non-empty provenance of the declaration, such as who stated it",
            "request_id": request_id,
            "declared_on": "Date of the declaration, YYYY-MM-DD; omit when unknown",
            "notes": "Free-text note stored on the declaration",
        },
        "record_bank_collection": {
            "transaction_id": "Bank movement UUID, the transaction_id from "
            "search_bank_transactions",
            "request_id": request_id,
        },
        "allocate_collection_batch": {
            "receipt_id": "Receipt id from get_collections, record_collection or "
            "record_bank_collection",
            "allocations_json": (
                "Non-empty JSON array encoded as a string; each object has invoice_id "
                "(integer), amount (EUR decimal string with up to 2 decimals) and optional "
                "payment_id (an installment of that invoice)"
            ),
            "request_id": request_id,
        },
    }
    tools = []
    for function, description in zip(functions, descriptions, strict=True):
        parameters = []
        for name, parameter in inspect.signature(function).parameters.items():
            parameters.append(
                ToolParameter(
                    name=name,
                    type=ToolParameterType.INTEGER
                    if name.endswith("_id") and name not in {"request_id", "transaction_id"}
                    else ToolParameterType.STRING,
                    description=parameter_descriptions[function.__name__][name],
                    required=parameter.default is inspect.Parameter.empty,
                )
            )
        reads = function is api.get_collections
        tools.append(
            Tool(
                name=function.__name__,
                risk=ToolRisk.READ if reads else ToolRisk.MUTATE,
                description=description,
                category="payments",
                parameters=parameters,
                func=function,
                requires_confirmation=not reads,
                tags=["read"] if reads else ["write", "collection"],
            )
        )
    return tools
