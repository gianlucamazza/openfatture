"""Datetime utilities for consistent timezone-aware timestamps."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return current time as timezone-aware UTC datetime."""
    return datetime.now(UTC)
