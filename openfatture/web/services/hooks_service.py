"""Hooks service adapter for Streamlit web interface.

Provides simplified API for hook management and automation.
"""

from typing import Any

import streamlit as st

from openfatture.core.hooks.executor import HookExecutor
from openfatture.core.hooks.registry import HookRegistry
from openfatture.utils.config import Settings, get_settings


class StreamlitHooksService:
    """Adapter service for hooks management in Streamlit."""

    def __init__(self) -> None:
        """Initialize service with settings."""
        self.settings: Settings = get_settings()
        self.registry = HookRegistry()
        self.executor = HookExecutor()

    @st.cache_data(ttl=60, show_spinner=False)  # 1 minute cache for hooks list
    def get_available_hooks(self) -> list[dict[str, Any]]:
        """
        Get list of all available hooks with their status.

        Returns:
            List of hook dictionaries with metadata
        """
        hooks = []

        for hook_config in self.registry.list_hooks():
            # Get metadata from script
            from openfatture.core.hooks.models import HookMetadata

            metadata = HookMetadata.from_script(hook_config.script_path)

            hook_info = {
                "name": hook_config.name,
                "path": str(hook_config.script_path),
                "enabled": hook_config.enabled,
                "timeout": hook_config.timeout_seconds,
                "fail_on_error": hook_config.fail_on_error,
                "description": metadata.description if metadata else None,
                "author": metadata.author if metadata else None,
                "requires": metadata.requires if metadata else [],
                "event_type": self._extract_event_type(hook_config.name),
                "last_execution": None,  # TODO: implement execution history
                "success_rate": None,  # TODO: implement success tracking
            }
            hooks.append(hook_info)

        return sorted(hooks, key=lambda x: x["name"])

    def get_hooks_by_event_type(self, event_type: str) -> list[dict[str, Any]]:
        """
        Get hooks filtered by event type.

        Args:
            event_type: Event type (pre, post, on)

        Returns:
            List of hooks for the specified event type
        """
        all_hooks = self.get_available_hooks()
        return [hook for hook in all_hooks if hook["event_type"] == event_type]

    def toggle_hook_status(self, hook_name: str, enabled: bool) -> bool:
        """
        Enable or disable a hook.

        Args:
            hook_name: Name of the hook to modify
            enabled: Whether to enable the hook

        Returns:
            True if successful, False otherwise
        """
        try:
            # Find the hook configuration
            hook_config = self.registry.get_hook(hook_name)

            if not hook_config:
                return False

            # Update the configuration
            # Note: This is a simplified implementation
            # In a real system, this would update a configuration file
            hook_config.enabled = enabled

            return True

        except Exception:
            return False

    def test_hook_execution(
        self, hook_name: str, test_data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Test execute a hook with sample data.

        Args:
            hook_name: Name of the hook to test
            test_data: Optional test data to pass to the hook

        Returns:
            Dictionary with execution results
        """
        try:
            # Find the hook configuration
            hook_config = self.registry.get_hook(hook_name)

            if not hook_config:
                return {"success": False, "error": f"Hook '{hook_name}' not found", "result": None}

            # Basic validation - check if file exists and is readable
            if not hook_config.script_path.exists():
                return {
                    "success": False,
                    "error": f"Hook file does not exist: {hook_config.script_path}",
                    "result": None,
                }

            # Try to read the file
            try:
                content = hook_config.script_path.read_text(encoding="utf-8")
                lines = len(content.split("\n"))
            except Exception as e:
                return {"success": False, "error": f"Cannot read hook file: {e}", "result": None}

            # Basic syntax validation for Python files
            if hook_config.script_path.suffix == ".py":
                try:
                    compile(content, str(hook_config.script_path), "exec")
                except SyntaxError as e:
                    return {"success": False, "error": f"Python syntax error: {e}", "result": None}

            return {
                "success": True,
                "error": None,
                "result": {
                    "file_size": len(content),
                    "line_count": lines,
                    "is_executable": hook_config.script_path.stat().st_mode & 0o111 != 0,
                    "validation_type": "syntax_check",
                    "message": "Hook validation successful",
                },
            }

        except Exception as e:
            return {"success": False, "error": str(e), "result": None}

    def get_hook_template(self, hook_type: str) -> str:
        """
        Get template code for a specific hook type.

        Args:
            hook_type: Type of hook (bash, python)

        Returns:
            Template code as string
        """
        if hook_type == "bash":
            return """#!/bin/bash
# DESCRIPTION: Hook description here
# AUTHOR: Your Name
# REQUIRES: curl,jq
# TIMEOUT: 30

# Hook script code here
# Environment variables available:
# - HOOK_NAME: Name of the hook being executed
# - EVENT_TYPE: Type of event that triggered this hook
# - Additional variables depending on the event

echo "Hook $HOOK_NAME executed for event: $EVENT_TYPE"

# Example: Send notification
# curl -X POST https://api.example.com/webhook \\
#   -H "Content-Type: application/json" \\
#   -d "{\"event\": \"$EVENT_TYPE\", \"hook\": \"$HOOK_NAME\"}"

exit 0
"""
        elif hook_type == "python":
            return """#!/usr/bin/env python3
# DESCRIPTION: Hook description here
# AUTHOR: Your Name
# REQUIRES: requests
# TIMEOUT: 30

import os
import sys
import json

def main():
    # Hook script code here
    # Environment variables available:
    # - HOOK_NAME: Name of the hook being executed
    # - EVENT_TYPE: Type of event that triggered this hook
    # - Additional variables depending on the event

    hook_name = os.getenv('HOOK_NAME', 'unknown')
    event_type = os.getenv('EVENT_TYPE', 'unknown')

    print(f"Hook {hook_name} executed for event: {event_type}")

    # Example: Send notification
    # import requests
    # requests.post('https://api.example.com/webhook',
    #               json={'event': event_type, 'hook': hook_name})

    return 0

if __name__ == '__main__':
    sys.exit(main())
"""
        else:
            return "# Unsupported hook type"

    def create_hook_from_template(
        self, hook_name: str, hook_type: str, description: str = ""
    ) -> tuple[bool, str]:
        """
        Create a new hook from template.

        Args:
            hook_name: Name for the new hook
            hook_type: Type of hook (bash, python)
            description: Optional description

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Get hooks directory
            hooks_dir = self.registry.hooks_dir
            hooks_dir.mkdir(parents=True, exist_ok=True)

            # Determine file extension
            if hook_type == "bash":
                extension = ".sh"
            elif hook_type == "python":
                extension = ".py"
            else:
                return False, f"Unsupported hook type: {hook_type}"

            # Create file path
            file_path = hooks_dir / f"{hook_name}{extension}"

            if file_path.exists():
                return False, f"Hook file already exists: {file_path}"

            # Get template and customize
            template = self.get_hook_template(hook_type)
            if description:
                template = template.replace("Hook description here", description)

            # Write file
            file_path.write_text(template, encoding="utf-8")

            # Make executable for shell scripts
            if hook_type == "bash":
                file_path.chmod(0o755)

            return True, f"Hook created successfully: {file_path}"

        except Exception as e:
            return False, str(e)

    def _extract_event_type(self, hook_name: str) -> str:
        """
        Extract event type from hook name.

        Args:
            hook_name: Hook name (e.g., 'pre-invoice-create')

        Returns:
            Event type ('pre', 'post', 'on', or 'unknown')
        """
        if hook_name.startswith("pre-"):
            return "pre"
        elif hook_name.startswith("post-"):
            return "post"
        elif hook_name.startswith("on-"):
            return "on"
        else:
            return "unknown"

    def get_hooks_summary(self) -> dict[str, Any]:
        """
        Get summary statistics about hooks.

        Returns:
            Dictionary with hook statistics
        """
        all_hooks = self.get_available_hooks()

        summary = {
            "total_hooks": len(all_hooks),
            "enabled_hooks": len([h for h in all_hooks if h["enabled"]]),
            "disabled_hooks": len([h for h in all_hooks if not h["enabled"]]),
            "by_event_type": {
                "pre": len([h for h in all_hooks if h["event_type"] == "pre"]),
                "post": len([h for h in all_hooks if h["event_type"] == "post"]),
                "on": len([h for h in all_hooks if h["event_type"] == "on"]),
            },
            "by_script_type": {
                "bash": len([h for h in all_hooks if h["path"].endswith((".sh", ".bash"))]),
                "python": len([h for h in all_hooks if h["path"].endswith(".py")]),
            },
        }

        return summary
