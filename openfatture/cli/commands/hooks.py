"""Hook management CLI commands.

Provides commands for listing, enabling, disabling, testing, and creating hooks.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

from openfatture.core.events import InvoiceCreatedEvent
from openfatture.core.hooks import get_hook_registry
from openfatture.core.hooks.executor import HookExecutor
from openfatture.core.hooks.models import HookMetadata

app = typer.Typer(help="Manage lifecycle hooks", no_args_is_help=True)
console = Console()


@app.command("list")
def list_hooks(
    enabled_only: bool = typer.Option(False, "--enabled", help="Show only enabled hooks"),
) -> None:
    """List all discovered hooks.

    Examples:
        openfatture hooks list
        openfatture hooks list --enabled
    """
    registry = get_hook_registry()
    hooks = registry.list_hooks(enabled_only=enabled_only)

    if not hooks:
        if enabled_only:
            console.print("[yellow]No enabled hooks found[/yellow]")
        else:
            console.print("[yellow]No hooks found[/yellow]")
        console.print(f"\n[dim]Create hooks in: {registry.hooks_dir}[/dim]")
        console.print("[dim]See: openfatture hooks create --help[/dim]\n")
        return

    # Create table
    table = Table(title=f"Hooks ({len(hooks)})", show_lines=False)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Enabled", style="white", width=8, justify="center")
    table.add_column("Timeout", style="yellow", width=8, justify="right")
    table.add_column("Script", style="dim")
    table.add_column("Description", style="white")

    for hook in hooks:
        enabled_icon = "✓" if hook.enabled else "✗"
        enabled_color = "green" if hook.enabled else "red"

        table.add_row(
            hook.name,
            f"[{enabled_color}]{enabled_icon}[/{enabled_color}]",
            f"{hook.timeout_seconds}s",
            hook.script_path.name,
            hook.description or "[dim]No description[/dim]",
        )

    console.print()
    console.print(table)
    console.print(f"\n[dim]Hooks directory: {registry.hooks_dir}[/dim]")
    console.print()


@app.command("enable")
def enable_hook(
    name: str = typer.Argument(..., help="Hook name to enable"),
) -> None:
    """Enable a hook.

    Examples:
        openfatture hooks enable post-invoice-send
    """
    registry = get_hook_registry()

    if registry.enable_hook(name):
        console.print(f"[green]✓ Hook '{name}' enabled[/green]")
    else:
        console.print(f"[red]Hook '{name}' not found[/red]")
        console.print("\n[dim]Available hooks:[/dim]")
        for hook in registry.list_hooks():
            console.print(f"  • {hook.name}")
        raise typer.Exit(1)


@app.command("disable")
def disable_hook(
    name: str = typer.Argument(..., help="Hook name to disable"),
) -> None:
    """Disable a hook.

    Examples:
        openfatture hooks disable post-invoice-send
    """
    registry = get_hook_registry()

    if registry.disable_hook(name):
        console.print(f"[yellow]Hook '{name}' disabled[/yellow]")
    else:
        console.print(f"[red]Hook '{name}' not found[/red]")
        raise typer.Exit(1)


@app.command("test")
def test_hook(
    name: str = typer.Argument(..., help="Hook name to test"),
    event_type: str = typer.Option(
        "InvoiceCreatedEvent",
        "--event",
        "-e",
        help="Event type to simulate",
    ),
) -> None:
    """Test a hook with sample event data.

    Executes the hook with a mock event to verify it works correctly.

    Examples:
        openfatture hooks test post-invoice-send
        openfatture hooks test post-invoice-create --event InvoiceCreatedEvent
    """
    registry = get_hook_registry()
    hook_config = registry.get_hook(name)

    if not hook_config:
        console.print(f"[red]Hook '{name}' not found[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold blue]Testing hook: {name}[/bold blue]\n")
    console.print(f"[cyan]Script:[/cyan] {hook_config.script_path}")
    console.print(f"[cyan]Timeout:[/cyan] {hook_config.timeout_seconds}s")
    console.print(f"[cyan]Event:[/cyan] {event_type}\n")

    # Create sample event based on type
    if event_type == "InvoiceCreatedEvent":
        from decimal import Decimal

        sample_event = InvoiceCreatedEvent(
            invoice_id=999,
            invoice_number="TEST/2025",
            client_id=1,
            client_name="Test Client SRL",
            total_amount=Decimal("1000.00"),
        )
    else:
        console.print(f"[yellow]Event type '{event_type}' not supported for testing yet[/yellow]")
        console.print("[dim]Using InvoiceCreatedEvent as default[/dim]\n")
        from decimal import Decimal

        sample_event = InvoiceCreatedEvent(
            invoice_id=999,
            invoice_number="TEST/2025",
            client_id=1,
            client_name="Test Client SRL",
            total_amount=Decimal("1000.00"),
        )

    # Execute hook
    executor = HookExecutor()

    console.print("[cyan]Executing hook...[/cyan]\n")

    try:
        result = executor.execute_hook(hook_config, sample_event)

        # Display result
        if result.success:
            console.print("[bold green]✓ Hook executed successfully![/bold green]\n")
        else:
            console.print(f"[bold red]✗ Hook failed (exit code {result.exit_code})[/bold red]\n")

        # Result details
        details = Table(show_header=False, box=None)
        details.add_column("Field", style="cyan", width=15)
        details.add_column("Value", style="white")

        details.add_row("Exit Code", str(result.exit_code))
        details.add_row("Duration", f"{result.duration_ms:.1f}ms")
        details.add_row("Timed Out", "Yes" if result.timed_out else "No")

        console.print(details)

        # Output
        if result.stdout:
            console.print("\n[bold]STDOUT:[/bold]")
            console.print(Syntax(result.stdout, "text", theme="monokai", word_wrap=True))

        if result.stderr:
            console.print("\n[bold]STDERR:[/bold]")
            console.print(Syntax(result.stderr, "text", theme="monokai", word_wrap=True))

        if result.error:
            console.print(f"\n[red]Error: {result.error}[/red]")

        console.print()

    except Exception as e:
        console.print(f"[red]Failed to execute hook: {e}[/red]")
        raise typer.Exit(1)


@app.command("create")
def create_hook(
    name: str = typer.Argument(..., help="Hook name (e.g., post-invoice-send)"),
    template: str = typer.Option(
        "bash",
        "--template",
        "-t",
        help="Template type: bash, python",
    ),
) -> None:
    """Create a new hook from template.

    Templates include example code and documentation.

    Examples:
        openfatture hooks create post-invoice-send
        openfatture hooks create on-payment-matched --template python
    """
    registry = get_hook_registry()

    # Determine script extension
    if template == "python":
        extension = ".py"
    else:
        extension = ".sh"

    script_path = registry.hooks_dir / f"{name}{extension}"

    # Check if already exists
    if script_path.exists():
        console.print(f"[yellow]Hook '{name}' already exists at:[/yellow]")
        console.print(f"  {script_path}")
        console.print("\n[dim]Edit the file or choose a different name.[/dim]")
        return

    # Create hook from template
    if template == "bash":
        content = _bash_template(name)
    elif template == "python":
        content = _python_template(name)
    else:
        console.print(f"[red]Unknown template: {template}[/red]")
        console.print("[dim]Available templates: bash, python[/dim]")
        raise typer.Exit(1)

    # Write file
    script_path.write_text(content, encoding="utf-8")

    # Make executable (bash scripts)
    if extension == ".sh":
        script_path.chmod(0o755)

    console.print(f"[green]✓ Hook created: {name}[/green]\n")
    console.print(f"[cyan]Path:[/cyan] {script_path}")
    console.print(f"[cyan]Template:[/cyan] {template}")
    console.print("\n[dim]Edit the hook script to customize its behavior.[/dim]")
    console.print(f"[dim]Test it with: openfatture hooks test {name}[/dim]\n")

    # Reload registry
    registry.reload()


@app.command("info")
def hook_info(
    name: str = typer.Argument(..., help="Hook name"),
) -> None:
    """Show detailed information about a hook.

    Examples:
        openfatture hooks info post-invoice-send
    """
    registry = get_hook_registry()
    hook_config = registry.get_hook(name)

    if not hook_config:
        console.print(f"[red]Hook '{name}' not found[/red]")
        raise typer.Exit(1)

    # Parse metadata
    metadata = HookMetadata.from_script(hook_config.script_path)

    console.print(f"\n[bold blue]Hook: {name}[/bold blue]\n")

    # Info table
    info = Table(show_header=False, box=None)
    info.add_column("Field", style="cyan", width=20)
    info.add_column("Value", style="white")

    info.add_row("Script Path", str(hook_config.script_path))
    info.add_row("Enabled", "✓ Yes" if hook_config.enabled else "✗ No")
    info.add_row("Timeout", f"{hook_config.timeout_seconds}s")
    info.add_row("Fail on Error", "Yes" if hook_config.fail_on_error else "No")

    if metadata.description:
        info.add_row("Description", metadata.description)
    if metadata.author:
        info.add_row("Author", metadata.author)
    if metadata.requires:
        info.add_row("Requires", ", ".join(metadata.requires))

    console.print(info)

    # Show script preview
    console.print("\n[bold]Script Preview:[/bold]")
    try:
        script_content = hook_config.script_path.read_text(encoding="utf-8")
        # Show first 20 lines
        lines = script_content.split("\n")[:20]
        preview = "\n".join(lines)
        if len(script_content.split("\n")) > 20:
            preview += "\n..."

        console.print(Syntax(preview, "bash", theme="monokai", line_numbers=True))
    except Exception as e:
        console.print(f"[red]Could not read script: {e}[/red]")

    console.print()


def _bash_template(name: str) -> str:
    """Generate bash hook template."""
    return f"""#!/bin/bash
