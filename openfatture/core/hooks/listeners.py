"""Hook-event bridge listeners.

Connects the event system to the hook execution system, automatically
triggering hooks when matching events are published.
"""

from __future__ import annotations

import structlog

from openfatture.core.events.base import BaseEvent, GlobalEventBus, get_global_event_bus

from .executor import HookExecutionError, HookExecutor
from .registry import HookRegistry, get_hook_registry

logger = structlog.get_logger("hooks.listeners")


class HookEventBridge:
    """Bridges events to hook execution.

    Listens to all events and automatically executes matching hooks
    when events are published to the event bus.

    Example:
        >>> bridge = HookEventBridge()
        >>> bridge.register(event_bus)
        >>> # Now when InvoiceCreatedEvent is published,
        >>> # post-invoice-create.sh will be executed automatically
    """

    def __init__(
        self,
        executor: HookExecutor | None = None,
        registry: HookRegistry | None = None,
    ):
        """Initialize hook-event bridge.

        Args:
            executor: Hook executor instance (creates new if None)
            registry: Hook registry instance (uses global if None)
        """
        self.executor = executor or HookExecutor()
        self.registry = registry or get_hook_registry()

        logger.info(
            "hook_event_bridge_initialized",
            hooks_dir=str(self.registry.hooks_dir),
            hook_count=len(self.registry.list_hooks()),
        )

    def register(self, event_bus: GlobalEventBus | None = None) -> None:
        """Register bridge as event listener on the event bus.

        Args:
            event_bus: Event bus instance (uses global if None)
        """
        event_bus = event_bus or get_global_event_bus()
        event_bus.subscribe(BaseEvent, self.handle_event, priority=-50)
        logger.info("hook_event_bridge_registered")

    def handle_event(self, event: BaseEvent) -> None:
        """Handle event by executing matching hooks.

        This is called automatically when events are published to the bus.

        Args:
            event: The event to handle
        """
        event_name = event.__class__.__name__

        # Find matching hooks
        hooks = self.registry.get_hooks_for_event(event_name)

        if not hooks:
            logger.debug("no_matching_hooks", event_type=event_name)
            return

        logger.info(
            "executing_hooks_for_event",
            event_type=event_name,
            hook_count=len(hooks),
            hooks=[h.name for h in hooks],
        )

        # Execute each matching hook
        for hook_config in hooks:
            try:
                result = self.executor.execute_hook(hook_config, event)

                if result.success:
                    logger.info(
                        "hook_succeeded",
                        hook=hook_config.name,
                        event_type=event_name,
                        duration_ms=result.duration_ms,
                    )
                else:
                    logger.warning(
                        "hook_failed",
                        hook=hook_config.name,
                        event_type=event_name,
                        exit_code=result.exit_code,
                        error=result.error,
                        stderr=result.stderr[:200],  # Truncate for logging
                    )

            except HookExecutionError as e:
                # Hook failed with fail_on_error=True
                logger.error(
                    "hook_execution_error_critical",
                    hook=hook_config.name,
                    event_type=event_name,
                    error=str(e),
                )
                # Re-raise to potentially halt the triggering operation
                raise

            except Exception as e:
                # Unexpected error - log but don't halt
                logger.error(
                    "hook_execution_exception",
                    hook=hook_config.name,
                    event_type=event_name,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )


# Global bridge instance
_bridge: HookEventBridge | None = None


def initialize_hook_system(event_bus: GlobalEventBus | None = None) -> HookEventBridge:
    """Initialize the hook system and register with event bus.

    This is the main entry point for setting up the hook system.

    Args:
        event_bus: Event bus instance (uses global if None)

    Returns:
        HookEventBridge instance

    Example:
        >>> # In cli/lifespan.py
        >>> bridge = initialize_hook_system()
    """
    global _bridge

    if _bridge is None:
        _bridge = HookEventBridge()

    event_bus = event_bus or get_global_event_bus()
    _bridge.register(event_bus)

    logger.info(
        "hook_system_initialized",
        registered_hooks=len(_bridge.registry.list_hooks(enabled_only=True)),
    )

    return _bridge


def get_hook_bridge() -> HookEventBridge | None:
    """Get the global hook bridge instance.

    Returns:
        HookEventBridge instance if initialized, None otherwise
    """
    return _bridge
