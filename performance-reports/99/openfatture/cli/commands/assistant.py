"""Agentic assistant entry point for the public CLI."""

from __future__ import annotations

import time

import typer
from rich.console import Console

from openfatture.cli.lifespan import get_event_bus, run_sync_with_lifespan
from openfatture.events.ai_events import AICommandCompletedEvent, AICommandStartedEvent
from openfatture.platform.config import get_settings
from openfatture.platform.logging import get_logger

app = typer.Typer(no_args_is_help=True)
console = Console()
logger = get_logger(__name__)


@app.command()
def assistant(
    ctx: typer.Context,
    message: str | None = typer.Argument(None, help="A request for the OpenFatture assistant."),
    stream: bool = typer.Option(True, "--stream/--no-stream", help="Stream the response."),
    json_output: bool = typer.Option(False, "--json", help="Emit the response as JSON."),
    session: str | None = typer.Option(
        None,
        "--session",
        help="Resume a file-backed chat session by ID (enables persistence).",
    ),
) -> None:
    """Ask the assistant to explain, inspect, or perform an invoicing task."""
    run_sync_with_lifespan(_run_assistant(ctx, message, stream, json_output, session))


async def run_assistant_session(message: str | None = None) -> None:
    """Run the conversational assistant session used by interactive mode."""
    await _run_assistant(None, message, True, False, None)


async def _run_assistant(
    ctx: typer.Context | None,
    message: str | None,
    stream: bool,
    json_output: bool,
    session_id: str | None,
) -> None:
    from openfatture.cli.formatters.utils import get_format_from_context, render_response
    from openfatture.platform.extras import MissingExtraError, require_extra

    try:
        require_extra("ai", feature="the business assistant")
        from openfatture.ai.runtime import create_assistant_runtime
    except MissingExtraError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    except ImportError as exc:
        console.print("[red]AI dependencies are incomplete. Install with: uv sync --extra ai[/red]")
        raise typer.Exit(code=1) from exc

    format_type = get_format_from_context(ctx, json_output)
    started_at = time.time()
    event_bus = get_event_bus()
    settings = get_settings()
    success = False
    tokens_used = 0
    cost_usd = 0.0

    if event_bus:
        event_bus.publish(
            AICommandStartedEvent(
                command="assistant",
                user_input=message or "Interactive assistant session",
                provider=settings.ai_provider,
                model=settings.ai_model,
                parameters={
                    "stream": stream,
                    "interactive": message is None,
                    "session_id": session_id,
                },
            )
        )

    try:
        # Persist for interactive mode or when resuming/continuing a named session.
        persist = message is None or session_id is not None
        runtime = create_assistant_runtime(
            enable_streaming=stream,
            debug_config=settings.debug_config,
            persist_session=persist,
            session_id=session_id,
        )
        if persist and runtime.session_id:
            console.print(f"[dim]Session: {runtime.session_id}[/dim]\n")
        if message:
            if stream and format_type == "rich":
                console.print("Assistant: ", end="")
                async for chunk in runtime.stream(message):
                    if isinstance(chunk, str):
                        console.print(chunk, end="")
                    elif hasattr(chunk, "is_content") and chunk.is_content():
                        console.print(chunk.get_text(), end="")
                console.print()
            else:
                response = await runtime.run(message)
                render_response(response, format_type, console, show_metrics=False)
                tokens_used = response.usage.total_tokens
                cost_usd = response.usage.estimated_cost_usd
            success = True
            return

        console.print("[bold]OpenFatture assistant[/bold]")
        console.print("Describe what you need, or type 'exit' to end the session.\n")
        # When persistence is on, the session store is the history source of truth.
        # Do not pass a parallel in-memory history that would duplicate turns.
        while True:
            try:
                user_input = console.input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                console.print()
                break
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit", "q"}:
                break
            if stream:
                console.print("Assistant: ", end="")
                answer = ""
                async for event in runtime.stream(user_input):
                    if isinstance(event, str):
                        console.print(event, end="")
                        answer += event
                    elif hasattr(event, "is_content") and event.is_content():
                        text = event.get_text()
                        console.print(text, end="")
                        answer += text
                console.print()
            else:
                response = await runtime.run(user_input)
                answer = response.content
                console.print(f"Assistant: {answer}")
            console.print()
        success = True
    except Exception as exc:
        logger.error("Assistant execution failed", error=str(exc))
        console.print(f"[red]Assistant error: {exc}[/red]")
        raise typer.Exit(1) from exc
    finally:
        if event_bus:
            event_bus.publish(
                AICommandCompletedEvent(
                    command="assistant",
                    success=success,
                    tokens_used=tokens_used,
                    cost_usd=cost_usd,
                    latency_ms=(time.time() - started_at) * 1000,
                )
            )
