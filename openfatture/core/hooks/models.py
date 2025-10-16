"""Hook configuration and result models.

Data classes for hook configuration, execution results, and metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class HookConfig:
    """Configuration for a single hook script.

    Attributes:
        name: Hook name (e.g., 'pre-invoice-create', 'post-invoice-send')
        script_path: Absolute path to the hook script file
        enabled: Whether this hook is currently enabled
        timeout_seconds: Maximum execution time before hook is killed
        fail_on_error: If True, halt the triggering operation on hook failure
        env_vars: Additional environment variables to pass to the hook
        description: Optional human-readable description

    Example:
        >>> config = HookConfig(
        ...     name="post-invoice-send",
        ...     script_path=Path("/path/to/hooks/post-invoice-send.sh"),
        ...     timeout_seconds=30,
        ...     fail_on_error=False,
        ... )
    """

    name: str
    script_path: Path
    enabled: bool = True
    timeout_seconds: int = 30
    fail_on_error: bool = False
    env_vars: dict[str, str] = field(default_factory=dict)
    description: str | None = None

    def __post_init__(self) -> None:
        """Validate hook configuration after initialization."""
        if not self.script_path.exists():
            raise FileNotFoundError(f"Hook script not found: {self.script_path}")

        if not self.script_path.is_file():
            raise ValueError(f"Hook script is not a file: {self.script_path}")

        if self.timeout_seconds <= 0:
            raise ValueError(f"Invalid timeout: {self.timeout_seconds} (must be positive)")


@dataclass
class HookResult:
    """Result of hook script execution.

    Attributes:
        hook_name: Name of the executed hook
        success: Whether the hook executed successfully (exit code 0)
        exit_code: Process exit code
        stdout: Standard output from the hook
        stderr: Standard error from the hook
        duration_ms: Execution duration in milliseconds
        error: Error message if execution failed
        timed_out: Whether the hook was killed due to timeout

    Example:
        >>> result = HookResult(
        ...     hook_name="post-invoice-send",
        ...     success=True,
        ...     exit_code=0,
        ...     stdout="Notification sent successfully",
        ...     stderr="",
        ...     duration_ms=125.5,
        ... )
    """

    hook_name: str
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    error: str | None = None
    timed_out: bool = False

    def __str__(self) -> str:
        """Human-readable string representation."""
        status = "✓ SUCCESS" if self.success else "✗ FAILED"
        return (
            f"Hook '{self.hook_name}' {status} "
            f"(exit={self.exit_code}, duration={self.duration_ms:.1f}ms)"
        )


@dataclass
class HookMetadata:
    """Metadata extracted from hook script comments.

    Many hooks include metadata in comments at the top of the script.
    This class parses and stores that metadata.

    Example hook header:
        #!/bin/bash
        # DESCRIPTION: Send Slack notification when invoice is sent
        # AUTHOR: John Doe
        # REQUIRES: curl, jq
        # TIMEOUT: 15

    Attributes:
        description: Hook description
        author: Hook author
        requires: Required dependencies (commands/tools)
        timeout: Recommended timeout in seconds
    """

    description: str | None = None
    author: str | None = None
    requires: list[str] = field(default_factory=list)
    timeout: int | None = None

    @classmethod
    def from_script(cls, script_path: Path) -> HookMetadata:
        """Parse metadata from hook script comments.

        Args:
            script_path: Path to the hook script

        Returns:
            HookMetadata instance with extracted metadata
        """
        metadata = cls()

        try:
            with open(script_path) as f:
                for line in f:
                    line = line.strip()

                    # Stop at first non-comment line (after shebang)
                    if not line.startswith("#"):
                        break

                    # Skip shebang
                    if line.startswith("#!"):
                        continue

                    # Parse metadata comments
                    if ":" in line:
                        key, _, value = line[1:].partition(":")
                        key = key.strip().lower()
                        value = value.strip()

                        if key == "description":
                            metadata.description = value
                        elif key == "author":
                            metadata.author = value
                        elif key == "requires":
                            metadata.requires = [dep.strip() for dep in value.split(",")]
                        elif key == "timeout":
                            try:
                                metadata.timeout = int(value)
                            except ValueError:
                                pass

        except Exception:
            # If metadata parsing fails, return empty metadata
            pass

        return metadata
