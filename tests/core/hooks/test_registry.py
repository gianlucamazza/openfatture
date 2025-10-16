"""Unit tests for HookRegistry."""

from textwrap import dedent

import pytest

from openfatture.core.hooks.registry import HookRegistry, get_hook_registry


@pytest.fixture
def temp_hooks_dir(tmp_path):
    """Create a temporary hooks directory for tests."""
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    return hooks_dir


@pytest.fixture
def registry(temp_hooks_dir):
    """Create a HookRegistry instance for testing."""
    return HookRegistry(hooks_dir=temp_hooks_dir)


@pytest.fixture
def sample_hooks(temp_hooks_dir):
    """Create sample hook scripts for testing."""
    # Create post-invoice-create.sh
    (temp_hooks_dir / "post-invoice-create.sh").write_text(
        dedent(
            """\
            #!/bin/bash
            # DESCRIPTION: Invoice creation hook
            # TIMEOUT: 15
            echo "Invoice created"
            """
        )
    )

    # Create post-invoice-send.py
    (temp_hooks_dir / "post-invoice-send.py").write_text(
        dedent(
            """\
            #!/usr/bin/env python3
            # DESCRIPTION: Invoice send hook
            # TIMEOUT: 30
            print("Invoice sent")
            """
        )
    )

    # Create pre-ai-command.sh
    (temp_hooks_dir / "pre-ai-command.sh").write_text(
        dedent(
            """\
            #!/bin/bash
            # DESCRIPTION: Pre AI command hook
            echo "AI command starting"
            """
        )
    )

    # Create on-sdi-notification.sh
    (temp_hooks_dir / "on-sdi-notification.sh").write_text(
        dedent(
            """\
            #!/bin/bash
            echo "SDI notification received"
            """
        )
    )

    # Create non-hook file (should be ignored)
    (temp_hooks_dir / "README.md").write_text("This is a README")

    # Create hidden file (should be ignored)
    (temp_hooks_dir / ".hidden-hook.sh").write_text("#!/bin/bash\necho hidden")


def test_hook_discovery(temp_hooks_dir, sample_hooks):
    """Test that .sh and .py files are discovered in hooks directory."""
    registry = HookRegistry(hooks_dir=temp_hooks_dir)

    # Should discover 4 hooks (.sh and .py), not README.md or hidden files
    hooks = registry.list_hooks()

    assert len(hooks) == 4

    hook_names = {h.name for h in hooks}
    assert "post-invoice-create" in hook_names
    assert "post-invoice-send" in hook_names
    assert "pre-ai-command" in hook_names
    assert "on-sdi-notification" in hook_names

    # README.md and hidden file should not be discovered
    assert "README" not in hook_names
    assert ".hidden-hook" not in hook_names


def test_hook_metadata_parsing(temp_hooks_dir, sample_hooks):
    """Test that hook metadata is parsed from script comments."""
    registry = HookRegistry(hooks_dir=temp_hooks_dir)

    # Check that DESCRIPTION and TIMEOUT are parsed
    invoice_create_hook = registry.get_hook("post-invoice-create")
    assert invoice_create_hook is not None
    assert invoice_create_hook.description == "Invoice creation hook"
    assert invoice_create_hook.timeout_seconds == 15

    invoice_send_hook = registry.get_hook("post-invoice-send")
    assert invoice_send_hook is not None
    assert invoice_send_hook.description == "Invoice send hook"
    assert invoice_send_hook.timeout_seconds == 30

    # Hook without timeout metadata should use default (30)
    ai_command_hook = registry.get_hook("pre-ai-command")
    assert ai_command_hook is not None
    assert ai_command_hook.timeout_seconds == 30


