"""UI Renderer for Interactive Chat."""

from datetime import datetime

from rich.align import Align
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text


class ChatRenderer:
    """
    Handles UI rendering for the interactive chat.

    Separates presentation logic from chat flow control.
    """

    def __init__(self, console: Console | None = None) -> None:
        """Initialize renderer."""
        self.console = console or Console()
        self._panel_width: int | None = None

    @property
    def panel_width(self) -> int:
        """Get cached panel width."""
        if self._panel_width is None:
            self._panel_width = min(int(self.console.width * 0.8), 120)
        return self._panel_width

    def show_welcome(self, provider_name: str, model_name: str) -> None:
        """Show welcome header."""
        header = Panel.fit(
            "[bold blue]OpenFatture AI Assistant[/bold blue]\n"
            f"[dim]Sessione attiva • Provider: {provider_name} • Modello: {model_name}[/dim]\n"
            "[dim]Comandi: /help /tools /stats /save /clear /exit[/dim]",
            border_style="blue",
            padding=(0, 1),
        )
        self.console.print(header)
        self.console.print()

    def show_goodbye(self) -> None:
        """Show goodbye message."""
        self.console.print("\n[blue]Grazie per aver usato OpenFatture AI. A presto! [/blue]\n")

    def display_user_message(self, message: str) -> None:
        """Display user message in bubble."""
        timestamp = datetime.now().strftime("%H:%M")
        bubble = Panel(
            f"[bold white]{message}[/bold white]",
            border_style="blue",
            padding=(0, 1),
            title=f"[dim]Tu • {timestamp}[/dim]",
            title_align="right",
            width=self.panel_width,
        )
        self.console.print(Align.right(bubble, width=self.panel_width))
        self.console.print()

    def display_ai_message(self, content: str) -> None:
        """Display AI message in bubble."""
        timestamp = datetime.now().strftime("%H:%M")

        # Render markdown first to avoid raw text issues
        md = Markdown(content)

        bubble = Panel(
            md,
            border_style="green",
            padding=(0, 1),
            title=f"[dim]AI • {timestamp}[/dim]",
            title_align="left",
            width=self.panel_width,
        )
        self.console.print(bubble)
        self.console.print()

    def display_error(self, error_message: str, context: str = "Errore") -> None:
        """Display error message."""
        error_bubble = Panel(
            f"[red]{context}:[/red] {error_message}\n\n"
            "[yellow]Suggerimenti:[/yellow]\n"
            "• Riprova il messaggio\n"
            "• Usa /help per assistenza\n"
            "• Controlla la connessione",
            title="Errore Rilevato",
            border_style="red",
            padding=(1, 2),
            width=self.panel_width,
        )
        self.console.print(error_bubble)
        self.console.print()

    def get_mini_stats_str(
        self, message_count: int, total_tokens: int, total_cost_usd: float
    ) -> str:
        """Get mini stats string."""
        return (
            f"[dim]Msgs: {message_count} | "
            f"Tokens: {total_tokens} | "
            f"Cost: ${total_cost_usd:.4f}[/dim]"
        )

    def create_live_content(
        self, content: str = "", progress_chunks: list[str] | None = None
    ) -> Panel:
        """Create content for Live display during streaming."""
        timestamp = datetime.now().strftime("%H:%M")

        if not content:
            content = "..."

        md_content = Markdown(content)
        renderables = [md_content]

        if progress_chunks:
            progress_text = Text("\n".join(progress_chunks), style="dim italic")
            renderables.append(Text("\n"))
            renderables.append(
                Panel(
                    progress_text,
                    border_style="dim",
                    title="[dim]Attività[/dim]",
                    title_align="left",
                )
            )

        group = Group(*renderables)

        return Panel(
            group,
            border_style="green",
            padding=(0, 1),
            title=f"[dim]AI • {timestamp}[/dim]",
            title_align="left",
            width=self.panel_width,
        )

    def create_thinking_panel(self) -> Panel:
        """Create initial thinking panel."""
        timestamp = datetime.now().strftime("%H:%M")
        return Panel(
            "AI sta pensando...",
            border_style="green",
            padding=(0, 1),
            title=f"[dim]AI • {timestamp}[/dim]",
            title_align="left",
            width=self.panel_width,
        )
