"""Default event listeners and registration utilities.

Provides audit logging listener and utilities for loading custom listeners
from configuration.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from dataclasses import asdict
from typing import Any

import structlog

from openfatture.utils.config import Settings, get_settings

from .base import BaseEvent, GlobalEventBus, get_global_event_bus
from .persistence import EventPersistenceListener

logger = structlog.get_logger("event_listeners")

# Global persistence listener instance
_persistence_listener: EventPersistenceListener | None = None


def audit_log_listener(event: BaseEvent) -> None:
    """Write all events to structured audit log.

    This listener logs every event with full metadata for audit trails,
    debugging, and compliance.

    Args:
        event: The event to log
    """
    event_data = asdict(event)

    # Convert non-serializable types
    if "event_id" in event_data:
        event_data["event_id"] = str(event_data["event_id"])
    if "occurred_at" in event_data:
        event_data["occurred_at"] = event_data["occurred_at"].isoformat()

    logger.info(
        "domain_event",
        event_type=event.__class__.__name__,
        **event_data,
    )


def register_default_listeners(event_bus: GlobalEventBus | None = None) -> None:
    """Register default listeners (audit logging, persistence) to the event bus.

    Args:
        event_bus: Event bus instance. If None, uses global singleton.
    """
    global _persistence_listener

    event_bus = event_bus or get_global_event_bus()

    # Register audit logging for all events
    # Use BaseEvent to catch all event types (polymorphism)
    existing_handlers = [reg.handler for reg in event_bus._handlers.get(BaseEvent, [])]

    registered_listeners = []

    if audit_log_listener not in existing_handlers:
        event_bus.subscribe(BaseEvent, audit_log_listener, priority=-100)
        registered_listeners.append("audit_log_listener")

    # Register event persistence for database audit trail
    if _persistence_listener is None:
        _persistence_listener = EventPersistenceListener()

    # Check if persistence listener already registered
    persistence_registered = any(
        hasattr(reg.handler, "__self__")
        and isinstance(reg.handler.__self__, EventPersistenceListener)
        for reg in event_bus._handlers.get(BaseEvent, [])
    )

    if not persistence_registered:
        event_bus.subscribe(BaseEvent, _persistence_listener.handle_event, priority=-100)
        registered_listeners.append("event_persistence_listener")

    if registered_listeners:
        logger.info("default_listeners_registered", listeners=registered_listeners)


def _import_listener(path: str) -> Callable[[BaseEvent], Any]:
    """Import a listener function from a Python module path.

    Args:
        path: Dotted Python path (e.g., 'mymodule.my_listener')

    Returns:
        The listener function

    Raises:
        ImportError: If module or attribute not found
        TypeError: If imported object is not callable
    """
    try:
        module_name, attr_name = path.rsplit(".", 1)
    except ValueError:
        raise ImportError(f"Invalid listener path '{path}'. Expected format: 'module.function'")

    try:
        module = importlib.import_module(module_name)
    except ImportError as e:
        raise ImportError(f"Could not import module '{module_name}': {e}")

    if not hasattr(module, attr_name):
        raise ImportError(f"Module '{module_name}' has no attribute '{attr_name}'")

    handler = getattr(module, attr_name)

    if not callable(handler):
        raise TypeError(f"Listener '{path}' is not callable (type: {type(handler).__name__})")

    return handler


def load_custom_listeners(
    event_bus: GlobalEventBus | None = None,
    settings: Settings | None = None,
) -> int:
    """Load custom event listeners from configuration.

    Reads OPENFATTURE_EVENT_LISTENERS environment variable (comma-separated
    Python paths) and registers them with the event bus.

    Args:
        event_bus: Event bus instance. If None, uses global singleton.
        settings: Settings instance. If None, uses global settings.

    Returns:
        Number of listeners successfully loaded

    Example:
        # In .env file:
        OPENFATTURE_EVENT_LISTENERS=myapp.listeners.slack_notifier,myapp.listeners.metrics_tracker

        # Then:
        >>> load_custom_listeners()
        2
    """
    event_bus = event_bus or get_global_event_bus()
    settings = settings or get_settings()

    if not settings.event_listeners:
        logger.debug("no_custom_listeners_configured")
        return 0

    listener_paths = [path.strip() for path in settings.event_listeners.split(",") if path.strip()]

    loaded_count = 0
    for path in listener_paths:
        try:
            handler = _import_listener(path)
            event_bus.subscribe(BaseEvent, handler, priority=0)

            logger.info(
                "custom_listener_loaded",
                listener=path,
                handler=handler.__name__,
            )
            loaded_count += 1

        except Exception as e:
            logger.error(
                "custom_listener_load_failed",
                listener=path,
                error=str(e),
                error_type=type(e).__name__,
            )

    logger.info(
        "custom_listeners_loaded", total=loaded_count, failed=len(listener_paths) - loaded_count
    )

    return loaded_count


def initialize_event_system(settings: Settings | None = None) -> GlobalEventBus:
    """Initialize the global event system with default and custom listeners.

    This is the main entry point for setting up the event system during
    application startup.

    Args:
        settings: Settings instance. If None, uses global settings.

    Returns:
        The initialized GlobalEventBus instance

    Example:
        >>> # In cli/lifespan.py
        >>> event_bus = initialize_event_system()
    """
    settings = settings or get_settings()
    event_bus = get_global_event_bus()

    # Register default listeners (audit logging, persistence)
    register_default_listeners(event_bus)

    # Load custom listeners from config
    custom_count = load_custom_listeners(event_bus, settings)

    logger.info(
        "event_system_initialized",
        default_listeners=2,  # audit_log_listener + event_persistence_listener
        custom_listeners=custom_count,
    )

    return event_bus
