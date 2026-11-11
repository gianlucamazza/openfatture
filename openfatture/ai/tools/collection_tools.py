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
        "Consult collection receipts, available money, allocations, reversals and owner statements.",
        "Record one manual receipt; optionally allocate it to an invoice/installment. Unknown date is allowed. Reuse request_id for retries.",
        "Allocate available receipt money explicitly to an invoice, optionally an installment. Reuse request_id for retries.",
        "Reverse an original allocation with audit reason. Does not refund money. Reuse request_id for retries.",
        "Record an owner declaration (not_settled or unknown), separately from money amounts.",
    ]
    functions.extend([api.record_bank_collection, api.allocate_collection_batch])
    descriptions.extend(
        [
            "Register an imported incoming EUR bank movement as an available receipt; transaction_id is a UUID string.",
            "Atomically allocate a receipt across invoices. allocations_json is an array of objects with invoice_id, amount and optional payment_id. Reuse request_id for retries.",
        ]
    )
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
                    description=name,
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
