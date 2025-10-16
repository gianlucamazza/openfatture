"""Custom slash commands system for OpenFatture CLI.

This module provides a registry for user-defined slash commands that can be loaded
from YAML files and executed in the interactive chat interface.

Inspired by Gemini CLI's custom commands feature, adapted for OpenFatture's
specific domain (invoicing, tax, payments, etc.).

Example command file (~/.openfatture/commands/fattura-rapida.yaml):
    name: fattura-rapida
    description: Crea fattura velocemente con AI
    category: invoicing
    aliases: [fr, quick-invoice]
    template: |
      Crea una fattura completa per:
      Cliente: {{ client }}
      Descrizione: {{ description }}
      Importo: {{ amount }}€

      Genera descrizione dettagliata, suggerisci IVA corretta, e verifica compliance.

Usage in chat:
    > /fattura-rapida "Rossi SRL" "consulenza web" "500"
    # Expands template with parameters and sends to AI
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Template, TemplateSyntaxError
from rich.console import Console
from rich.table import Table

from openfatture.utils.logging import get_logger

logger = get_logger(__name__)
console = Console()


@dataclass
class CustomCommand:
    """User-defined custom command.

    Attributes:
        name: Command name (used as /name in chat)
        description: Human-readable description
        template: Jinja2 template string
        category: Command category (invoicing, tax, payment, general, etc.)
        aliases: Alternative names for the command
        examples: Usage examples for documentation
        author: Command author (optional)
        version: Command version (optional)
    """

    name: str
    description: str
    template: str
    category: str = "general"
    aliases: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    author: str | None = None
    version: str | None = None

    def __post_init__(self) -> None:
        """Validate command after initialization."""
        # Validate name (alphanumeric + hyphens + underscores only)
        if not re.match(r"^[a-zA-Z0-9_-]+$", self.name):
            raise ValueError(
                f"Invalid command name '{self.name}'. "
                "Only alphanumeric characters, hyphens, and underscores allowed."
            )

        # Validate template syntax
        try:
            Template(self.template)
        except TemplateSyntaxError as e:
            raise ValueError(f"Invalid Jinja2 template syntax in command '{self.name}': {e}")

    def expand(self, args: list[str] | None = None, kwargs: dict[str, Any] | None = None) -> str:
        """Expand command template with arguments.

        Args:
            args: Positional arguments (available as args, arg1, arg2, etc.)
            kwargs: Named arguments (available by name)

        Returns:
            Expanded template string

        Examples:
            >>> cmd = CustomCommand(
            ...     name="test",
            ...     description="Test command",
            ...     template="Hello {{ arg1 }}!"
            ... )
            >>> cmd.expand(["World"])
            'Hello World!'
        """
        args = args or []
        kwargs = kwargs or {}

        # Build template context
        context: dict[str, Any] = {
            "args": args,
            "kwargs": kwargs,
            **kwargs,  # Make kwargs available as top-level variables
        }

        # Add positional args as arg1, arg2, etc.
        for i, arg in enumerate(args, start=1):
            context[f"arg{i}"] = arg

        # Render template
        try:
            template = Template(self.template)
            rendered = template.render(**context)
            return rendered.strip()
        except Exception as e:
            logger.error(
                "command_expansion_failed",
                command=self.name,
                args=args,
                kwargs=kwargs,
                error=str(e),
            )
            raise ValueError(f"Failed to expand command '{self.name}': {e}")


class CustomCommandRegistry:
    """Registry for custom user-defined slash commands.

    Loads commands from YAML files in the specified directory
    (default: ~/.openfatture/commands/) and provides methods to execute,
    list, and manage them.

    Example:
        >>> registry = CustomCommandRegistry()
        >>> registry.list_commands()
        [CustomCommand(name='fattura-rapida', ...), ...]
        >>> registry.execute('fattura-rapida', ['Acme Corp', 'Consulting', '500'])
        'Crea una fattura completa per: ...'
    """

    def __init__(self, commands_dir: Path | None = None) -> None:
        """Initialize command registry.

        Args:
            commands_dir: Directory containing command YAML files.
                         Defaults to ~/.openfatture/commands/
        """
        self.commands_dir = commands_dir or (Path.home() / ".openfatture" / "commands")
        self._commands: dict[str, CustomCommand] = {}
        self._aliases: dict[str, str] = {}  # alias -> command name mapping

        # Create commands directory if it doesn't exist
        self.commands_dir.mkdir(parents=True, exist_ok=True)

        # Load commands
        self._load_commands()

    def _load_commands(self) -> None:
        """Load custom commands from YAML files."""
        loaded_count = 0
        error_count = 0

        for yaml_file in self.commands_dir.glob("*.yaml"):
            try:
                with open(yaml_file) as f:
                    data = yaml.safe_load(f)

                if not isinstance(data, dict):
                    logger.warning(
                        "invalid_command_file",
                        file=str(yaml_file),
                        reason="Not a valid YAML dictionary",
                    )
                    error_count += 1
                    continue

                # Create command
                cmd = CustomCommand(**data)

                # Check for name conflicts
                if cmd.name in self._commands:
                    logger.warning(
                        "duplicate_command_name",
                        name=cmd.name,
                        file=str(yaml_file),
                        action="Skipping",
                    )
                    error_count += 1
                    continue

                # Register command
                self._commands[cmd.name] = cmd
                loaded_count += 1

                # Register aliases
                for alias in cmd.aliases:
                    if alias in self._aliases:
                        logger.warning(
                            "duplicate_command_alias",
                            alias=alias,
                            command=cmd.name,
                            existing_command=self._aliases[alias],
                            action="Skipping alias",
                        )
                    else:
                        self._aliases[alias] = cmd.name

                logger.debug(
                    "command_loaded",
                    name=cmd.name,
                    category=cmd.category,
                    aliases=cmd.aliases,
                    file=str(yaml_file),
                )

            except Exception as e:
                logger.error(
                    "command_load_failed",
                    file=str(yaml_file),
                    error=str(e),
                    error_type=type(e).__name__,
                )
                error_count += 1
                continue

        if loaded_count > 0 or error_count > 0:
            logger.info(
                "commands_loaded",
                total=loaded_count,
                errors=error_count,
                directory=str(self.commands_dir),
            )

    def reload(self) -> None:
        """Reload all commands from disk."""
        self._commands.clear()
        self._aliases.clear()
        self._load_commands()

    def execute(
        self,
        command_name: str,
        args: list[str] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> str:
        """Execute custom command with arguments.

        Args:
            command_name: Command name or alias
            args: Positional arguments
            kwargs: Named arguments

        Returns:
            Expanded command template

        Raises:
            ValueError: If command not found or expansion fails
        """
        # Resolve alias
        if command_name in self._aliases:
            command_name = self._aliases[command_name]

        if command_name not in self._commands:
            available = ", ".join(sorted(self._commands.keys()))
            raise ValueError(f"Command '{command_name}' not found. Available commands: {available}")

        cmd = self._commands[command_name]

        logger.info(
            "command_executed",
            command=command_name,
            category=cmd.category,
            args_count=len(args or []),
            kwargs_count=len(kwargs or {}),
        )

        return cmd.expand(args=args, kwargs=kwargs)

    def get_command(self, name: str) -> CustomCommand | None:
        """Get command by name or alias.

        Args:
            name: Command name or alias

        Returns:
            CustomCommand if found, None otherwise
        """
        # Resolve alias
        if name in self._aliases:
            name = self._aliases[name]

        return self._commands.get(name)

    def list_commands(self, category: str | None = None) -> list[CustomCommand]:
        """List all available custom commands.

        Args:
            category: Filter by category (None = all commands)

        Returns:
            List of CustomCommand objects
        """
        commands = list(self._commands.values())

        if category:
            commands = [cmd for cmd in commands if cmd.category == category]

        # Sort by category, then by name
        commands.sort(key=lambda cmd: (cmd.category, cmd.name))

        return commands

    def has_command(self, name: str) -> bool:
        """Check if command exists (by name or alias).

        Args:
            name: Command name or alias

        Returns:
            True if command exists, False otherwise
        """
        return name in self._commands or name in self._aliases

    def get_categories(self) -> list[str]:
        """Get all command categories.

        Returns:
            Sorted list of unique categories
        """
        categories = {cmd.category for cmd in self._commands.values()}
        return sorted(categories)

    def display_commands(self, category: str | None = None) -> None:
        """Display commands in a Rich table.

        Args:
            category: Filter by category (None = all commands)
        """
        commands = self.list_commands(category=category)

        if not commands:
            if category:
                console.print(f"[yellow]No commands found in category '{category}'[/yellow]")
            else:
                console.print("[yellow]No custom commands available[/yellow]")
                console.print(f"[dim]Create commands in: {self.commands_dir}[/dim]")
            return

        table = Table(title=f"Custom Commands{' - ' + category if category else ''}")
        table.add_column("Command", style="cyan", no_wrap=True)
        table.add_column("Aliases", style="dim")
        table.add_column("Category", style="yellow")
        table.add_column("Description", style="white")

        for cmd in commands:
            aliases_str = ", ".join(cmd.aliases) if cmd.aliases else "-"
            table.add_row(
                f"/{cmd.name}",
                aliases_str,
                cmd.category,
                cmd.description,
            )

        console.print()
        console.print(table)
        console.print()

        # Show usage hint
        console.print("[dim]Usage: /command-name [args...][/dim]")
        console.print(f"[dim]Commands directory: {self.commands_dir}[/dim]")
        console.print()


# Global registry instance (singleton pattern)
_registry: CustomCommandRegistry | None = None


def get_command_registry(commands_dir: Path | None = None) -> CustomCommandRegistry:
    """Get the global command registry instance.

    Args:
        commands_dir: Commands directory (only used on first call)

    Returns:
        CustomCommandRegistry singleton instance
    """
    global _registry
    if _registry is None:
        _registry = CustomCommandRegistry(commands_dir=commands_dir)
    return _registry
