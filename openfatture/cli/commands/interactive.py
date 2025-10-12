"""Interactive mode with menus for OpenFatture."""

import typer
from rich.console import Console
from rich.panel import Panel

from openfatture.cli.ui.menus import handle_main_menu, show_main_menu

app = typer.Typer()
console = Console()


@app.command("start")
def interactive_mode() -> None:
    """
    🎯 Launch interactive mode with menus.

    Navigate with arrow keys, select with Enter.
    Press Ctrl+C to exit at any time.

    Example:
        openfatture interactive start
    """
    show_welcome()

    while True:
        try:
            choice = show_main_menu()

            # Handle exit
            if not choice or "Esci" in choice:
                show_goodbye()
                break

            # Process menu selection
            should_continue = handle_main_menu(choice)

            if not should_continue:
                show_goodbye()
                break

        except KeyboardInterrupt:
            console.print("\n\n[yellow]⚠ Interrupted by user.[/yellow]")
            show_goodbye()
            break
        except Exception as e:
            console.print(f"\n[red]❌ Error: {e}[/red]")
            console.print("[dim]Press Ctrl+C to exit or continue with another action.[/dim]")


def show_welcome() -> None:
    """Display welcome message."""
    welcome_text = """
    [bold blue]🚀 OpenFatture - Interactive Mode[/bold blue]

    [dim]Welcome to OpenFatture's interactive mode![/dim]
    [dim]Use [bold]↑↓[/bold] to navigate and [bold]ENTER[/bold] to select.[/dim]
    [dim]Press [bold]Ctrl+C[/bold] at any time to exit.[/dim]
    """

    console.print(
        Panel(
            welcome_text,
            border_style="blue",
            padding=(1, 2),
        )
    )


def show_goodbye() -> None:
    """Display goodbye message."""
    console.print("\n[bold green]👋 Thanks for using OpenFatture![/bold green]")
    console.print(
        "[dim]To restart interactive mode: [cyan]openfatture interactive start[/cyan][/dim]\n"
    )


if __name__ == "__main__":
    app()
