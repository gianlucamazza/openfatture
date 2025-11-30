"""Interactive chat UI for AI assistant."""

import asyncio
from typing import cast

import questionary
from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from openfatture.ai.agents.chat_agent import ChatAgent
from openfatture.ai.context import enrich_chat_context, enrich_with_rag
from openfatture.ai.domain.context import ChatContext
from openfatture.ai.domain.message import Message
from openfatture.ai.feedback import FeedbackCreate, FeedbackService
from openfatture.ai.providers.base import BaseLLMProvider
from openfatture.ai.providers.factory import create_provider
from openfatture.ai.session import ChatSession, SessionManager
from openfatture.ai.streaming import StreamAccumulator, StreamEventType
from openfatture.cli.commands.custom_commands import get_command_registry
from openfatture.cli.ui.styles import openfatture_style
from openfatture.storage.database.models import FeedbackType
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

    # Memory limits for streaming (used by StreamAccumulator for automatic overflow)
    MAX_CONTENT_CHUNKS = 1000  # Maximum number of content chunks (bounded deque)
    MAX_PROGRESS_MESSAGES = 50  # Maximum number of progress messages (bounded deque)

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
        # Cache panel width to avoid repeated calculations
        self._panel_width: int | None = None

        # Initialize session - ensure it's always created
        if session is not None:
            self._session = session
        else:
            # Try to create ChatSession, fallback to a mock if it fails
            try:
                self._session = ChatSession()
            except Exception as e:
                logger.warning("ChatSession creation failed, using mock", error=str(e))

                # Create a minimal mock session
                class MockMetadata:
                    def __init__(self):
                        self.message_count = 0
                        self.total_tokens = 0
                        self.total_cost_usd = 0.0
                        self.title = "Mock Session"
                        self.primary_provider = None
                        self.primary_model = None
                        self.tools_used = []

                class MockSession:
                    def __init__(self):
                        self.id = "mock-session"
                        self.metadata = MockMetadata()
                        self.auto_save = False

                    def add_user_message(self, msg):
                        pass

                    def add_assistant_message(self, content, **kwargs):
                        pass

                    def clear_messages(self, keep_system=True):
                        pass

                    def get_messages(self, include_system=False):
                        return []

                    def get_summary(self):
                        return "Mock session"

                self._session = MockSession()  # type: ignore[assignment]

        # Initialize session manager with error handling
        try:
            self.session_manager = session_manager or SessionManager()
        except Exception as e:
            logger.warning("session_manager_creation_failed", error=str(e))
            try:
                self.session_manager = SessionManager()
            except Exception as fallback_e:
                logger.error("session_manager_fallback_failed", error=str(fallback_e))
                # Last resort: raise the original error
                raise e from fallback_e

        self.agent: ChatAgent | None = None
        self.provider: BaseLLMProvider | None = None

        # Initialize custom commands registry
        self.custom_commands = get_command_registry()

        # Built-in commands
        self.commands = {
            "/help": self._show_help,
            "/clear": self._clear_chat,
            "/save": self._save_session,
            "/export": self._export_session,
            "/stats": self._show_stats,
            "/tools": self._show_tools,
            "/custom": self._show_custom_commands,
            "/reload": self._reload_custom_commands,
            "/feedback": self._submit_feedback,
            "/exit": self._exit_chat,
            "/quit": self._exit_chat,
        }

        # Feedback tracking
        self.last_ai_message: str | None = None
        self.feedback_service = FeedbackService()

    @property
    def session(self):
        """Get the chat session."""
        return self._session

    @property
    def panel_width(self) -> int:
        """Get cached panel width to avoid repeated calculations."""
        if self._panel_width is None:
            self._panel_width = min(int(console.width * 0.8), 120)
        return self._panel_width

    def _handle_error(self, error: Exception, context: str, show_suggestions: bool = True) -> None:
        """Centralized error handling with consistent formatting and logging."""
        logger.error(f"{context}_error", error=str(error))

        error_lines = [f"[red]❌ Errore {context}: {error}[/red]"]

        if show_suggestions:
            error_lines.extend(
                [
                    "",
                    "[yellow]💡 Suggerimenti:[/yellow]",
                    "• Riprova l'operazione",
                    "• Controlla la connessione",
                    "• Usa /help per assistenza",
                ]
            )

        console.print("\n".join(error_lines))
        console.print()

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
            self._handle_error(e, "inizializzazione")
            raise

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
        """Show compact welcome header with essential information."""
        # Header principale compatto
        header = Panel.fit(
            "[bold blue]🤖 OpenFatture AI Assistant[/bold blue]\n"
            "[dim]Sessione attiva • Provider: "
            + f"{self.provider.provider_name if self.provider else 'N/A'} • "
            + f"Modello: {self.provider.model if self.provider else 'N/A'}[/dim]\n"
            "[dim]Comandi: /help /tools /stats /save /clear /exit[/dim]",
            border_style="blue",
            padding=(0, 1),
        )
        console.print(header)

        # Capabilities summary (compact)
        capabilities = Panel(
            "[bold]💡 Capacità:[/bold] Ricerca fatture/clienti • Statistiche • Workflow guidance\n"
            "[bold]🎯 Pronto per aiutarti![/bold] Digita un messaggio o usa /help per i comandi",
            border_style="green",
            padding=(0, 1),
        )
        console.print(capabilities)
        console.print()  # Breathing room

    async def _get_user_input(self) -> str:
        """Get user input with improved UX."""
        # Show token counter with better formatting using buffered output
        output_lines = [
            "",  # Spacing
            self._get_mini_stats_str(),
            "",  # Spacing
        ]
        console.print("\n".join(output_lines))

        # Get input with better prompt
        user_input = await questionary.text(
            "💬 Messaggio:",
            style=openfatture_style,
            qmark="",
            instruction="(Digita il tuo messaggio o usa /comando. Premi Ctrl+C per uscire)",
        ).ask_async()

        return user_input.strip() if user_input else ""

    async def _process_message(self, user_input: str) -> None:
        """
        Process user message and get AI response with modern bubble UI.

        Args:
            user_input: User message
        """
        # Display user message in bubble format
        self._display_user_message_bubble(user_input)

        # Add user message to session
        self.session.add_user_message(user_input)

        # Check if streaming is enabled
        if self.agent is None:
            raise RuntimeError("Agent not initialized. Call _initialize_agent() first.")
        if self.agent.config.streaming_enabled:
            # Start Live display with thinking message
            from datetime import datetime

            timestamp = datetime.now().strftime("%H:%M")
            thinking_content = Panel(
                "🤖 AI sta pensando...",
                border_style="green",
                padding=(0, 1),
                title=f"[dim]🤖 AI • {timestamp}[/dim]",
                title_align="left",
                width=min(int(console.width * 0.8), 100),
            )
            with Live(thinking_content, console=console, refresh_per_second=4) as live:
                # Build context while showing thinking
                context = await self._build_context(user_input)
                # Stream response with real-time rendering
                await self._process_message_streaming(context, live)
        else:
            # Build context
            context = await self._build_context(user_input)
            # Use non-streaming mode (fallback)
            await self._process_message_non_streaming(context)

    async def _process_message_streaming(self, context: ChatContext, live: Live) -> None:
        """
        Process message with streaming response and modern bubble UI.

        Best Practice (2025): Use Live display for entire bubble to prevent text leakage.
        - All content is managed within Live context
        - Progress indicators are integrated into bubble content
        - No direct console printing during streaming

        Args:
            context: Chat context
        """
        # Collect response chunks for session storage using bounded accumulators
        full_response = ""
        content_acc = StreamAccumulator(max_size=self.MAX_CONTENT_CHUNKS)
        progress_acc = StreamAccumulator(max_size=self.MAX_PROGRESS_MESSAGES)

        try:
            if self.agent is None:
                raise RuntimeError("Agent not initialized. Call _initialize_agent() first.")

            # Create initial bubble content for Live display
            from datetime import datetime

            timestamp = datetime.now().strftime("%H:%M")

            def create_live_content(
                content: str = "", progress_chunks: list[str] | None = None
            ) -> Panel:
                """Create the complete bubble content for Live display."""
                bubble_content = content
                if progress_chunks:
                    if bubble_content:
                        bubble_content += "\n\n" + "\n".join(progress_chunks)
                    else:
                        bubble_content = "\n".join(progress_chunks)

                # Don't truncate content during streaming - let Rich handle wrapping
                # The Panel will handle width constraints automatically

                return Panel(
                    bubble_content,
                    border_style="green",
                    padding=(0, 1),
                    title=f"[dim]🤖 AI • {timestamp}[/dim]",
                    title_align="left",
                    width=min(
                        int(console.width * 0.8), 120
                    ),  # Increased width for better formatting
                )

                # Live is already started in caller

            async for event in self.agent.execute_stream(context):
                # Handle different event types
                if event.is_content():
                    # Content event - accumulate and display
                    chunk = event.get_text()
                    full_response += chunk
                    content_acc.add(chunk)

                    rendered_content = content_acc.get_text()
                    live.update(create_live_content(rendered_content, progress_acc.get_chunks()))

                elif event.type == StreamEventType.TOOL_START:
                    # Tool started - show progress
                    if isinstance(event.data, dict):
                        tool_name = event.data.get("tool_name", "unknown")
                        progress_acc.add(f"🔧 Avvio {tool_name}...")
                        live.update(
                            create_live_content(content_acc.get_text(), progress_acc.get_chunks())
                        )

                elif event.type == StreamEventType.TOOL_RESULT:
                    # Tool succeeded - show result
                    if isinstance(event.data, dict):
                        tool_name = event.data.get("tool_name", "unknown")
                        result = str(event.data.get("result", ""))
                        # Truncate long results
                        if len(result) > 200:
                            result = result[:200] + "..."
                        progress_acc.add(f"✅ {tool_name}: {result}")
                        live.update(
                            create_live_content(content_acc.get_text(), progress_acc.get_chunks())
                        )

                elif event.type == StreamEventType.TOOL_ERROR:
                    # Tool failed - show error
                    if isinstance(event.data, dict):
                        tool_name = event.data.get("tool_name", "unknown")
                        error = event.data.get("error", "Errore sconosciuto")
                        progress_acc.add(f"❌ {tool_name}: {error}")
                        live.update(
                            create_live_content(content_acc.get_text(), progress_acc.get_chunks())
                        )

                elif event.type == StreamEventType.METRICS:
                    # Metrics event - show summary
                    if isinstance(event.data, dict):
                        exec_time = event.data.get("execution_time_ms", 0) / 1000
                        successful = event.data.get("successful_tools", 0)
                        failed = event.data.get("failed_tools", 0)
                        progress_acc.add(
                            f"📊 Completato: {successful} OK, {failed} errori ({exec_time:.1f}s)"
                        )
                        live.update(
                            create_live_content(content_acc.get_text(), progress_acc.get_chunks())
                        )

            # Final display in proper bubble format via Live
            if len(content_acc) > 0:
                final_content = content_acc.get_text()
                # Create final bubble content with markdown rendered inside panel
                from datetime import datetime

                timestamp = datetime.now().strftime("%H:%M")
                live.update(
                    Panel(
                        Markdown(final_content),
                        border_style="green",
                        padding=(0, 1),
                        title=f"[dim]🤖 AI • {timestamp}[/dim]",
                        title_align="left",
                        width=min(int(console.width * 0.8), 120),  # Match streaming width
                    )
                )

            # Add assistant message to session with proper token/cost tracking
            if self.provider is None:
                raise RuntimeError("Provider not initialized.")

            # Try to get actual token usage from provider if available
            actual_tokens = getattr(self.provider, "_last_response_tokens", None)
            actual_cost = getattr(self.provider, "_last_response_cost", None)

            if actual_tokens is not None and actual_cost is not None:
                tokens = actual_tokens
                cost = actual_cost
            else:
                # Fallback to estimation
                estimated_tokens = len(full_response) // 4
                estimated_cost = estimated_tokens * 0.00001  # Rough estimate
                tokens = estimated_tokens
                cost = estimated_cost

            self.session.add_assistant_message(
                full_response,
                provider=self.provider.provider_name,
                model=self.provider.model,
                tokens=tokens,
                cost=cost,
            )

            # Save last AI message for feedback
            self.last_ai_message = full_response

            # Auto-save if configured
            if self.session.auto_save:
                self._auto_save()

            # Ask for feedback (optional, quick)
            await self._ask_for_feedback()

        except Exception as e:
            self._handle_error(e, "streaming")

    async def _process_message_non_streaming(self, context: ChatContext) -> None:
        """
        Process message without streaming (fallback) with modern UI.

        Args:
            context: Chat context
        """
        if self.agent is None:
            raise RuntimeError("Agent not initialized. Call _initialize_agent() first.")

        try:
            # Execute agent
            response = await self.agent.execute(context)

            # Check for errors
            if response.status.value == "error":
                self._display_error_bubble(response.error or "Errore sconosciuto")
                return

            # Add assistant message to session
            self.session.add_assistant_message(
                response.content,
                provider=response.provider,
                model=response.model,
                tokens=response.usage.total_tokens,
                cost=response.usage.estimated_cost_usd,
            )

            # Display response in bubble format
            self._display_response(response.content)

            # Save last AI message for feedback
            self.last_ai_message = response.content

            # Auto-save if configured
            if self.session.auto_save:
                self._auto_save()

            # Ask for feedback (optional, quick)
            await self._ask_for_feedback()

        except Exception as e:
            self._handle_error(e, "elaborazione")

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
        Display AI response with modern bubble design and markdown rendering.

        Args:
            content: Response content
        """
        # For non-streaming responses, render as markdown and display in bubble
        md = Markdown(content)
        with console.capture() as capture:
            console.print(md)
        rendered_content = capture.get()
        self._display_ai_message_bubble(rendered_content.strip())

    def _display_user_message_bubble(self, message: str) -> None:
        """Display user message in modern bubble format."""
        from datetime import datetime

        timestamp = datetime.now().strftime("%H:%M")
        bubble = Panel(
            f"[bold white]{message}[/bold white]",
            border_style="blue",
            padding=(0, 1),
            title=f"[dim]👤 Tu • {timestamp}[/dim]",
            title_align="right",
            width=min(int(console.width * 0.8), 120),  # Match other widths
        )
        console.print(Align.right(bubble, width=min(int(console.width * 0.8), 120)))
        console.print()  # Spacing

    def _display_ai_message_bubble(self, content: str) -> None:
        """Display AI message in modern bubble format."""
        from datetime import datetime

        timestamp = datetime.now().strftime("%H:%M")

        bubble = Panel(
            content,
            border_style="green",
            padding=(0, 1),
            title=f"[dim]🤖 AI • {timestamp}[/dim]",
            title_align="left",
            width=min(int(console.width * 0.8), 120),  # Match streaming width
        )
        console.print(bubble)
        console.print()  # Spacing

    def _display_error_bubble(self, error_message: str) -> None:
        """Display error in dedicated error bubble."""
        error_bubble = Panel(
            f"[red]❌ Errore:[/red] {error_message}\n\n"
            "[yellow]💡 Suggerimenti:[/yellow]\n"
            "• Riprova il messaggio\n"
            "• Usa /help per assistenza\n"
            "• Controlla la connessione",
            title="🚨 Errore Rilevato",
            border_style="red",
            padding=(1, 2),
        )
        console.print(error_bubble)
        console.print()

    async def _show_typing_indicator(self, max_duration: int = 5) -> None:
        """Show typing indicator during AI processing."""
        frames = [
            "🤖 AI sta pensando",
            "🤖 AI sta pensando.",
            "🤖 AI sta pensando..",
            "🤖 AI sta pensando...",
        ]

        with Live("", console=console, refresh_per_second=1) as live:  # Reduced refresh rate
            for i in range(max_duration * 1):  # 1 update per second
                frame = frames[i % len(frames)]
                live.update(f"[dim]{frame}[/dim]")
                await asyncio.sleep(1.0)  # Longer sleep interval

    def _show_mini_stats(self) -> None:
        """Show mini stats bar."""
        stats = self._get_mini_stats_str()
        console.print(stats)

    def _get_mini_stats_str(self) -> str:
        """Get mini stats as string for buffered output."""
        if not hasattr(self, "session") or self.session is None:
            return "[dim]Sessione in inizializzazione...[/dim]"

        try:
            return (
                f"[dim]Msgs: {self.session.metadata.message_count} | "
                f"Tokens: {self.session.metadata.total_tokens} | "
                f"Cost: ${self.session.metadata.total_cost_usd:.4f}[/dim]"
            )
        except AttributeError:
            return "[dim]Statistiche non disponibili[/dim]"

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
        args = parts[1:] if len(parts) > 1 else []

        # Check built-in commands first
        if cmd in self.commands:
            return await self.commands[cmd]()

        # Check custom commands
        if self.custom_commands.has_command(cmd.lstrip("/")):
            try:
                # Expand custom command template
                expanded = self.custom_commands.execute(cmd.lstrip("/"), args=args)

                # Display expansion preview
                console.print("\n[dim]🔧 Custom command expanded:[/dim]")
                preview = expanded[:200] + "..." if len(expanded) > 200 else expanded
                console.print(Panel(preview, border_style="blue", padding=(0, 1)))
                console.print()

                # Process as regular message
                await self._process_message(expanded)

            except ValueError as e:
                console.print(f"[red]❌ Command error: {e}[/red]")

            return None

        # Unknown command
        console.print(f"[yellow]Comando sconosciuto: {cmd}[/yellow]")
        console.print(
            "[dim]Usa /help per comandi built-in o /custom per comandi personalizzati[/dim]"
        )
        return None

    async def _show_help(self) -> None:
        """Show help message."""
        custom_count = len(self.custom_commands.list_commands())

        help_text = f"""
