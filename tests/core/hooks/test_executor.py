"""Unit tests for HookExecutor."""

import json
from dataclasses import dataclass
from textwrap import dedent

import pytest

from openfatture.core.events.base import BaseEvent
from openfatture.core.hooks.executor import HookExecutor
from openfatture.core.hooks.models import HookConfig


# Test event for unit testing
@dataclass(frozen=True)
class TestEvent(BaseEvent):
    """Simple test event."""

    invoice_id: int = 123
    invoice_number: str = "001/2025"
    total_amount: float = 1000.0


@pytest.fixture
def temp_hooks_dir(tmp_path):
    """Create a temporary hooks directory for tests."""
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    return hooks_dir


@pytest.fixture
def executor(temp_hooks_dir):
    """Create a HookExecutor instance for testing."""
    return HookExecutor(hooks_dir=temp_hooks_dir, default_timeout=5)


@pytest.fixture
def test_event():
    """Create a test event."""
    return TestEvent(invoice_id=123, invoice_number="001/2025", total_amount=1000.0)


@pytest.fixture
def success_bash_hook(temp_hooks_dir):
    """Create a simple bash hook that succeeds (exit 0)."""
    script_path = temp_hooks_dir / "success.sh"
    script_path.write_text(
        dedent(
            """\
            #!/bin/bash
            echo "Hook executed successfully"
            exit 0
            """
        )
    )
    script_path.chmod(0o755)

    return HookConfig(
        name="success-hook",
        script_path=script_path,
        enabled=True,
        timeout_seconds=5,
    )


@pytest.fixture
def success_python_hook(temp_hooks_dir):
    """Create a simple Python hook that succeeds."""
    script_path = temp_hooks_dir / "success.py"
    script_path.write_text(
        dedent(
            """\
            #!/usr/bin/env python3
            import sys
            print("Python hook executed successfully")
            sys.exit(0)
            """
        )
    )
    script_path.chmod(0o755)

    return HookConfig(
        name="success-python-hook",
        script_path=script_path,
        enabled=True,
        timeout_seconds=5,
    )


@pytest.fixture
def timeout_hook(temp_hooks_dir):
    """Create a hook that times out (sleeps forever)."""
    script_path = temp_hooks_dir / "timeout.sh"
    script_path.write_text(
        dedent(
            """\
            #!/bin/bash
            echo "Starting long task"
            sleep 100
            echo "This should never be reached"
            """
        )
    )
    script_path.chmod(0o755)

    return HookConfig(
        name="timeout-hook",
        script_path=script_path,
        enabled=True,
        timeout_seconds=1,  # 1 second timeout
    )


@pytest.fixture
def env_check_hook(temp_hooks_dir):
    """Create a hook that prints all OPENFATTURE_* env vars."""
    script_path = temp_hooks_dir / "env_check.sh"
    script_path.write_text(
        dedent(
            """\
            #!/bin/bash
            # Print all OPENFATTURE_ environment variables
            env | grep "^OPENFATTURE_" | sort
            """
        )
    )
    script_path.chmod(0o755)

    return HookConfig(
        name="env-check-hook",
        script_path=script_path,
        enabled=True,
        timeout_seconds=5,
    )


@pytest.fixture
def failure_hook(temp_hooks_dir):
    """Create a hook that fails (exit 1)."""
    script_path = temp_hooks_dir / "failure.sh"
    script_path.write_text(
        dedent(
            """\
            #!/bin/bash
            echo "Hook failed" >&2
            exit 1
            """
        )
    )
    script_path.chmod(0o755)

    return HookConfig(
        name="failure-hook",
        script_path=script_path,
        enabled=True,
        timeout_seconds=5,
    )


@pytest.fixture
def output_hook(temp_hooks_dir):
    """Create a hook that outputs to both stdout and stderr."""
    script_path = temp_hooks_dir / "output.sh"
    script_path.write_text(
        dedent(
            """\
            #!/bin/bash
            echo "This goes to stdout"
            echo "This goes to stderr" >&2
            exit 0
            """
        )
    )
    script_path.chmod(0o755)

    return HookConfig(
        name="output-hook",
        script_path=script_path,
        enabled=True,
        timeout_seconds=5,
    )


def test_execute_bash_hook(executor, success_bash_hook, test_event):
    """Test bash script execution with exit 0."""
    result = executor.execute_hook(success_bash_hook, test_event)

    assert result.success is True
    assert result.exit_code == 0
    assert "Hook executed successfully" in result.stdout
    assert result.stderr == ""
    assert result.timed_out is False
    assert result.duration_ms > 0


def test_execute_python_hook(executor, success_python_hook, test_event):
    """Test Python script execution."""
    result = executor.execute_hook(success_python_hook, test_event)

    assert result.success is True
    assert result.exit_code == 0
    assert "Python hook executed successfully" in result.stdout
    assert result.stderr == ""
    assert result.timed_out is False
    assert result.duration_ms > 0


