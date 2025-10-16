"""Hook registry for discovery and management of hook scripts.

Scans the hooks directory and maintains a registry of available hooks,
supporting filtering by event name and wildcard matching.
"""

from __future__ import annotations

import re
from pathlib import Path

import structlog

from .models import HookConfig, HookMetadata

logger = structlog.get_logger("hooks.registry")


class HookRegistry:
    """Registry for discovered hooks in ~/.openfatture/hooks/

    Automatically discovers hook scripts based on naming convention:
    - pre-invoice-create.sh
    - post-invoice-send.py
    - on-payment-matched.sh
    - etc.

    Supports wildcard matching:
    - `pre-*` matches all pre-hooks
    - `*-invoice-*` matches all invoice hooks
    - `on-*` matches all event hooks

    Example:
        >>> registry = HookRegistry()
        >>> hooks = registry.get_hooks_for_event("InvoiceCreatedEvent")
        >>> for hook in hooks:
        ...     print(hook.name)
        pre-invoice-create
        post-invoice-create
    """

    # Supported script extensions
    HOOK_EXTENSIONS = {".sh", ".bash", ".py"}

    def __init__(self, hooks_dir: Path | None = None):
        """Initialize hook registry.

        Args:
            hooks_dir: Directory containing hook scripts (default: ~/.openfatture/hooks)
        """
        self.hooks_dir = hooks_dir or (Path.home() / ".openfatture" / "hooks")
        self._hooks: dict[str, HookConfig] = {}

        # Ensure hooks directory exists
        self.hooks_dir.mkdir(parents=True, exist_ok=True)

        # Discover hooks
        self._load_hooks()

    def _load_hooks(self) -> None:
        """Discover and load all hooks from hooks directory."""
        loaded_count = 0
        error_count = 0

        for script_file in self.hooks_dir.iterdir():
            # Skip non-files
            if not script_file.is_file():
                continue

            # Skip files without supported extensions
            if script_file.suffix.lower() not in self.HOOK_EXTENSIONS:
                continue

            # Skip hidden files
            if script_file.name.startswith("."):
                continue

            # Hook name is filename without extension
            hook_name = script_file.stem

            try:
                # Parse metadata from script comments
                metadata = HookMetadata.from_script(script_file)

                # Create hook config
                config = HookConfig(
                    name=hook_name,
                    script_path=script_file,
                    enabled=True,
                    timeout_seconds=metadata.timeout or 30,
                    fail_on_error=False,
                    description=metadata.description,
                )

                # Check for duplicate names
                if hook_name in self._hooks:
                    logger.warning(
                        "duplicate_hook_name",
                        hook=hook_name,
                        existing_path=str(self._hooks[hook_name].script_path),
                        new_path=str(script_file),
                        action="Skipping new file",
                    )
                    error_count += 1
                    continue

                # Register hook
                self._hooks[hook_name] = config
                loaded_count += 1

                logger.debug(
                    "hook_discovered",
                    hook=hook_name,
                    path=str(script_file),
                    timeout=config.timeout_seconds,
                    description=config.description,
                )

            except Exception as e:
                logger.error(
                    "hook_load_failed",
                    file=str(script_file),
                    error=str(e),
                    error_type=type(e).__name__,
                )
                error_count += 1

        if loaded_count > 0 or error_count > 0:
            logger.info(
                "hooks_discovered",
                total=loaded_count,
                errors=error_count,
                directory=str(self.hooks_dir),
            )

    def reload(self) -> None:
        """Reload all hooks from disk.

        Clears the registry and re-discovers all hooks.
        """
        logger.info("reloading_hooks", directory=str(self.hooks_dir))
        self._hooks.clear()
        self._load_hooks()

    def get_hook(self, name: str) -> HookConfig | None:
        """Get hook configuration by name.

        Args:
            name: Hook name

        Returns:
            HookConfig if found, None otherwise
        """
        return self._hooks.get(name)

    def list_hooks(self, enabled_only: bool = False) -> list[HookConfig]:
        """List all registered hooks.

        Args:
            enabled_only: If True, only return enabled hooks

        Returns:
            List of HookConfig objects sorted by name
        """
        hooks = list(self._hooks.values())

        if enabled_only:
            hooks = [h for h in hooks if h.enabled]

        return sorted(hooks, key=lambda h: h.name)

    def get_hooks_for_event(self, event_name: str) -> list[HookConfig]:
        """Get hooks matching the given event name.

        Maps event names to hook naming convention and returns all matching hooks:
        - InvoiceCreatedEvent → [post-invoice-create]
        - InvoiceSentEvent → [post-invoice-send]
        - AICommandStartedEvent → [pre-ai-command]
        - etc.

        Args:
            event_name: Event class name (e.g., 'InvoiceCreatedEvent')

        Returns:
            List of matching HookConfig objects sorted by name

        Example:
            >>> hooks = registry.get_hooks_for_event("InvoiceCreatedEvent")
            >>> for hook in hooks:
            ...     print(hook.name)
            post-invoice-create
        """
        # Convert event name to hook patterns
        patterns = self._event_to_hook_patterns(event_name)

        # Find matching hooks
        matching_hooks = []

        for pattern in patterns:
            for hook_name, config in self._hooks.items():
                if config.enabled and self._matches_pattern(hook_name, pattern):
                    if config not in matching_hooks:
                        matching_hooks.append(config)

        return sorted(matching_hooks, key=lambda h: h.name)

    def _event_to_hook_patterns(self, event_name: str) -> list[str]:
        """Convert event name to hook name patterns.

        Args:
            event_name: Event class name (e.g., 'InvoiceCreatedEvent')

        Returns:
            List of hook name patterns to match

        Example:
            >>> patterns = registry._event_to_hook_patterns("InvoiceCreatedEvent")
            >>> print(patterns)
            ['post-invoice-create', 'on-invoice-create']
        """
        patterns = []

        # Remove "Event" suffix
        if event_name.endswith("Event"):
            event_name = event_name[:-5]

        # Convert camelCase to kebab-case
        kebab = self._camel_to_kebab(event_name)

        # Determine hook timing based on event name
        if event_name.startswith("Batch"):
            if "Completed" in event_name:
                patterns.append(f"post-{kebab.replace('-completed', '')}")
                patterns.append(f"on-{kebab}")
            elif "Started" in event_name:
                patterns.append(f"pre-{kebab.replace('-started', '')}")
                patterns.append(f"on-{kebab}")
        elif event_name.startswith("AICommand"):
            if "Completed" in event_name:
                patterns.append("post-ai-command")
                patterns.append("on-ai-command-complete")
            elif "Started" in event_name:
                patterns.append("pre-ai-command")
                patterns.append("on-ai-command-start")
        elif "Created" in event_name:
            # e.g., InvoiceCreatedEvent → post-invoice-create
            base = kebab.replace("-created", "")
            patterns.append(f"post-{base}-create")
            patterns.append(f"on-{base}-create")
        elif "Sent" in event_name:
            # e.g., InvoiceSentEvent → post-invoice-send
            base = kebab.replace("-sent", "")
            patterns.append(f"post-{base}-send")
            patterns.append(f"on-{base}-send")
        elif "Deleted" in event_name:
            base = kebab.replace("-deleted", "")
            patterns.append(f"post-{base}-delete")
            patterns.append(f"on-{base}-delete")
        elif "Validated" in event_name:
            base = kebab.replace("-validated", "")
            patterns.append(f"post-{base}-validate")
            patterns.append(f"on-{base}-validate")
        elif "Notification" in event_name:
            # e.g., SDINotificationReceivedEvent → on-sdi-notification
            patterns.append("on-sdi-notification")
        else:
            # Generic pattern
            patterns.append(f"on-{kebab}")

        return patterns

    def _camel_to_kebab(self, text: str) -> str:
        """Convert CamelCase to kebab-case.

        Args:
            text: CamelCase string

        Returns:
            kebab-case string

        Example:
            >>> registry._camel_to_kebab("InvoiceCreated")
            'invoice-created'
        """
        # Insert hyphen before uppercase letters (except at start)
        kebab = re.sub(r"(?<!^)(?=[A-Z])", "-", text)
        return kebab.lower()

    def _matches_pattern(self, hook_name: str, pattern: str) -> bool:
        """Check if hook name matches pattern (supports wildcards).

        Args:
            hook_name: Hook name (e.g., 'post-invoice-create')
            pattern: Pattern to match (e.g., 'post-invoice-*', '*-invoice-*')

        Returns:
            True if hook name matches pattern
        """
        # Convert wildcard pattern to regex
        regex_pattern = pattern.replace("*", ".*").replace("?", ".")
        regex_pattern = f"^{regex_pattern}$"

        return re.match(regex_pattern, hook_name) is not None

    def enable_hook(self, name: str) -> bool:
        """Enable a hook.

        Args:
            name: Hook name

        Returns:
            True if hook was found and enabled, False otherwise
        """
        if name in self._hooks:
            self._hooks[name].enabled = True
            logger.info("hook_enabled", hook=name)
            return True
        return False

    def disable_hook(self, name: str) -> bool:
        """Disable a hook.

        Args:
            name: Hook name

        Returns:
            True if hook was found and disabled, False otherwise
        """
        if name in self._hooks:
            self._hooks[name].enabled = False
            logger.info("hook_disabled", hook=name)
            return True
        return False


# Global registry instance
_registry: HookRegistry | None = None


def get_hook_registry(hooks_dir: Path | None = None) -> HookRegistry:
    """Get the global hook registry singleton.

    Args:
        hooks_dir: Hooks directory (only used on first call)

    Returns:
        HookRegistry singleton instance
    """
    global _registry
    if _registry is None:
        _registry = HookRegistry(hooks_dir=hooks_dir)
    return _registry
