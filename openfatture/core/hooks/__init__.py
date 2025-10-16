"""Hook system for OpenFatture.

Provides a flexible system for executing custom scripts (shell, Python) at
lifecycle events (invoice creation, AI commands, SDI notifications, etc.).

Architecture:
    - Models: HookConfig, HookResult, HookMetadata
    - Executor: Runs hook scripts with timeout, env vars, error handling
    - Registry: Discovers and manages hooks from ~/.openfatture/hooks/
    - Bridge: Connects events to hooks automatically

Example hook script (~/.openfatture/hooks/post-invoice-send.sh):
    #!/bin/bash
    # DESCRIPTION: Send Slack notification when invoice is sent
    # TIMEOUT: 15

    curl -X POST "$SLACK_WEBHOOK" \\
      -d "{\\"text\\": \\"Invoice ${OPENFATTURE_INVOICE_NUMBER} sent!\\"}"

Usage:
    >>> from openfatture.core.hooks import initialize_hook_system
    >>> from openfatture.core.events import get_global_event_bus
    >>>
    >>> # Initialize hook system (done automatically in lifespan)
    >>> event_bus = get_global_event_bus()
    >>> initialize_hook_system(event_bus)
    >>>
    >>> # Now hooks will execute automatically when events are published
    >>> event_bus.publish(InvoiceSentEvent(...))
    >>> # → post-invoice-send.sh executes automatically
"""

from __future__ import annotations

__all__ = [
    # Models
    "HookConfig",
    "HookResult",
    "HookMetadata",
    # Executor
    "HookExecutor",
    "HookExecutionError",
    # Registry
    "HookRegistry",
    "get_hook_registry",
    # Bridge
    "HookEventBridge",
    "initialize_hook_system",
    "get_hook_bridge",
]

from .executor import HookExecutionError, HookExecutor
from .listeners import HookEventBridge, get_hook_bridge, initialize_hook_system
from .models import HookConfig, HookMetadata, HookResult
from .registry import HookRegistry, get_hook_registry
