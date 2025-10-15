"""Interactive chat UI for AI assistant."""

from typing import cast

import questionary
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from openfatture.ai.agents.chat_agent import ChatAgent
from openfatture.ai.context import enrich_chat_context, enrich_with_rag
from openfatture.ai.domain.context import ChatContext
from openfatture.ai.domain.message import Message
from openfatture.ai.providers.base import BaseLLMProvider
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
        session: ChatSession | None = None,
        session_manager: SessionManager | None = None,
    ) -> None:
        """
        Initialize chat UI.

        Args:
            session: Existing session to resume (creates new if None)
            session_manager: Session manager (creates new if None)
        """
        self.session = session or ChatSession()
        self.session_manager = session_manager or SessionManager()
        self.agent: ChatAgent | None = None
        self.provider: BaseLLMProvider | None = None

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
            provider = create_provider()
            if provider is None:
                raise RuntimeError("Provider initialization failed.")

            # Create agent with streaming enabled
            self.agent = ChatAgent(
                provider=provider,
                enable_tools=True,
                enable_streaming=True,
            )

            self.provider = provider

            logger.info(
                "chat_agent_initialized",
                provider=provider.provider_name,
                model=provider.model,
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
        user_input = await questionary.text(
            "Tu:",
            style=openfatture_style,
            qmark="",
        ).ask_async()

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
        context = await self._build_context(user_input)

        try:
            # Check if streaming is enabled
            if self.agent is None:
                raise RuntimeError("Agent not initialized. Call _initialize_agent() first.")
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

        Best Practice (2025): Separate transient progress from persistent content.
        - Progress indicators (🔧, ✅, ❌, 📊, ⏱️) are printed directly
        - Content is streamed via Live display

        Args:
            context: Chat context
        """
        console.print("\n[bold cyan]AI:[/bold cyan]")

        # Collect response chunks for session storage
        full_response = ""
        content_chunks = []  # Only actual content (no progress messages)

        try:
            if self.agent is None:
                raise RuntimeError("Agent not initialized. Call _initialize_agent() first.")

            # Stream response with Live rendering for content
            with Live("", console=console, refresh_per_second=10) as live:
                async for chunk in self.agent.execute_stream(context):
                    full_response += chunk

                    # Detect progress messages vs content
                    # Progress messages start with: \n\n🔧, \n  (numbered), "     " (indented results), \n📊, ⏱️
                    is_progress = (
                        chunk.startswith("\n\n🔧")
                        or chunk.startswith("\n  ")
                        or chunk.startswith("     ")
                        or chunk.startswith("\n📊")
                        or chunk.startswith("⏱️")
                        or chunk.startswith("\n\n🤖 Continuando")
                    )

                    if is_progress:
                        # Print progress directly (transient, outside Live)
                        # Stop Live temporarily to print progress
                        live.stop()
                        console.print(chunk, end="", style="dim")
                        live.start()
                    else:
                        # Accumulate content and update Live display
                        content_chunks.append(chunk)
                        if content_chunks:  # Only update if we have content
                            live.update(Markdown("".join(content_chunks)))

            console.print()  # Add newline after response

            # Add assistant message to session
            # Note: Token count is estimated in streaming mode
            estimated_tokens = len(full_response) // 4
            estimated_cost = estimated_tokens * 0.00001  # Rough estimate

            if self.provider is None:
                raise RuntimeError("Provider not initialized.")

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
        if self.agent is None:
            raise RuntimeError("Agent not initialized. Call _initialize_agent() first.")

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

    async def _build_context(self, user_input: str) -> ChatContext:
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
        for chat_message in self.session.get_messages(include_system=False):
            context.conversation_history.add_message(
                Message(
                    role=chat_message.role,
                    content=chat_message.content,
                    metadata=chat_message.metadata,
                    tool_call_id=chat_message.tool_call_id,
                )
            )

        # Add available tools
        if self.agent:
            context.available_tools = self.agent.get_available_tools()

        # Enrich with business data
        context = enrich_chat_context(context)

        # Optional RAG enrichment (knowledge + invoices)
        cleaned_input = user_input.strip()
        if self.agent and self.agent.config.rag_enabled and len(cleaned_input) >= 4:
            try:
                context = cast(ChatContext, await enrich_with_rag(context, cleaned_input))
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning(
                    "rag_enrichment_skipped",
                    error=str(exc),
                )

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

    async def _handle_command(self, command: str) -> str | None:
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
[bold]Available Commands:[/bold]

/help     - Show this message
/tools    - List available AI tools
/stats    - Display conversation stats
/save     - Save the current conversation
/export   - Export to Markdown or JSON
/clear    - Clear messages (keep session)
/exit     - Leave the chat

[bold]Example prompts:[/bold]

• "How many invoices did I issue this year?"
• "Find invoices for client Rossi"
• "Show me the last 5 invoices"
• "Which customers have the most invoices?"
• "Give me a summary of the current year"
"""

        console.print(Panel(help_text, title="Help", border_style="blue"))
        return None

    async def _clear_chat(self) -> None:
        """Clear chat messages."""
        if await questionary.confirm(
            "Do you really want to delete all messages?",
            default=False,
            style=openfatture_style,
        ).ask_async():
            self.session.clear_messages(keep_system=True)
            console.print("[green]✓ Chat cleared[/green]\n")
        return None

    async def _save_session(self) -> None:
        """Save current session."""
        if self.session_manager.save_session(self.session):
            console.print(f"[green]✓ Session saved: {self.session.id[:8]}...[/green]\n")
        else:
            console.print("[red]✗ Error while saving[/red]\n")
        return None

    async def _export_session(self) -> None:
        """Export session to file."""
        # Ask format
        format_choice = await questionary.select(
            "Export format:",
            choices=["Markdown", "JSON"],
            style=openfatture_style,
        ).ask_async()

        format_type = format_choice.lower()

        # Export
        output_path = self.session_manager.export_session(
            self.session.id,
            format=format_type,
        )

        if output_path:
            console.print(f"[green]✓ Exported to: {output_path}[/green]\n")
        else:
            console.print("[red]✗ Error during export[/red]\n")

        return None

    async def _show_stats(self) -> None:
        """Show session statistics."""
        table = Table(title="Session Statistics", show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Session ID", self.session.id[:16] + "...")
        table.add_row("Title", self.session.metadata.title)
        table.add_row("Messages", str(self.session.metadata.message_count))
        table.add_row("Total tokens", str(self.session.metadata.total_tokens))
        table.add_row("Total cost", f"${self.session.metadata.total_cost_usd:.4f}")
        table.add_row("Provider", self.session.metadata.primary_provider or "N/A")
        table.add_row("Model", self.session.metadata.primary_model or "N/A")

        if self.session.metadata.tools_used:
            table.add_row("Tools used", ", ".join(self.session.metadata.tools_used))

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

        table = Table(title="Available AI Tools")
        table.add_column("Name", style="cyan")
        table.add_column("Category", style="yellow")
        table.add_column("Description", style="white")

        for tool in tools:
            table.add_row(tool.name, tool.category, tool.description)

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
[bold green]👋 Thanks for using OpenFatture AI![/bold green]

[bold]Conversation summary:[/bold]
{summary}

[dim]The session was saved automatically.[/dim]
[dim]Resume anytime via interactive > AI Assistant[/dim]
"""

        console.print(Panel(goodbye_text, border_style="green"))


async def start_interactive_chat(
    session_id: str | None = None,
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
