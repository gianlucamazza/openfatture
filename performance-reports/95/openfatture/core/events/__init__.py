"""Global event system for OpenFatture.

This module provides a domain event system that extends across all modules
(invoices, AI, SDI, payments, batch operations) enabling loose coupling and
extensibility through the Observer pattern.

The event system supports:
- Synchronous and asynchronous event handlers
- Priority-based handler execution
- Event filtering by type
- Structured logging and audit trails
- Custom event listeners via configuration

Example:
    >>> from openfatture.core.events import GlobalEventBus, InvoiceCreatedEvent
    >>> event_bus = GlobalEventBus()
    >>> event_bus.subscribe(InvoiceCreatedEvent, my_handler)
    >>> event_bus.publish(InvoiceCreatedEvent(invoice_id=123, ...))

Architecture:
    This extends the payment event pattern (openfatture/payment/application/events.py)
    to provide a global, unified event system across all domains.
"""

from __future__ import annotations

__all__ = [
    # Base
    "BaseEvent",
    "EventBus",
    "GlobalEventBus",
    "get_global_event_bus",
    # Invoice events
    "InvoiceCreatedEvent",
    "InvoiceSentEvent",
    "InvoiceValidatedEvent",
    "InvoiceDeletedEvent",
    # Client events
    "ClientCreatedEvent",
    "ClientUpdatedEvent",
    "ClientDeletedEvent",
    # AI events
    "AICommandStartedEvent",
    "AICommandCompletedEvent",
    # SDI events
    "SDINotificationReceivedEvent",
    # Batch events
    "BatchImportStartedEvent",
    "BatchImportCompletedEvent",
    # Listeners
    "register_default_listeners",
    "audit_log_listener",
    "initialize_event_system",
    # Analytics
    "EventAnalytics",
]

from .ai_events import AICommandCompletedEvent, AICommandStartedEvent
from .analytics import EventAnalytics
from .base import BaseEvent, EventBus, GlobalEventBus, get_global_event_bus
from .batch_events import BatchImportCompletedEvent, BatchImportStartedEvent
from .client_events import ClientCreatedEvent, ClientDeletedEvent, ClientUpdatedEvent
from .invoice_events import (
    InvoiceCreatedEvent,
    InvoiceDeletedEvent,
    InvoiceSentEvent,
    InvoiceValidatedEvent,
)
from .listeners import audit_log_listener, initialize_event_system, register_default_listeners
from .sdi_events import SDINotificationReceivedEvent
