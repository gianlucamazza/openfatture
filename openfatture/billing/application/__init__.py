"""Billing application services (use-case layer for tools and CLI).

AI tools must call these modules rather than opening SQLAlchemy sessions
directly.
"""

from openfatture.billing.application import (
    batch_ops,
    client_commands,
    client_queries,
    invoice_commands,
    invoice_queries,
    line_commands,
    preventivo_commands,
    preventivo_queries,
    prodotto_ops,
    report_queries,
)

__all__ = [
    "invoice_queries",
    "invoice_commands",
    "line_commands",
    "client_queries",
    "client_commands",
    "preventivo_queries",
    "preventivo_commands",
    "prodotto_ops",
    "batch_ops",
    "report_queries",
]
