"""Progress bar utilities for long operations."""

from collections.abc import Callable
from typing import TypeVar

from rich.console import Console
from rich.live import Live
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.spinner import Spinner

console = Console()
T = TypeVar("T")


def create_progress() -> Progress:
    """
    Create a Rich progress bar with OpenFatture style.

    Returns:
        Configured Progress instance
    """
    return Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=40),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    )


def process_with_progress(
    items: list[T],
    process_fn: Callable[[T], tuple[bool, str | None]],
    description: str = "Elaborazione...",
    success_message: str = "Completato",
    error_message: str = "Errori riscontrati",
) -> tuple[int, int, list[str]]:
    """
    Process items with progress bar.

    Args:
        items: List of items to process
        process_fn: Function to process each item, returns (success, error_message)
        description: Task description
        success_message: Message on success
        error_message: Message on error

    Returns:
        Tuple of (success_count, error_count, error_messages)
    """
    success_count = 0
    error_count = 0
    errors = []

    with create_progress() as progress:
        task = progress.add_task(description, total=len(items))

        for item in items:
            success, error = process_fn(item)

            if success:
                success_count += 1
            else:
                error_count += 1
                if error:
                    errors.append(error)

            progress.update(task, advance=1)

    # Show summary
    if error_count == 0:
        console.print(f"\n[green]✓ {success_message}: {success_count}/{len(items)}[/green]")
    else:
        console.print(f"\n[yellow]⚠ {success_count} successi, {error_count} errori[/yellow]")
        console.print(f"\n[red]{error_message}:[/red]")
        for i, err in enumerate(errors[:5], 1):  # Show max 5 errors
            console.print(f"  {i}. {err}")
        if len(errors) > 5:
            console.print(f"  ... e altri {len(errors) - 5} errori")

    return success_count, error_count, errors


def with_spinner(
    fn: Callable[[], T],
    message: str = "Elaborazione...",
    success_message: str = "Completato!",
) -> T:
    """
    Execute function with a spinner.

    Args:
        fn: Function to execute
        message: Message to show while running
        success_message: Message on success

    Returns:
        Function result
    """
    with Live(
        Spinner("dots", text=f"[bold blue]{message}[/bold blue]"),
        console=console,
        refresh_per_second=10,
    ) as live:
        result = fn()
        live.update(f"[green]✓ {success_message}[/green]")

    return result


def with_progress_message(message: str) -> Progress:
    """
    Create a simple progress bar with just a message.

    Useful for operations where you don't know the total count.

    Args:
        message: Message to display

    Returns:
        Progress instance (remember to call .start() and .stop())

    Example:
        progress = with_progress_message("Processing...")
        progress.start()
        # ... do work ...
        progress.stop()
        console.print("[green]Done![/green]")
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}[/bold blue]"),
        console=console,
    )