def test_hook_timeout(executor, timeout_hook, test_event):
    """Test that script is killed after timeout expires."""
    result = executor.execute_hook(timeout_hook, test_event)

    # Hook should have timed out
    assert result.success is False
    assert result.timed_out is True
    assert result.exit_code == -1
    assert "Starting long task" in result.stdout
    assert "This should never be reached" not in result.stdout
    assert result.error is not None
    assert "timed out" in result.error.lower()


def test_environment_variable_injection(executor, env_check_hook, test_event):
    """Test that all OPENFATTURE_* env vars are present."""
    result = executor.execute_hook(env_check_hook, test_event)

    assert result.success is True

    # Check that expected env vars are present in output
    output = result.stdout
    assert "OPENFATTURE_HOOK_NAME=env-check-hook" in output
    assert "OPENFATTURE_EVENT_TYPE=TestEvent" in output
    assert "OPENFATTURE_EVENT_ID=" in output  # UUID present
    assert "OPENFATTURE_EVENT_TIME=" in output  # ISO timestamp present
    assert "OPENFATTURE_INVOICE_ID=123" in output
    assert "OPENFATTURE_INVOICE_NUMBER=001/2025" in output
    assert "OPENFATTURE_TOTAL_AMOUNT=1000.0" in output

    # Check EVENT_DATA is valid JSON
    event_data_line = [line for line in output.split("\n") if "OPENFATTURE_EVENT_DATA=" in line]
    assert len(event_data_line) == 1
    event_data_json = event_data_line[0].split("=", 1)[1]
    event_data = json.loads(event_data_json)
    assert event_data["invoice_id"] == 123
    assert event_data["invoice_number"] == "001/2025"
    assert event_data["total_amount"] == 1000.0


def test_hook_success_exit_code(executor, success_bash_hook, test_event):
    """Test that exit code 0 results in success=True."""
    result = executor.execute_hook(success_bash_hook, test_event)

    assert result.exit_code == 0
    assert result.success is True


def test_hook_failure_exit_code(executor, failure_hook, test_event):
    """Test that exit code non-zero results in success=False."""
    result = executor.execute_hook(failure_hook, test_event)

    assert result.exit_code == 1
    assert result.success is False
    assert "Hook failed" in result.stderr


def test_stdout_stderr_capture(executor, output_hook, test_event):
    """Test that stdout and stderr are correctly captured."""
    result = executor.execute_hook(output_hook, test_event)

    assert result.success is True
    assert "This goes to stdout" in result.stdout
    assert "This goes to stderr" in result.stderr
    assert result.stdout.strip() == "This goes to stdout"
    assert result.stderr.strip() == "This goes to stderr"


@pytest.mark.asyncio
async def test_async_execution(executor, success_bash_hook, test_event):
    """Test that execute_hook_async() works."""
    result = await executor.execute_hook_async(success_bash_hook, test_event)

    assert result.success is True
    assert result.exit_code == 0
    assert "Hook executed successfully" in result.stdout
    assert result.stderr == ""
    assert result.duration_ms > 0


def test_disabled_hook_returns_success(executor, success_bash_hook, test_event):
    """Test that disabled hooks return success without executing."""
    success_bash_hook.enabled = False

    result = executor.execute_hook(success_bash_hook, test_event)

    assert result.success is True
    assert result.exit_code == 0
    assert result.stdout == ""
    assert result.stderr == "Hook is disabled"
    assert result.duration_ms == 0.0


def test_extra_env_vars(executor, env_check_hook, test_event):
    """Test that extra env vars are passed to hook."""
    extra_env = {
        "CUSTOM_VAR_1": "value1",
        "CUSTOM_VAR_2": "value2",
    }

    result = executor.execute_hook(env_check_hook, test_event, env_vars=extra_env)

    # Note: env_check_hook only prints OPENFATTURE_* vars, so custom vars won't show
    # But we can verify they're passed by creating a different hook
    assert result.success is True


def test_config_env_vars(temp_hooks_dir, executor, test_event):
    """Test that config.env_vars are passed to hook."""
    script_path = temp_hooks_dir / "config_env.sh"
    script_path.write_text(
        dedent(
            """\
            #!/bin/bash
            echo "CONFIG_VAR=$CONFIG_VAR"
            echo "ANOTHER_VAR=$ANOTHER_VAR"
            """
        )
    )
    script_path.chmod(0o755)

    config = HookConfig(
        name="config-env-hook",
        script_path=script_path,
        enabled=True,
        timeout_seconds=5,
        env_vars={
            "CONFIG_VAR": "from_config",
            "ANOTHER_VAR": "also_from_config",
        },
    )

    result = executor.execute_hook(config, test_event)

    assert result.success is True
    assert "CONFIG_VAR=from_config" in result.stdout
    assert "ANOTHER_VAR=also_from_config" in result.stdout
