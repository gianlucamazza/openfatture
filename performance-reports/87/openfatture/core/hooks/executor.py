"""Hook script execution engine.

Executes hook scripts (shell, Python) with timeout, environment variable injection,
and comprehensive error handling.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import time
from dataclasses import asdict
from pathlib import Path

import structlog

from openfatture.core.events.base import BaseEvent

from .models import HookConfig, HookResult

logger = structlog.get_logger("hooks.executor")


class HookExecutionError(Exception):
    """Exception raised when hook execution fails with fail_on_error=True."""

    def __init__(self, message: str, result: HookResult):
        super().__init__(message)
        self.result = result


class HookExecutor:
    """Executes hook scripts with timeout, env vars, and error handling.

    The executor runs shell scripts (.sh, .bash) and Python scripts (.py)
    in subprocess with comprehensive lifecycle management:
    - Environment variable injection
    - Timeout enforcement
    - stdout/stderr capture
    - Exit code handling
    - Structured logging

    Example:
        >>> executor = HookExecutor(hooks_dir=Path("~/.openfatture/hooks"))
        >>> config = HookConfig(name="post-invoice-send", ...)
        >>> event = InvoiceSentEvent(invoice_id=123, ...)
        >>> result = executor.execute_hook(config, event)
        >>> print(result.success)
        True
    """

    def __init__(
        self,
        hooks_dir: Path | None = None,
        default_timeout: int = 30,
        fail_on_error: bool = False,
    ):
        """Initialize hook executor.

        Args:
            hooks_dir: Directory containing hook scripts (default: ~/.openfatture/hooks)
            default_timeout: Default timeout in seconds for hook execution
            fail_on_error: Default fail_on_error behavior (can be overridden per hook)
        """
        self.hooks_dir = hooks_dir or (Path.home() / ".openfatture" / "hooks")
        self.default_timeout = default_timeout
        self.fail_on_error = fail_on_error

        # Ensure hooks directory exists
        self.hooks_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "hook_executor_initialized",
            hooks_dir=str(self.hooks_dir),
            default_timeout=default_timeout,
        )

    def execute_hook(
        self,
        config: HookConfig,
        event: BaseEvent,
        env_vars: dict[str, str] | None = None,
    ) -> HookResult:
        """Execute a hook script with the given event data.

        Args:
            config: Hook configuration
            event: The event that triggered this hook
            env_vars: Additional environment variables (merged with config.env_vars)

        Returns:
            HookResult with execution details

        Raises:
            HookExecutionError: If hook fails and config.fail_on_error is True
        """
        if not config.enabled:
            logger.debug("hook_disabled", hook=config.name)
            return HookResult(
                hook_name=config.name,
                success=True,
                exit_code=0,
                stdout="",
                stderr="Hook is disabled",
                duration_ms=0.0,
            )

        start_time = time.perf_counter()

        try:
            # Build environment variables
            hook_env = self._build_env_vars(config, event, env_vars or {})

            # Execute hook script
            logger.info(
                "hook_executing",
                hook=config.name,
                script=str(config.script_path),
                event_type=event.__class__.__name__,
                timeout=config.timeout_seconds,
            )

            result = self._run_script(config, hook_env)

            duration_ms = (time.perf_counter() - start_time) * 1000

            # Build result
            hook_result = HookResult(
                hook_name=config.name,
                success=result.returncode == 0,
                exit_code=result.returncode,
                stdout=result.stdout.decode("utf-8", errors="replace").strip(),
                stderr=result.stderr.decode("utf-8", errors="replace").strip(),
                duration_ms=duration_ms,
                timed_out=False,
            )

            # Log result
            log_method = logger.info if hook_result.success else logger.warning
            log_method(
                "hook_executed",
                hook=config.name,
                success=hook_result.success,
                exit_code=hook_result.exit_code,
                duration_ms=duration_ms,
                stdout_length=len(hook_result.stdout),
                stderr_length=len(hook_result.stderr),
            )

            # Check fail_on_error
            if not hook_result.success and config.fail_on_error:
                raise HookExecutionError(
                    f"Hook '{config.name}' failed with exit code {hook_result.exit_code}",
                    hook_result,
                )

            return hook_result

        except subprocess.TimeoutExpired as e:
            duration_ms = (time.perf_counter() - start_time) * 1000

            logger.error(
                "hook_timeout",
                hook=config.name,
                timeout=config.timeout_seconds,
                duration_ms=duration_ms,
            )

            timeout_result = HookResult(
                hook_name=config.name,
                success=False,
                exit_code=-1,
                stdout=(e.stdout.decode("utf-8", errors="replace") if e.stdout else ""),
                stderr=(e.stderr.decode("utf-8", errors="replace") if e.stderr else ""),
                duration_ms=duration_ms,
                error=f"Hook timed out after {config.timeout_seconds}s",
                timed_out=True,
            )

            if config.fail_on_error:
                raise HookExecutionError(
                    f"Hook '{config.name}' timed out after {config.timeout_seconds}s",
                    timeout_result,
                )

            return timeout_result

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000

            logger.error(
                "hook_execution_failed",
                hook=config.name,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=duration_ms,
                exc_info=True,
            )

            error_result = HookResult(
                hook_name=config.name,
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                duration_ms=duration_ms,
                error=str(e),
            )

            if config.fail_on_error:
                raise HookExecutionError(
                    f"Hook '{config.name}' failed: {e}",
                    error_result,
                )

            return error_result

    def _build_env_vars(
        self,
        config: HookConfig,
        event: BaseEvent,
        extra_env: dict[str, str],
    ) -> dict[str, str]:
        """Build environment variables for hook execution.

        Combines:
        1. Current process environment
        2. Hook-specific metadata (OPENFATTURE_HOOK_NAME, etc.)
        3. Event data (flattened, uppercase keys)
        4. Config env_vars
        5. Extra env_vars

        Args:
            config: Hook configuration
            event: The event
            extra_env: Additional environment variables

        Returns:
            Dictionary of environment variables
        """
        env = dict(os.environ)

        # Hook metadata
        env["OPENFATTURE_HOOK_NAME"] = config.name
        env["OPENFATTURE_EVENT_TYPE"] = event.__class__.__name__
        env["OPENFATTURE_EVENT_ID"] = str(event.event_id)
        env["OPENFATTURE_EVENT_TIME"] = event.occurred_at.isoformat()

        # Event data as JSON
        event_data = asdict(event)
        # Convert non-serializable types
        if "event_id" in event_data:
            event_data["event_id"] = str(event_data["event_id"])
        if "occurred_at" in event_data:
            event_data["occurred_at"] = event_data["occurred_at"].isoformat()

        env["OPENFATTURE_EVENT_DATA"] = json.dumps(event_data, default=str)

        # Event fields as individual env vars (uppercase, with OPENFATTURE_ prefix)
        for key, value in event_data.items():
            if key not in ("event_id", "occurred_at", "context"):
                env_key = f"OPENFATTURE_{key.upper()}"
                env[env_key] = str(value)

        # Config env vars (override)
        env.update(config.env_vars)

        # Extra env vars (highest priority)
        env.update(extra_env)

        return env

    def _run_script(self, config: HookConfig, env: dict[str, str]) -> subprocess.CompletedProcess:
        """Run hook script with subprocess.

        Args:
            config: Hook configuration
            env: Environment variables

        Returns:
            CompletedProcess with stdout, stderr, returncode
        """
        script_path = config.script_path

        # Determine interpreter based on file extension
        suffix = script_path.suffix.lower()

        if suffix in (".sh", ".bash"):
            command = ["/bin/bash", str(script_path)]
        elif suffix == ".py":
            command = ["python", str(script_path)]
        else:
            # Default to making file executable and running directly
            command = [str(script_path)]

        # Execute with timeout
        result = subprocess.run(
            command,
            env=env,
            capture_output=True,
            timeout=config.timeout_seconds,
            cwd=self.hooks_dir,
        )

        return result

    async def execute_hook_async(
        self,
        config: HookConfig,
        event: BaseEvent,
        env_vars: dict[str, str] | None = None,
    ) -> HookResult:
        """Execute a hook asynchronously in a background thread.

        Args:
            config: Hook configuration
            event: The event
            env_vars: Additional environment variables

        Returns:
            HookResult

        Example:
            >>> result = await executor.execute_hook_async(config, event)
        """
        # Run in executor to avoid blocking event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.execute_hook,
            config,
            event,
            env_vars,
        )
