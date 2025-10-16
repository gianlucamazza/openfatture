"""Integration tests for the hook system.

Tests the full flow from event publishing to hook execution,
including the HookEventBridge, HookRegistry, and HookExecutor.
"""

import json
from decimal import Decimal
from textwrap import dedent

import pytest

from openfatture.core.events.base import BaseEvent, GlobalEventBus
from openfatture.core.events.invoice_events import InvoiceCreatedEvent, InvoiceSentEvent
from openfatture.core.hooks.executor import HookExecutor
from openfatture.core.hooks.listeners import HookEventBridge
from openfatture.core.hooks.registry import HookRegistry


@pytest.fixture
def temp_hooks_dir(tmp_path):
    """Create a temporary hooks directory for tests."""
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    return hooks_dir


@pytest.fixture
def event_bus():
    """Create a fresh event bus for integration tests."""
    return GlobalEventBus()


@pytest.fixture
def registry(temp_hooks_dir):
    """Create a HookRegistry instance."""
    return HookRegistry(hooks_dir=temp_hooks_dir)


@pytest.fixture
def executor(temp_hooks_dir):
    """Create a HookExecutor instance."""
    return HookExecutor(hooks_dir=temp_hooks_dir)


@pytest.fixture
def hook_bridge(event_bus, registry, executor):
    """Create a HookEventBridge connecting all components."""
    bridge = HookEventBridge(executor=executor, registry=registry)
    bridge.register(event_bus)
    return bridge


@pytest.fixture
def invoice_create_hook(temp_hooks_dir):
    """Create a hook for invoice creation."""
    script_path = temp_hooks_dir / "post-invoice-create.sh"
    script_path.write_text(
        dedent(
            """\
            #!/bin/bash
            # DESCRIPTION: Invoice creation hook
            echo "Invoice ${OPENFATTURE_INVOICE_NUMBER} created"
            echo "Total: ${OPENFATTURE_TOTAL_AMOUNT} ${OPENFATTURE_CURRENCY}"
            """
        )
    )
    script_path.chmod(0o755)


@pytest.fixture
def invoice_send_hook(temp_hooks_dir):
    """Create a hook for invoice sending."""
    script_path = temp_hooks_dir / "post-invoice-send.sh"
    script_path.write_text(
        dedent(
            """\
            #!/bin/bash
            # DESCRIPTION: Invoice send hook
            echo "Invoice sent to ${OPENFATTURE_RECIPIENT}"
            """
        )
    )
    script_path.chmod(0o755)


@pytest.fixture
def env_check_hook(temp_hooks_dir):
    """Create a hook that outputs all event data as JSON."""
    script_path = temp_hooks_dir / "on-invoice-create.py"
    script_path.write_text(
        dedent(
            """\
            #!/usr/bin/env python3
            import os
            import json

            # Output all OPENFATTURE_* env vars to validate injection
            env_vars = {k: v for k, v in os.environ.items() if k.startswith('OPENFATTURE_')}
            print(json.dumps(env_vars, indent=2))
            """
        )
    )
    script_path.chmod(0o755)


@pytest.fixture
def failing_hook(temp_hooks_dir):
    """Create a hook that always fails."""
    # Use "on-invoice-send" to match InvoiceSentEvent pattern
    script_path = temp_hooks_dir / "on-invoice-send.sh"
    script_path.write_text(
        dedent(
            """\
            #!/bin/bash
            # DESCRIPTION: Failing hook for error isolation test
            echo "This hook will fail" >&2
            exit 1
            """
        )
    )
    script_path.chmod(0o755)


def test_event_triggers_hook(event_bus, hook_bridge, invoice_create_hook, temp_hooks_dir, registry):
    """Test that publishing an event triggers the corresponding hook."""
    # Reload registry to discover the hook
    registry.reload()

    # Create and publish invoice created event
    event = InvoiceCreatedEvent(
        invoice_id=123,
        invoice_number="001/2025",
        client_id=1,
        client_name="Acme Corp",
        total_amount=Decimal("1000.00"),
        currency="EUR",
    )

    # Publish event (should trigger hook via bridge)
    event_bus.publish(event)

    # Hook should have been executed
    # We can't directly inspect the result in this test because HookEventBridge
    # doesn't expose results, but we can verify the hook was discovered
    hooks = registry.get_hooks_for_event("InvoiceCreatedEvent")
    assert len(hooks) == 1
    assert hooks[0].name == "post-invoice-create"


def test_multiple_hooks_for_event(
    event_bus, hook_bridge, invoice_create_hook, env_check_hook, temp_hooks_dir, registry
):
    """Test that multiple hooks are triggered by a single event."""
    # Reload registry to discover both hooks
    registry.reload()

    # Both post-invoice-create and on-invoice-create should be discovered
    hooks = registry.get_hooks_for_event("InvoiceCreatedEvent")
    assert len(hooks) == 2

    hook_names = {h.name for h in hooks}
    assert "post-invoice-create" in hook_names
    assert "on-invoice-create" in hook_names

    # Publish event
    event = InvoiceCreatedEvent(
        invoice_id=123,
        invoice_number="001/2025",
        client_id=1,
        client_name="Acme Corp",
        total_amount=Decimal("1000.00"),
    )

    # Both hooks should be executed (we can't verify execution directly,
    # but we've confirmed they're discovered and enabled)
    event_bus.publish(event)