def test_get_hooks_for_event(temp_hooks_dir, sample_hooks):
    """Test that get_hooks_for_event() maps events to hooks correctly."""
    registry = HookRegistry(hooks_dir=temp_hooks_dir)

    # InvoiceCreatedEvent should match post-invoice-create
    hooks = registry.get_hooks_for_event("InvoiceCreatedEvent")
    assert len(hooks) == 1
    assert hooks[0].name == "post-invoice-create"

    # InvoiceSentEvent should match post-invoice-send
    hooks = registry.get_hooks_for_event("InvoiceSentEvent")
    assert len(hooks) == 1
    assert hooks[0].name == "post-invoice-send"

    # AICommandStartedEvent should match pre-ai-command
    hooks = registry.get_hooks_for_event("AICommandStartedEvent")
    assert len(hooks) == 1
    assert hooks[0].name == "pre-ai-command"

    # SDINotificationReceivedEvent should match on-sdi-notification
    hooks = registry.get_hooks_for_event("SDINotificationReceivedEvent")
    assert len(hooks) == 1
    assert hooks[0].name == "on-sdi-notification"

    # Event with no matching hooks
    hooks = registry.get_hooks_for_event("PaymentMatchedEvent")
    assert len(hooks) == 0


def test_event_name_to_pattern_conversion(registry):
    """Test that event names are correctly converted to hook patterns."""
    # InvoiceCreatedEvent → post-invoice-create, on-invoice-create
    patterns = registry._event_to_hook_patterns("InvoiceCreatedEvent")
    assert "post-invoice-create" in patterns
    assert "on-invoice-create" in patterns

    # InvoiceSentEvent → post-invoice-send, on-invoice-send
    patterns = registry._event_to_hook_patterns("InvoiceSentEvent")
    assert "post-invoice-send" in patterns
    assert "on-invoice-send" in patterns

    # InvoiceDeletedEvent → post-invoice-delete, on-invoice-delete
    patterns = registry._event_to_hook_patterns("InvoiceDeletedEvent")
    assert "post-invoice-delete" in patterns
    assert "on-invoice-delete" in patterns

    # AICommandStartedEvent → pre-ai-command, on-ai-command-start
    patterns = registry._event_to_hook_patterns("AICommandStartedEvent")
    assert "pre-ai-command" in patterns
    assert "on-ai-command-start" in patterns

    # AICommandCompletedEvent → post-ai-command, on-ai-command-complete
    patterns = registry._event_to_hook_patterns("AICommandCompletedEvent")
    assert "post-ai-command" in patterns
    assert "on-ai-command-complete" in patterns


def test_camel_to_kebab_conversion(registry):
    """Test CamelCase to kebab-case conversion."""
    assert registry._camel_to_kebab("InvoiceCreated") == "invoice-created"
    assert registry._camel_to_kebab("AICommandStarted") == "a-i-command-started"
    assert registry._camel_to_kebab("SDINotification") == "s-d-i-notification"
    assert registry._camel_to_kebab("PaymentMatched") == "payment-matched"


def test_pattern_matching(registry):
    """Test wildcard pattern matching."""
    # Exact match
    assert registry._matches_pattern("post-invoice-create", "post-invoice-create") is True
    assert registry._matches_pattern("post-invoice-create", "post-invoice-send") is False

    # Wildcard at end
    assert registry._matches_pattern("post-invoice-create", "post-*") is True
    assert registry._matches_pattern("post-invoice-send", "post-*") is True
    assert registry._matches_pattern("pre-invoice-create", "post-*") is False

    # Wildcard at beginning
    assert registry._matches_pattern("post-invoice-create", "*-create") is True
    assert registry._matches_pattern("on-invoice-create", "*-create") is True
    assert registry._matches_pattern("post-invoice-send", "*-create") is False

    # Wildcard in middle
    assert registry._matches_pattern("post-invoice-create", "*-invoice-*") is True
    assert registry._matches_pattern("pre-invoice-send", "*-invoice-*") is True
    assert registry._matches_pattern("on-payment-matched", "*-invoice-*") is False


