"""Payment matching strategies using Strategy pattern.

This module implements fuzzy matching algorithms to reconcile bank transactions
with payment records. Uses the Strategy pattern for extensibility.

Available Strategies:
- ExactAmountMatcher: Perfect amount + date match (confidence 1.0)
- FuzzyDescriptionMatcher: Levenshtein similarity on textual fields
- IBANMatcher: IBAN detected in transaction metadata
- DateWindowMatcher: Amount + date within ±N days (confidence 0.6-0.8)
- CompositeMatcher: Weighted combination of the above signals

Usage:
    >>> from openfatture.payment.matchers import CompositeMatcher
    >>> matcher = CompositeMatcher()
    >>> results = matcher.match(transaction, payments)
    >>> best_match = max(results, key=lambda r: r.confidence)
"""

__all__ = [
    "IMatcherStrategy",
    "ExactAmountMatcher",
    "FuzzyDescriptionMatcher",
    "IBANMatcher",
    "DateWindowMatcher",
    "CompositeMatcher",
]

from .base import IMatcherStrategy
from .composite import CompositeMatcher
from .date_window import DateWindowMatcher
from .exact import ExactAmountMatcher
from .fuzzy import FuzzyDescriptionMatcher
from .iban import IBANMatcher