def test_hook_env_vars_populated(executor, env_check_hook, temp_hooks_dir, registry):
    """Test that event data is correctly injected as environment variables."""
    # Reload registry to discover the hook
    registry.reload()

    # Get the hook config
    hook_config = registry.get_hook("on-invoice-create")
    assert hook_config is not None

    # Create event
    event = InvoiceCreatedEvent(
        invoice_id=123,
        invoice_number="001/2025",
        client_id=1,
        client_name="Acme Corp",
        total_amount=Decimal("1500.50"),
        currency="EUR",
    )

    # Execute hook directly
    result = executor.execute_hook(hook_config, event)

    # Hook should succeed
    assert result.success is True

    # Parse JSON output to verify env vars
    env_vars = json.loads(result.stdout)

    # Verify standard env vars
    assert env_vars["OPENFATTURE_HOOK_NAME"] == "on-invoice-create"
    assert env_vars["OPENFATTURE_EVENT_TYPE"] == "InvoiceCreatedEvent"
    assert "OPENFATTURE_EVENT_ID" in env_vars
    assert "OPENFATTURE_EVENT_TIME" in env_vars

    # Verify event-specific env vars
    assert env_vars["OPENFATTURE_INVOICE_ID"] == "123"
    assert env_vars["OPENFATTURE_INVOICE_NUMBER"] == "001/2025"
    assert env_vars["OPENFATTURE_CLIENT_ID"] == "1"
    assert env_vars["OPENFATTURE_CLIENT_NAME"] == "Acme Corp"
    assert env_vars["OPENFATTURE_TOTAL_AMOUNT"] == "1500.50"
    assert env_vars["OPENFATTURE_CURRENCY"] == "EUR"

    # Verify EVENT_DATA JSON
    event_data = json.loads(env_vars["OPENFATTURE_EVENT_DATA"])
    assert event_data["invoice_id"] == 123
    assert event_data["invoice_number"] == "001/2025"
    assert event_data["total_amount"] == "1500.50"


def test_hook_bridge_error_isolation(
    executor, invoice_send_hook, failing_hook, temp_hooks_dir, registry
):
    """Test that one hook failure doesn't affect others."""
    # Reload registry to discover both hooks
    registry.reload()

    # Both hooks should be discovered
    hooks = registry.get_hooks_for_event("InvoiceSentEvent")
    assert len(hooks) == 2

    # Create event
    event = InvoiceSentEvent(
        invoice_id=123,
        invoice_number="001/2025",
        recipient="0000000",
        pec_address="sdi01@pec.fatturapa.it",
        xml_path="/path/to/invoice.xml",
        signed=False,
    )

    # Execute both hooks manually to verify error isolation
    # (HookEventBridge also handles errors, but we test executor directly)
    results = []
    for hook_config in hooks:
        result = executor.execute_hook(hook_config, event)
        results.append(result)

    # One hook should succeed, one should fail
    success_count = sum(1 for r in results if r.success)
    failure_count = sum(1 for r in results if not r.success)

    assert success_count == 1
    assert failure_count == 1

    # Verify the failing hook has the correct error
    failing_result = next(r for r in results if not r.success)
    assert failing_result.exit_code == 1
    assert "This hook will fail" in failing_result.stderr


def test_hook_bridge_registers_as_listener(event_bus, hook_bridge):
    """Test that HookEventBridge correctly registers as an event listener."""
    # The bridge should have subscribed to BaseEvent
    # (it listens to all events via BaseEvent)

    # Check that BaseEvent has handlers registered
    assert BaseEvent in event_bus._handlers
    handlers = event_bus._handlers[BaseEvent]

    # Find the hook bridge handler
    hook_bridge_handlers = [h for h in handlers if h.handler == hook_bridge.handle_event]
    assert len(hook_bridge_handlers) == 1

    # Verify priority (set to -50 in register method)
    assert hook_bridge_handlers[0].priority == -50


def test_end_to_end_flow(
    event_bus, hook_bridge, invoice_create_hook, temp_hooks_dir, registry, executor
):
    """Test complete end-to-end flow: event → bridge → executor → result."""
    # Reload registry
    registry.reload()

    # Verify hook is discovered
    hooks = registry.get_hooks_for_event("InvoiceCreatedEvent")
    assert len(hooks) == 1
    assert hooks[0].name == "post-invoice-create"

    # Create event
    event = InvoiceCreatedEvent(
        invoice_id=456,
        invoice_number="002/2025",
        client_id=2,
        client_name="Test Client SRL",
        total_amount=Decimal("2500.00"),
        currency="EUR",
    )

    # Publish event via event bus (will trigger hook via bridge)
    event_bus.publish(event)

    # We can't directly verify the hook execution result via the bridge,
    # but we can execute the hook manually to verify it would work
    hook_config = registry.get_hook("post-invoice-create")
    result = executor.execute_hook(hook_config, event)

    # Hook should succeed
    assert result.success is True
    assert "Invoice 002/2025 created" in result.stdout
    assert "Total: 2500.00 EUR" in result.stdout


def test_disabled_hooks_not_executed(
    event_bus, hook_bridge, invoice_create_hook, temp_hooks_dir, registry
):
    """Test that disabled hooks are not executed."""
    # Reload registry
    registry.reload()

    # Verify hook is discovered
    hooks = registry.get_hooks_for_event("InvoiceCreatedEvent")
    assert len(hooks) == 1

    # Disable the hook
    registry.disable_hook("post-invoice-create")

    # Now no hooks should be returned
    hooks = registry.get_hooks_for_event("InvoiceCreatedEvent")
    assert len(hooks) == 0

    # Publishing event should not trigger any hooks
    event = InvoiceCreatedEvent(
        invoice_id=123,
        invoice_number="001/2025",
        client_id=1,
        client_name="Acme Corp",
        total_amount=Decimal("1000.00"),
    )

    event_bus.publish(event)
    # (No assertion needed - just verify no exceptions are raised)
