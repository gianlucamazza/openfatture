"""Payment matching strategies using Strategy pattern.

This module implements fuzzy matching algorithms to reconcile bank transactions
with payment records. Uses the Strategy pattern for extensibility.

Available Strategies:
- ExactAmountMatcher: Perfect amount + date match (confidence 1.0)
- FuzzyStringMatcher: Levenshtein distance >85% (confidence 0.7-0.95)
- IBANMatcher: IBAN found in reference field (confidence 0.9)
- DateWindowMatcher: Amount + date within ±7 days (confidence 0.6-0.8)
- CompositeMatcher: Weighted combination (confidence varies)

Usage:
    >>> from openfatture.payment.matchers import CompositeMatcher
    >>> matcher = CompositeMatcher()
    >>> results = matcher.match(transaction, payments)
    >>> best_match = max(results, key=lambda r: r.confidence)
"""

__all__ = [
    "IMatcherStrategy",
    "ExactAmountMatcher",
    "FuzzyStringMatcher",
    "IBANMatcher",
    "DateWindowMatcher",
    "CompositeMatcher",
]

from .base import IMatcherStrategy
from .composite import CompositeMatcher
from .date_window import DateWindowMatcher
from .exact import ExactAmountMatcher
from .fuzzy import FuzzyStringMatcher
from .iban import IBANMatcher
