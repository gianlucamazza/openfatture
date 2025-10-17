"""Web service adapter for custom slash commands.

Provides async/sync bridge for custom commands in Streamlit web interface.
"""

from typing import Any

import streamlit as st

from openfatture.cli.commands.custom_commands import CustomCommandRegistry, get_command_registry


class StreamlitCustomCommandsService:
    """Adapter service for custom commands in Streamlit."""

    def __init__(self) -> None:
        """Initialize service with command registry."""
        self._registry: CustomCommandRegistry | None = None

    @property
    def registry(self) -> CustomCommandRegistry:
        """Get or create command registry (cached)."""
        if self._registry is None:
            self._registry = get_command_registry()
        return self._registry

    def list_commands(self) -> list[dict[str, Any]]:
        """
        Get list of available custom commands.

        Returns:
            List of command dictionaries with metadata
        """
        commands = self.registry.list_commands()
        return [
            {
                "name": cmd.name,
                "description": cmd.description,
                "category": cmd.category,
                "aliases": cmd.aliases,
                "examples": cmd.examples,
                "author": cmd.author,
                "version": cmd.version,
            }
            for cmd in commands
        ]

    def has_command(self, command_name: str) -> bool:
        """
        Check if a command exists.

        Args:
            command_name: Command name (with or without leading slash)

        Returns:
            True if command exists
        """
        return self.registry.has_command(command_name.lstrip("/"))

    def execute_command(self, command_name: str, args: list[str] | None = None) -> str:
        """
        Execute a custom command and return expanded template.

        Args:
            command_name: Command name (with or without leading slash)
            args: Command arguments

        Returns:
            Expanded command template

        Raises:
            ValueError: If command doesn't exist or execution fails
        """
        try:
            return self.registry.execute(command_name.lstrip("/"), args=args or [])
        except Exception as e:
            raise ValueError(f"Command execution failed: {e}")

    def reload_commands(self) -> dict[str, Any]:
        """
        Reload commands from disk.

        Returns:
            Reload statistics
        """
        old_count = len(self.registry.list_commands())

        # Force reload by recreating registry
        self._registry = CustomCommandRegistry()

        new_count = len(self.registry.list_commands())

        return {
            "old_count": old_count,
            "new_count": new_count,
            "added": new_count - old_count,
            "removed": old_count - new_count,
        }

    def get_command_help(self, command_name: str) -> dict[str, Any] | None:
        """
        Get detailed help for a specific command.

        Args:
            command_name: Command name (with or without leading slash)

        Returns:
            Command details or None if not found
        """
        try:
            cmd = self.registry.get_command(command_name.lstrip("/"))
            if cmd:
                return {
                    "name": cmd.name,
                    "description": cmd.description,
                    "category": cmd.category,
                    "aliases": cmd.aliases,
                    "examples": cmd.examples,
                    "template": cmd.template,
                    "author": cmd.author,
                    "version": cmd.version,
                }
        except Exception:
            pass
        return None


@st.cache_resource
def get_custom_commands_service() -> StreamlitCustomCommandsService:
    """
    Get cached custom commands service instance.

    Returns:
        Singleton custom commands service
    """
    return StreamlitCustomCommandsService()