def test_enable_disable_hooks(temp_hooks_dir, sample_hooks):
    """Test that enable_hook and disable_hook work correctly."""
    registry = HookRegistry(hooks_dir=temp_hooks_dir)

    hook_name = "post-invoice-create"

    # Initially enabled
    hook = registry.get_hook(hook_name)
    assert hook is not None
    assert hook.enabled is True

    # Disable hook
    result = registry.disable_hook(hook_name)
    assert result is True
    hook = registry.get_hook(hook_name)
    assert hook.enabled is False

    # Enable hook
    result = registry.enable_hook(hook_name)
    assert result is True
    hook = registry.get_hook(hook_name)
    assert hook.enabled is True

    # Try to disable non-existent hook
    result = registry.disable_hook("non-existent-hook")
    assert result is False


def test_list_hooks(temp_hooks_dir, sample_hooks):
    """Test list_hooks with and without enabled filter."""
    registry = HookRegistry(hooks_dir=temp_hooks_dir)

    # List all hooks
    all_hooks = registry.list_hooks()
    assert len(all_hooks) == 4

    # Disable one hook
    registry.disable_hook("post-invoice-create")

    # List all hooks (should still be 4)
    all_hooks = registry.list_hooks()
    assert len(all_hooks) == 4

    # List only enabled hooks (should be 3)
    enabled_hooks = registry.list_hooks(enabled_only=True)
    assert len(enabled_hooks) == 3
    hook_names = {h.name for h in enabled_hooks}
    assert "post-invoice-create" not in hook_names
    assert "post-invoice-send" in hook_names


def test_reload_hooks(temp_hooks_dir, sample_hooks):
    """Test that reload() rediscovers hooks from disk."""
    registry = HookRegistry(hooks_dir=temp_hooks_dir)

    # Initially 4 hooks
    assert len(registry.list_hooks()) == 4

    # Add a new hook file
    (temp_hooks_dir / "on-payment-matched.sh").write_text(
        dedent(
            """\
            #!/bin/bash
            echo "Payment matched"
            """
        )
    )

    # Before reload, still 4 hooks
    assert len(registry.list_hooks()) == 4

    # Reload
    registry.reload()

    # After reload, should have 5 hooks
    assert len(registry.list_hooks()) == 5
    assert registry.get_hook("on-payment-matched") is not None


def test_get_hook(temp_hooks_dir, sample_hooks):
    """Test get_hook retrieves hook by name."""
    registry = HookRegistry(hooks_dir=temp_hooks_dir)

    # Get existing hook
    hook = registry.get_hook("post-invoice-create")
    assert hook is not None
    assert hook.name == "post-invoice-create"
    assert hook.script_path.name == "post-invoice-create.sh"

    # Get non-existent hook
    hook = registry.get_hook("non-existent-hook")
    assert hook is None


def test_singleton_registry(temp_hooks_dir):
    """Test that get_hook_registry returns singleton instance."""
    # Clear global registry for this test
    import openfatture.core.hooks.registry as registry_module

    registry_module._registry = None

    # First call creates instance
    registry1 = get_hook_registry(hooks_dir=temp_hooks_dir)
    assert registry1 is not None

    # Second call returns same instance
    registry2 = get_hook_registry(hooks_dir=temp_hooks_dir)
    assert registry1 is registry2

    # Clean up
    registry_module._registry = None


def test_disabled_hooks_not_returned_for_events(temp_hooks_dir, sample_hooks):
    """Test that disabled hooks are not returned by get_hooks_for_event."""
    registry = HookRegistry(hooks_dir=temp_hooks_dir)

    # Initially, InvoiceCreatedEvent returns the hook
    hooks = registry.get_hooks_for_event("InvoiceCreatedEvent")
    assert len(hooks) == 1
    assert hooks[0].name == "post-invoice-create"

    # Disable the hook
    registry.disable_hook("post-invoice-create")

    # Now, InvoiceCreatedEvent should return no hooks
    hooks = registry.get_hooks_for_event("InvoiceCreatedEvent")
    assert len(hooks) == 0