[bold]Built-in Commands:[/bold]

/help     - Show this message
/tools    - List available AI tools
/stats    - Display conversation stats
/feedback - Submit detailed feedback on AI response
/custom   - Show custom commands ({custom_count} available)
/reload   - Reload custom commands from disk
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

[bold]Custom Commands:[/bold]

Create custom commands in: [cyan]~/.openfatture/commands/[/cyan]
Use /custom to see available custom commands
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
        # Only save if we have a real ChatSession (not MockSession)
        if isinstance(self.session, ChatSession) and self.session_manager.save_session(
            self.session
        ):
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

    async def _show_custom_commands(self) -> None:
        """Show available custom commands."""
        self.custom_commands.display_commands()

        # Show usage examples if commands exist
        commands = self.custom_commands.list_commands()
        if commands and commands[0].examples:
            console.print("[bold cyan]Example usage:[/bold cyan]")
            for example in commands[0].examples[:3]:  # Show first 3 examples
                console.print(f"  [dim]{example}[/dim]")
            console.print()

        return None

    async def _reload_custom_commands(self) -> None:
        """Reload custom commands from disk."""
        try:
            self.custom_commands.reload()
            count = len(self.custom_commands.list_commands())
            console.print(f"[green]✓ Custom commands reloaded: {count} available[/green]\n")
        except Exception as e:
            console.print(f"[red]✗ Error reloading commands: {e}[/red]\n")

        return None

    async def _exit_chat(self) -> str:
        """Exit chat."""
        return "exit"

    def _auto_save(self) -> None:
        """Auto-save session."""
        try:
            # Only auto-save if we have a real ChatSession (not MockSession)
            if isinstance(self.session, ChatSession):
                self.session_manager.save_session(self.session)
                logger.debug("session_auto_saved", session_id=self.session.id)
        except Exception as e:
            logger.warning("session_auto_save_failed", error=str(e))

    async def _ask_for_feedback(self) -> None:
        """Ask user for quick feedback on AI response."""
        if not self.last_ai_message:
            return

        console.print()
        console.print("[dim]👍/👎 Rate questa risposta? (1-5, o Enter per saltare):[/dim] ", end="")

        try:
            # Get rating with timeout (non-blocking)
            import sys

            rating_input = await asyncio.wait_for(
                asyncio.to_thread(sys.stdin.readline), timeout=3.0
            )
            rating_str = rating_input.strip()

            if not rating_str:
                return

            # Parse rating
            if rating_str in ["1", "2", "3", "4", "5"]:
                rating = int(rating_str)

                # Create feedback
                feedback = FeedbackCreate(
                    session_id=self.session.id,
                    feedback_type=FeedbackType.RATING,
                    rating=rating,
                    original_text=self.last_ai_message[:500],  # Truncate
                    agent_type="chat_agent",
                )

                # Save feedback
                self.feedback_service.create_user_feedback(feedback)

                # Show confirmation
                emoji = "👍" if rating >= 4 else ("👌" if rating == 3 else "👎")
                console.print(f"[green]{emoji} Grazie per il feedback![/green]")

            elif rating_str in ["👍", "+", "y", "yes", "si", "sì"]:
                # Quick thumbs up
                feedback = FeedbackCreate(
                    session_id=self.session.id,
                    feedback_type=FeedbackType.THUMBS_UP,
                    rating=None,
                    original_text=self.last_ai_message[:500],
                    agent_type="chat_agent",
                )
                self.feedback_service.create_user_feedback(feedback)
                console.print("[green]👍 Grazie![/green]")

            elif rating_str in ["👎", "-", "n", "no"]:
                # Quick thumbs down
                feedback = FeedbackCreate(
                    session_id=self.session.id,
                    feedback_type=FeedbackType.THUMBS_DOWN,
                    rating=None,
                    original_text=self.last_ai_message[:500],
                    agent_type="chat_agent",
                )
                self.feedback_service.create_user_feedback(feedback)
                console.print(
                    "[yellow]👎 Grazie per il feedback. Usa /feedback per dettagli.[/yellow]"
                )

        except TimeoutError:
            # User didn't respond in time, skip feedback
            pass
        except Exception as e:
            logger.warning("feedback_prompt_error", error=str(e))

        console.print()

    async def _submit_feedback(self) -> None:
        """Submit detailed feedback via command."""
        if not self.last_ai_message:
            console.print("[yellow]Nessun messaggio AI recente da valutare[/yellow]\n")
            return None

        console.print("\n[bold cyan]📝 Feedback Dettagliato[/bold cyan]\n")

        # Ask for feedback type
        feedback_type_choice = await questionary.select(
            "Tipo di feedback:",
            choices=[
                "Rating (1-5 stelle)",
                "Correzione (testo corretto)",
                "Commento generale",
            ],
            style=openfatture_style,
        ).ask_async()

        if "Rating" in feedback_type_choice:
            # Rating feedback
            rating = await questionary.select(
                "Rating:",
                choices=["1 ⭐", "2 ⭐⭐", "3 ⭐⭐⭐", "4 ⭐⭐⭐⭐", "5 ⭐⭐⭐⭐⭐"],
                style=openfatture_style,
            ).ask_async()

            rating_value = int(rating[0])

            comment = await questionary.text(
                "Commento opzionale:",
                style=openfatture_style,
            ).ask_async()

            if not rating_value:
                console.print("[red]Rating è obbligatorio per questo tipo di feedback[/red]")
                return None

            feedback = FeedbackCreate(
                session_id=self.session.id,
                feedback_type=FeedbackType.RATING,
                rating=rating_value,
                original_text=self.last_ai_message[:1000],
                user_comment=comment if comment else None,
                agent_type="chat_agent",
            )

        elif "Correzione" in feedback_type_choice:
            # Correction feedback
            console.print("\n[dim]Messaggio originale (troncato):[/dim]")
            console.print(self.last_ai_message[:200] + "...\n")

            corrected = await questionary.text(
                "Versione corretta:",
                style=openfatture_style,
                multiline=True,
            ).ask_async()

            comment = await questionary.text(
                "Spiega la correzione:",
                style=openfatture_style,
            ).ask_async()

            if not corrected:
                console.print(
                    "[red]Testo corretto è obbligatorio per questo tipo di feedback[/red]"
                )
                return None

            feedback = FeedbackCreate(
                session_id=self.session.id,
                feedback_type=FeedbackType.CORRECTION,
                rating=None,
                original_text=self.last_ai_message[:1000],
                corrected_text=corrected,
                user_comment=comment if comment else None,
                agent_type="chat_agent",
            )

        else:
            # Comment feedback
            comment = await questionary.text(
                "Il tuo commento:",
                style=openfatture_style,
                multiline=True,
            ).ask_async()

            feedback = FeedbackCreate(
                session_id=self.session.id,
                feedback_type=FeedbackType.COMMENT,
                rating=None,
                original_text=self.last_ai_message[:1000],
                user_comment=comment,
                agent_type="chat_agent",
            )

        # Save feedback
        try:
            self.feedback_service.create_user_feedback(feedback)
            console.print("[green]✓ Feedback salvato! Grazie per aiutarci a migliorare.[/green]\n")
        except Exception as e:
            console.print(f"[red]✗ Errore nel salvataggio: {e}[/red]\n")
            logger.error("feedback_save_error", error=str(e))

        return None

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
