"""Fiscal helpers for the billing bounded context.

Deterministic tax/SDI rules live with compliance agents and SDI validation —
not in LLM free text. This package re-exports application report queries that
surface fiscal aggregates; it is not a place for silent mock rates.
"""

from openfatture.billing.application import report_queries

__all__ = ["report_queries"]
