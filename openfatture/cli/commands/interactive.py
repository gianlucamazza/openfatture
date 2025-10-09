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
    [bold blue]🚀 OpenFatture - Modalità Interattiva[/bold blue]

    [dim]Benvenuto nella modalità interattiva di OpenFatture![/dim]
    [dim]Usa i tasti [bold]↑↓[/bold] per navigare e [bold]INVIO[/bold] per selezionare.[/dim]
    [dim]Premi [bold]Ctrl+C[/bold] in qualsiasi momento per uscire.[/dim]
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
    console.print("\n[bold green]👋 Grazie per aver usato OpenFatture![/bold green]")
    console.print(
        "[dim]Per tornare alla modalità interattiva: [cyan]openfatture interactive start[/cyan][/dim]\n"
    )


if __name__ == "__main__":
    app()
