"""Interactive chat UI for AI assistant."""

import asyncio
from typing import Optional

import questionary
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from openfatture.ai.agents.chat_agent import ChatAgent
from openfatture.ai.context import enrich_chat_context
from openfatture.ai.domain.context import ChatContext
from openfatture.ai.domain.message import Role
from openfatture.ai.providers.factory import create_provider
from openfatture.ai.session import ChatSession, SessionManager
from openfatture.cli.ui.styles import openfatture_style
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)
console = Console()


class InteractiveChatUI:
    """
    Interactive chat interface with Rich UI.

    Features:
    - Beautiful terminal UI with Rich
    - Multi-turn conversations
    - Session persistence
    - Command shortcuts
    - Token/cost tracking
    - Markdown rendering
    """

    def __init__(
        self,
        session: Optional[ChatSession] = None,
        session_manager: Optional[SessionManager] = None,
    ) -> None:
        """
        Initialize chat UI.

        Args:
            session: Existing session to resume (creates new if None)
            session_manager: Session manager (creates new if None)
        """
        self.session = session or ChatSession()
        self.session_manager = session_manager or SessionManager()
        self.agent: Optional[ChatAgent] = None
        self.provider = None

        # Commands
        self.commands = {
            "/help": self._show_help,
            "/clear": self._clear_chat,
            "/save": self._save_session,
            "/export": self._export_session,
            "/stats": self._show_stats,
            "/tools": self._show_tools,
            "/exit": self._exit_chat,
            "/quit": self._exit_chat,
        }

    async def start(self) -> None:
        """Start the interactive chat loop."""
        try:
            # Initialize provider and agent
            self._initialize_agent()

            # Show welcome
            self._show_welcome()

            # Chat loop
            while True:
                try:
                    # Get user input
                    user_input = await self._get_user_input()

                    if not user_input:
                        continue

                    # Check for commands
                    if user_input.startswith("/"):
                        command_result = await self._handle_command(user_input)
                        if command_result == "exit":
                            break
                        continue

                    # Process message
                    await self._process_message(user_input)

                except KeyboardInterrupt:
                    console.print("\n[yellow]Usa /exit per uscire dalla chat[/yellow]")
                    continue

                except Exception as e:
                    logger.error("chat_error", error=str(e))
                    console.print(f"\n[red]Errore: {e}[/red]")
                    continue

        finally:
            # Save session on exit
            if self.session.metadata.message_count > 0:
                self._auto_save()

            self._show_goodbye()

    def _initialize_agent(self) -> None:
        """Initialize LLM provider and agent."""
        console.print("[dim]Inizializzazione AI...[/dim]")

        try:
            # Create provider
            self.provider = create_provider()

            # Create agent with streaming enabled
            self.agent = ChatAgent(
                provider=self.provider,
                enable_tools=True,
                enable_streaming=True,
            )

            logger.info(
                "chat_agent_initialized",
                provider=self.provider.provider_name,
                model=self.provider.model,
                streaming_enabled=True,
            )

        except Exception as e:
            console.print(f"[red]Errore nell'inizializzazione: {e}[/red]")
            raise

    def _show_welcome(self) -> None:
        """Show welcome message."""
        welcome_text = f"""
[bold blue]🤖 OpenFatture AI Assistant[/bold blue]

Ciao! Sono il tuo assistente per la fatturazione elettronica.

[bold]Posso aiutarti a:[/bold]
• Cercare fatture e clienti
• Fornire statistiche e analytics
• Rispondere a domande sulla fatturazione
• Guidarti attraverso i workflow

[bold]Comandi disponibili:[/bold]
/help     - Mostra aiuto
/tools    - Mostra strumenti disponibili
/stats    - Mostra statistiche sessione
/save     - Salva conversazione
/export   - Esporta conversazione
/clear    - Pulisci chat
/exit     - Esci

[dim]Session ID: {self.session.id[:8]}...[/dim]
[dim]Provider: {self.provider.provider_name if self.provider else 'N/A'} | Model: {self.provider.model if self.provider else 'N/A'}[/dim]
"""

        console.print(Panel(welcome_text, border_style="blue"))
        console.print()

    async def _get_user_input(self) -> str:
        """Get user input."""
        # Show token counter
        self._show_mini_stats()

        # Get input
        user_input = questionary.text(
            "Tu:",
            style=openfatture_style,
            qmark="",
        ).ask()

        return user_input.strip() if user_input else ""

    async def _process_message(self, user_input: str) -> None:
        """
        Process user message and get AI response.

        Args:
            user_input: User message
        """
        # Add user message to session
        self.session.add_user_message(user_input)

        # Build context
        context = self._build_context(user_input)

        try:
            # Check if streaming is enabled
            if self.agent.config.streaming_enabled:
                # Stream response with real-time rendering
                await self._process_message_streaming(context)
            else:
                # Use non-streaming mode (fallback)
                await self._process_message_non_streaming(context)

        except Exception as e:
            logger.error("message_processing_failed", error=str(e))
            console.print(f"\n[red]Errore nell'elaborazione: {e}[/red]\n")

    async def _process_message_streaming(self, context: ChatContext) -> None:
        """
        Process message with streaming response.

        Args:
            context: Chat context
        """
        console.print("\n[bold cyan]AI:[/bold cyan]")

        # Collect response chunks for session storage
        full_response = ""

        try:
            # Stream response with Live rendering
            with Live("", console=console, refresh_per_second=10) as live:
                async for chunk in self.agent.execute_stream(context):
                    full_response += chunk
                    # Update live display with markdown
                    live.update(Markdown(full_response))

            console.print()  # Add newline after response

            # Add assistant message to session
            # Note: Token count is estimated in streaming mode
            estimated_tokens = len(full_response) // 4
            estimated_cost = estimated_tokens * 0.00001  # Rough estimate

            self.session.add_assistant_message(
                full_response,
                provider=self.provider.provider_name,
                model=self.provider.model,
                tokens=estimated_tokens,
                cost=estimated_cost,
            )

            # Auto-save if configured
            if self.session.auto_save:
                self._auto_save()

        except Exception as e:
            logger.error("streaming_failed", error=str(e))
            console.print(f"\n[red]Errore nello streaming: {e}[/red]\n")

    async def _process_message_non_streaming(self, context: ChatContext) -> None:
        """
        Process message without streaming (fallback).

        Args:
            context: Chat context
        """
        # Show "thinking" indicator
        with console.status("[bold green]AI sta pensando...") as status:
            try:
                # Execute agent
                response = await self.agent.execute(context)

                status.stop()

                # Check for errors
                if response.status.value == "error":
                    console.print(f"\n[red]❌ Errore: {response.error}[/red]\n")
                    return

                # Add assistant message to session
                self.session.add_assistant_message(
                    response.content,
                    provider=response.provider,
                    model=response.model,
                    tokens=response.usage.total_tokens,
                    cost=response.usage.estimated_cost_usd,
                )

                # Display response
                self._display_response(response.content)

                # Auto-save if configured
                if self.session.auto_save:
                    self._auto_save()

            except Exception as e:
                status.stop()
                logger.error("non_streaming_failed", error=str(e))
                console.print(f"\n[red]Errore nell'elaborazione: {e}[/red]\n")

    def _build_context(self, user_input: str) -> ChatContext:
        """
        Build chat context for agent.

        Args:
            user_input: User message

        Returns:
            Enriched ChatContext
        """
        # Create base context
        context = ChatContext(
            user_input=user_input,
            session_id=self.session.id,
            enable_tools=True,
        )

        # Add conversation history from session
        for msg in self.session.get_messages(include_system=False):
            context.conversation_history.add_message(msg)

        # Add available tools
        if self.agent:
            context.available_tools = self.agent.get_available_tools()

        # Enrich with business data
        context = enrich_chat_context(context)

        return context

    def _display_response(self, content: str) -> None:
        """
        Display AI response with markdown rendering.

        Args:
            content: Response content
        """
        # Render as markdown
        md = Markdown(content)

        console.print("\n[bold cyan]AI:[/bold cyan]")
        console.print(md)
        console.print()

    def _show_mini_stats(self) -> None:
        """Show mini stats bar."""
        stats = (
            f"[dim]Msgs: {self.session.metadata.message_count} | "
            f"Tokens: {self.session.metadata.total_tokens} | "
            f"Cost: ${self.session.metadata.total_cost_usd:.4f}[/dim]"
        )
        console.print(stats)

    async def _handle_command(self, command: str) -> Optional[str]:
        """
        Handle chat command.

        Args:
            command: Command string

        Returns:
            "exit" to exit chat, None to continue
        """
        # Parse command (handle arguments)
        parts = command.split()
        cmd = parts[0].lower()

        if cmd in self.commands:
            return await self.commands[cmd]()
        else:
            console.print(f"[yellow]Comando sconosciuto: {cmd}[/yellow]")
            console.print("[dim]Usa /help per vedere i comandi disponibili[/dim]")
            return None

    async def _show_help(self) -> None:
        """Show help message."""
        help_text = """
[bold]Comandi Disponibili:[/bold]

/help     - Mostra questo messaggio
/tools    - Mostra strumenti AI disponibili
/stats    - Mostra statistiche conversazione
/save     - Salva conversazione corrente
/export   - Esporta in Markdown o JSON
/clear    - Pulisci messaggi (mantieni sessione)
/exit     - Esci dalla chat

[bold]Esempi di domande:[/bold]

• "Quante fatture ho emesso quest'anno?"
• "Cerca fatture del cliente Rossi"
• "Mostrami le ultime 5 fatture"
• "Quali sono i clienti con più fatture?"
• "Dammi un riepilogo dell'anno corrente"
"""

        console.print(Panel(help_text, title="Aiuto", border_style="blue"))
        return None

    async def _clear_chat(self) -> None:
        """Clear chat messages."""
        if questionary.confirm(
            "Vuoi davvero cancellare tutti i messaggi?",
            default=False,
            style=openfatture_style,
        ).ask():
            self.session.clear_messages(keep_system=True)
            console.print("[green]✓ Chat pulita[/green]\n")
        return None

    async def _save_session(self) -> None:
        """Save current session."""
        if self.session_manager.save_session(self.session):
            console.print(f"[green]✓ Sessione salvata: {self.session.id[:8]}...[/green]\n")
        else:
            console.print("[red]✗ Errore nel salvataggio[/red]\n")
        return None

    async def _export_session(self) -> None:
        """Export session to file."""
        # Ask format
        format_choice = questionary.select(
            "Formato di export:",
            choices=["Markdown", "JSON"],
            style=openfatture_style,
        ).ask()

        format_type = format_choice.lower()

        # Export
        output_path = self.session_manager.export_session(
            self.session.id,
            format=format_type,
        )

        if output_path:
            console.print(f"[green]✓ Esportato in: {output_path}[/green]\n")
        else:
            console.print("[red]✗ Errore nell'export[/red]\n")

        return None

    async def _show_stats(self) -> None:
        """Show session statistics."""
        table = Table(title="Statistiche Sessione", show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Session ID", self.session.id[:16] + "...")
        table.add_row("Titolo", self.session.metadata.title)
        table.add_row("Messaggi", str(self.session.metadata.message_count))
        table.add_row("Token totali", str(self.session.metadata.total_tokens))
        table.add_row("Costo totale", f"${self.session.metadata.total_cost_usd:.4f}")
        table.add_row("Provider", self.session.metadata.primary_provider or "N/A")
        table.add_row("Model", self.session.metadata.primary_model or "N/A")

        if self.session.metadata.tools_used:
            table.add_row("Tools usati", ", ".join(self.session.metadata.tools_used))

        console.print()
        console.print(table)
        console.print()

        return None

    async def _show_tools(self) -> None:
        """Show available tools."""
        if not self.agent:
            console.print("[yellow]Agent non inizializzato[/yellow]\n")
            return None

        tools = self.agent.tool_registry.list_tools()

        table = Table(title="Strumenti AI Disponibili")
        table.add_column("Nome", style="cyan")
        table.add_column("Categoria", style="yellow")
        table.add_column("Descrizione", style="white")

        for tool in tools:
            table.add_column(tool.name, tool.category, tool.description)

        console.print()
        console.print(table)
        console.print()

        return None

    async def _exit_chat(self) -> str:
        """Exit chat."""
        return "exit"

    def _auto_save(self) -> None:
        """Auto-save session."""
        try:
            self.session_manager.save_session(self.session)
            logger.debug("session_auto_saved", session_id=self.session.id)
        except Exception as e:
            logger.warning("session_auto_save_failed", error=str(e))

    def _show_goodbye(self) -> None:
        """Show goodbye message."""
        summary = self.session.get_summary()

        goodbye_text = f"""
[bold green]👋 Grazie per aver usato OpenFatture AI![/bold green]

[bold]Riepilogo conversazione:[/bold]
{summary}

[dim]La sessione è stata salvata automaticamente.[/dim]
[dim]Per riprendere: usa il comando interactive > AI Assistant[/dim]
"""

        console.print(Panel(goodbye_text, border_style="green"))


async def start_interactive_chat(
    session_id: Optional[str] = None,
) -> None:
    """
    Start interactive chat session.

    Args:
        session_id: Resume existing session (creates new if None)
    """
    # Create or load session
    session_manager = SessionManager()

    if session_id:
        session = session_manager.load_session(session_id)
        if not session:
            console.print(f"[red]Sessione {session_id} non trovata[/red]")
            session = None
    else:
        session = None

    # Create UI and start
    ui = InteractiveChatUI(session=session, session_manager=session_manager)
    await ui.start()
