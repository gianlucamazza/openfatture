"""Client use-cases for the billing bounded context.

Re-exports the application-layer client queries and commands. AI tools and
other callers should import from here or from ``billing.application`` —
never open SQLAlchemy sessions in the tool layer.
"""

from openfatture.billing.application import client_commands, client_queries

__all__ = ["client_queries", "client_commands"]
