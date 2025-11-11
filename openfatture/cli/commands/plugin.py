"""Plugin management CLI commands."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from ...plugins import PluginDiscovery, get_plugin_registry

app = typer.Typer(help="Manage OpenFatture plugins", no_args_is_help=True)
console = Console()


@app.command("list")
def list_plugins(
    show_disabled: bool = typer.Option(
        False, "--all", "-a", help="Show all plugins (including disabled)"
    ),
) -> None:
    """List all registered plugins.

    Examples:
        openfatture plugin list
        openfatture plugin list --all
    """
    registry = get_plugin_registry()
    plugins = registry.list_plugins()

    if not plugins:
        console.print("[yellow]No plugins registered[/yellow]")
        console.print("\n[dim]To discover plugins, run: openfatture plugin discover[/dim]")
        return

    # Create table
    table = Table(title=f"Plugins ({len(plugins)} registered)", show_lines=False)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Version", style="yellow", justify="center")
    table.add_column("Status", style="green", justify="center")
    table.add_column("Description", style="white")
    table.add_column("Author", style="blue")

    for plugin in plugins:
        status = "✅ Enabled" if registry.is_enabled(plugin.metadata.name) else "❌ Disabled"
        if not show_disabled and not registry.is_enabled(plugin.metadata.name):
            continue

        table.add_row(
            plugin.metadata.name,
            plugin.metadata.version,
            status,
            (
                plugin.metadata.description[:50] + "..."
                if len(plugin.metadata.description) > 50
                else plugin.metadata.description
            ),
            plugin.metadata.author,
        )

    console.print()
    console.print(table)
    console.print()


@app.command("enable")
def enable_plugin(
    name: str = typer.Argument(..., help="Plugin name to enable"),
) -> None:
    """Enable a plugin.

    Examples:
        openfatture plugin enable lightning
    """
    registry = get_plugin_registry()

    if registry.enable_plugin(name):
        console.print(f"[green]✅ Plugin '{name}' enabled[/green]")
        console.print("\n[dim]Restart OpenFatture to apply changes[/dim]")
    else:
        console.print(f"[red]❌ Plugin '{name}' not found[/red]")
        console.print("\n[dim]Available plugins:[/dim]")
        for plugin in registry.list_plugins():
            console.print(f"  • {plugin.metadata.name}")


@app.command("disable")
def disable_plugin(
    name: str = typer.Argument(..., help="Plugin name to disable"),
) -> None:
    """Disable a plugin.

    Examples:
        openfatture plugin disable lightning
    """
    registry = get_plugin_registry()

    if registry.disable_plugin(name):
        console.print(f"[yellow]Plugin '{name}' disabled[/yellow]")
        console.print("\n[dim]Restart OpenFatture to apply changes[/dim]")
    else:
        console.print(f"[red]❌ Plugin '{name}' not found or already disabled[/red]")


@app.command("discover")
def discover_plugins(
    plugin_dir: Path = typer.Option(
        None, "--dir", help="Plugin directory to search (default: ~/.openfatture/plugins)"
    ),
) -> None:
    """Discover and register plugins from directories.

    Examples:
        openfatture plugin discover
        openfatture plugin discover --dir /path/to/plugins
    """
    if plugin_dir is None:
        plugin_dir = Path.home() / ".openfatture" / "plugins"

    console.print(f"[bold blue]🔍 Discovering plugins in: {plugin_dir}[/bold blue]\n")

    discovery = PluginDiscovery([plugin_dir])
    plugins = discovery.discover_plugins()

    if not plugins:
        console.print("[yellow]No plugins found[/yellow]")
        console.print(f"\n[dim]Create plugins in: {plugin_dir}[/dim]")
        console.print("[dim]Each plugin should be a directory with plugin.py or __init__.py[/dim]")
        return

    # Register discovered plugins
    registry = get_plugin_registry()
    registered_count = 0

    for plugin in plugins:
        try:
            registry.register_plugin(plugin)
            registered_count += 1
            console.print(
                f"[green]✅ Registered:[/green] {plugin.metadata.name} v{plugin.metadata.version}"
            )
        except Exception as e:
            console.print(f"[red]❌ Failed to register {plugin.metadata.name}: {e}[/red]")

    console.print(f"\n[bold green]🎉 Registered {registered_count} plugin(s)[/bold green]")

    if registered_count > 0:
        console.print("\n[dim]Use 'openfatture plugin list' to see all plugins[/dim]")
        console.print("[dim]Use 'openfatture plugin enable <name>' to enable plugins[/dim]")


@app.command("info")
def plugin_info(
    name: str = typer.Argument(..., help="Plugin name"),
) -> None:
    """Show detailed information about a plugin.

    Examples:
        openfatture plugin info lightning
    """
    registry = get_plugin_registry()
    plugin = registry.get_plugin(name)

    if not plugin:
        console.print(f"[red]❌ Plugin '{name}' not found[/red]")
        return

    metadata = plugin.metadata

    console.print(f"\n[bold blue]🔌 Plugin: {metadata.name}[/bold blue]\n")

    # Info table
    info = Table(show_header=False, box=None)
    info.add_column("Field", style="cyan", width=20)
    info.add_column("Value", style="white")

    info.add_row("Name", metadata.name)
    info.add_row("Version", metadata.version)
    info.add_row("Description", metadata.description)
    info.add_row("Author", metadata.author)
    info.add_row("Compatible Versions", metadata.compatible_versions)
    info.add_row("Enabled", "✅ Yes" if registry.is_enabled(name) else "❌ No")

    if metadata.homepage:
        info.add_row("Homepage", metadata.homepage)
    if metadata.license:
        info.add_row("License", metadata.license)
    if metadata.requires:
        info.add_row("Dependencies", ", ".join(metadata.requires))

    console.print(info)
    console.print()


@app.command("install")
def install_plugin(
    package: str = typer.Argument(..., help="Plugin package name or URL"),
) -> None:
    """Install a plugin from PyPI or URL.

    Examples:
        openfatture plugin install openfatture-plugin-lightning
        openfatture plugin install https://github.com/user/plugin-repo.git
    """
    console.print(f"[bold blue]📦 Installing plugin: {package}[/bold blue]\n")

    # For now, just show placeholder - actual implementation would use pip
    console.print("[yellow]⚠️  Plugin installation not yet implemented[/yellow]")
    console.print("[dim]This feature will be available in a future version[/dim]")
    console.print("\n[dim]For now, manually install plugins with:[/dim]")
    console.print(f"[dim]  pip install {package}[/dim]")
    console.print("[dim]Then run: openfatture plugin discover[/dim]")


@app.command("uninstall")
def uninstall_plugin(
    name: str = typer.Argument(..., help="Plugin name to uninstall"),
) -> None:
    """Uninstall a plugin.

    Examples:
        openfatture plugin uninstall lightning
    """
    console.print(f"[bold blue]🗑️  Uninstalling plugin: {name}[/bold blue]\n")

    # For now, just show placeholder
    console.print("[yellow]⚠️  Plugin uninstallation not yet implemented[/yellow]")
    console.print("[dim]This feature will be available in a future version[/dim]")
    console.print("\n[dim]For now, manually uninstall with:[/dim]")
    console.print(f"[dim]  pip uninstall openfatture-plugin-{name}[/dim]")
