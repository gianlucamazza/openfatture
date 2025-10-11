"""Event listeners for payment domain events."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from dataclasses import asdict

import structlog

from openfatture.utils.config import Settings, get_settings

from .events import InMemoryEventBus, PaymentEvent

logger = structlog.get_logger("payment_events")


def audit_log_listener(event: PaymentEvent) -> None:
    """Write payment events to the structured audit log."""
    logger.info(
        "payment_event",
        event_type=event.__class__.__name__,
        **asdict(event),
    )


def register_default_payment_listeners(event_bus: InMemoryEventBus) -> None:
    """Attach default listeners (audit logging) to the provided event bus."""
    existing = event_bus._listeners.get(PaymentEvent, [])  # type: ignore[attr-defined]
    if audit_log_listener not in existing:
        event_bus.subscribe(PaymentEvent, audit_log_listener)


def _import_listener(path: str) -> Callable[[PaymentEvent], object]:
    module_name, attr = path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    handler = getattr(module, attr)
    if not callable(handler):
        raise TypeError(f"Listener '{path}' is not callable")
    return handler


def create_event_bus(settings: Settings | None = None) -> InMemoryEventBus:
    """Create an event bus with default audit listener and optional custom listeners."""
    settings = settings or get_settings()
    bus = InMemoryEventBus()
    register_default_payment_listeners(bus)

    extra_listeners = (
        settings.payment_event_listeners.split(",") if settings.payment_event_listeners else []
    )
    for path in (listener.strip() for listener in extra_listeners):
        if not path:
            continue
        handler = _import_listener(path)
        bus.subscribe(PaymentEvent, handler)

    return bus
