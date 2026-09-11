"""Nota di credito tools — thin adapter over billing.application.nota_credito_ops."""

from openfatture.billing.application.nota_credito_ops import (
    create_nota_credito_from_fattura,
)

__all__ = [
    "create_nota_credito_from_fattura",
]
