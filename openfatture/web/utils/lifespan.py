"""Lifespan management utilities for OpenFatture Web UI.

Provides access to shared resources initialized at application startup.
"""

from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openfatture.core.events import GlobalEventBus
    from openfatture.core.hooks import HookEventBridge

# Context variables to hold shared resources
_event_bus_context: ContextVar["GlobalEventBus | None"] = ContextVar(
    "_event_bus_context", default=None
)

_hook_bridge_context: ContextVar["HookEventBridge | None"] = ContextVar(
    "_hook_bridge_context", default=None
)


def set_event_bus(event_bus: "GlobalEventBus") -> None:
    """Set the global event bus for the web application."""
    _event_bus_context.set(event_bus)


def get_event_bus() -> "GlobalEventBus | None":
    """Get the global event bus for the web application."""
    return _event_bus_context.get()


def set_hook_bridge(hook_bridge: "HookEventBridge") -> None:
    """Set the hook bridge for the web application."""
    _hook_bridge_context.set(hook_bridge)


def get_hook_bridge() -> "HookEventBridge | None":
    """Get the hook bridge for the web application."""
    return _hook_bridge_context.get()
