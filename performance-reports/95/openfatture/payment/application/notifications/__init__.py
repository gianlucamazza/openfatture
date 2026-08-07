"""Notification system for payment reminders.

Provides abstraction for sending notifications via multiple channels (email, SMS, etc.)
following the Strategy pattern.
"""

__all__ = [
    "INotifier",
    "EmailNotifier",
    "ConsoleNotifier",
    "CompositeNotifier",
    "SMTPConfig",
]

from .notifier import (
    CompositeNotifier,
    ConsoleNotifier,
    EmailNotifier,
    INotifier,
    SMTPConfig,
)
