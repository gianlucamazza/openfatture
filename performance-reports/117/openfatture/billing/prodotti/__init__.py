"""Product catalog use-cases for the billing bounded context.

Re-exports application-layer product operations (search, CRUD). Prefer these
over raw storage models in assistant tools.
"""

from openfatture.billing.application import prodotto_ops

__all__ = ["prodotto_ops"]