# DESCRIPTION: {name} hook
# AUTHOR: Your Name
# TIMEOUT: 30
# REQUIRES: curl

# This hook is triggered by the {name} event.
# Environment variables are injected automatically:
#   OPENFATTURE_HOOK_NAME={name}
#   OPENFATTURE_EVENT_TYPE=<EventClassName>
#   OPENFATTURE_EVENT_ID=<UUID>
#   OPENFATTURE_EVENT_DATA=<JSON>
#   OPENFATTURE_INVOICE_ID=<id>
#   OPENFATTURE_INVOICE_NUMBER=<number>
#   ... (depends on event type)

# Example: Send notification
echo "Hook {name} triggered!"
echo "Event: $OPENFATTURE_EVENT_TYPE"
echo "Event ID: $OPENFATTURE_EVENT_ID"

# Parse event data with jq
INVOICE_NUMBER=$(echo "$OPENFATTURE_EVENT_DATA" | jq -r '.invoice_number // "N/A"')
echo "Invoice: $INVOICE_NUMBER"

# Your custom logic here
# Example: Send Slack notification
# curl -X POST "$SLACK_WEBHOOK" \\
#   -H 'Content-Type: application/json' \\
#   -d "{{\\"text\\": \\"Invoice $INVOICE_NUMBER created!\\"}}"

exit 0
"""


def _python_template(name: str) -> str:
    """Generate Python hook template."""
    return f"""#!/usr/bin/env python3
\"\"\"
DESCRIPTION: {name} hook
AUTHOR: Your Name
TIMEOUT: 30
REQUIRES: requests
\"\"\"

import json
import os
import sys

def main():
    \"\"\"Hook entry point.\"\"\"
    # Environment variables are injected automatically
    hook_name = os.getenv("OPENFATTURE_HOOK_NAME")
    event_type = os.getenv("OPENFATTURE_EVENT_TYPE")
    event_id = os.getenv("OPENFATTURE_EVENT_ID")
    event_data_json = os.getenv("OPENFATTURE_EVENT_DATA")

    print(f"Hook {{hook_name}} triggered!")
    print(f"Event: {{event_type}}")
    print(f"Event ID: {{event_id}}")

    # Parse event data
    event_data = json.loads(event_data_json)
    invoice_number = event_data.get("invoice_number", "N/A")
    print(f"Invoice: {{invoice_number}}")

    # Your custom logic here
    # Example: Send notification, update database, trigger workflow, etc.

    return 0


if __name__ == "__main__":
    sys.exit(main())
"""
