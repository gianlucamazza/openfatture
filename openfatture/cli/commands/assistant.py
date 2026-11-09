"""Agentic assistant entry point for the public CLI."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from openfatture.ai.runtime.service import AssistantRuntime

import typer
from rich.console import Console
from rich.text import Text

from openfatture.cli.lifespan import get_event_bus, run_sync_with_lifespan
from openfatture.events.ai_events import AICommandCompletedEvent, AICommandStartedEvent
from openfatture.platform.config import get_settings
from openfatture.platform.logging import get_logger

app = typer.Typer(no_args_is_help=True)
console = Console()
logger = get_logger(__name__)


def _text(key: str, **values: Any) -> str:
    from openfatture.cli.assistant_ui import translate

    return translate(key, get_settings().locale, **values)


async def _render_stream(runtime: AssistantRuntime, message: str) -> str:
    from openfatture.cli.assistant_ui import ChatPresentation

    return await ChatPresentation(console, get_settings().locale).render(runtime.stream(message))


def _handle_slash_command(user_input: str, *, runtime: AssistantRuntime) -> str | None:
    if not user_input.startswith("/"):
        return None
    cmd = user_input.split(maxsplit=1)[0].lower()
    if cmd in {"/exit", "/quit", "/q"}:
        return "exit"
    if cmd in {"/help", "/?"}:
        console.print(Text(_text("assistant-help")))
    elif cmd == "/session":
        console.print(
            Text(
                _text(
                    "assistant-session",
                    session=runtime.session_id or _text("assistant-not-persisted"),
                )
            )
        )
    elif cmd == "/clear":
        console.print(
            Text(_text("assistant-cleared" if runtime.clear_session() else "assistant-no-session"))
        )
    else:
        console.print(Text(_text("assistant-unknown-command", command=cmd)))
    return "handled"


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
    import asyncio
    import sys
    import traceback

    from openfatture.cli.assistant_ui import ChatPresentation, interruptible_turn
    from openfatture.cli.formatters.utils import get_format_from_context, render_response
    from openfatture.platform.extras import MissingExtraError, require_extra
    from openfatture.platform.logging import redact_sensitive
    from openfatture.storage.database.base import init_db

    format_type = get_format_from_context(ctx, json_output)
    settings = get_settings()
    machine = format_type != "rich"
    ui = ChatPresentation(
        console,
        settings.locale,
        interactive=console.is_terminal and sys.stdin.isatty() and not machine,
    )
    runtime = None
    started_at = time.monotonic()
    event_bus = get_event_bus()
    success = False
    failure = None
    try:
        require_extra("ai", feature="the business assistant")
        from openfatture.ai.runtime import create_assistant_runtime

        init_db(str(settings.database_url))
        runtime = create_assistant_runtime(
            enable_streaming=stream,
            debug_config=settings.debug_config,
            persist_session=message is None or session_id is not None,
            session_id=session_id,
            interaction=ui if ui.interactive else None,
        )
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

        async def execute(text: str) -> bool:
            async with interruptible_turn():
                if stream and not machine:
                    await ui.render(runtime.stream(text))
                    response = runtime.last_response
                else:
                    response = await runtime.run(text)
                    render_response(response, format_type, console, show_metrics=False)
                if not response.success and not machine:
                    console.print(Text(ui.text("assistant-turn-failed")))
                return response.success

        if message is not None:
            success = await execute(message)
            if not success:
                raise typer.Exit(1)
            return
        if machine:
            # One JSON/other formatted response per input line; no interactive banners.
            for line in sys.stdin:
                if line.strip():
                    await execute(line.strip())
            success = True
            return
        console.print(Text(f"OpenFatture · {settings.ai_model}"))
        console.print(Text(ui.text("assistant-describe-what-you-need")))
        while True:
            try:
                user_input = (await ui.read()).strip()
            except (EOFError, KeyboardInterrupt):
                console.print()
                break
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit", "q"}:
                break
            slash = _handle_slash_command(user_input, runtime=runtime)
            if slash == "exit":
                break
            if slash:
                continue
            try:
                await execute(user_input)
            except (asyncio.CancelledError, KeyboardInterrupt):
                console.print(Text(ui.text("assistant-interrupted")))
            except Exception:
                console.print(Text(ui.text("assistant-request-error")))
                if settings.debug_config.enable_debug_logging:
                    console.print(Text(redact_sensitive(traceback.format_exc())))
            console.print()
        success = True
    except typer.Exit:
        raise
    except (Exception, asyncio.CancelledError) as exc:
        failure = type(exc).__name__
        if machine:
            from openfatture.ai.domain.response import AgentResponse, ResponseStatus

            render_response(
                AgentResponse(content="", status=ResponseStatus.ERROR, error=failure),
                format_type,
                console,
                show_metrics=False,
            )
        else:
            console.print(
                Text(
                    ui.text(
                        "assistant-missing-extra"
                        if isinstance(exc, (MissingExtraError, ImportError))
                        else "assistant-request-error"
                    )
                )
            )
            if settings.debug_config.enable_debug_logging:
                console.print(Text(redact_sensitive(traceback.format_exc())))
        raise typer.Exit(1) from exc
    finally:
        if event_bus:
            event_bus.publish(
                AICommandCompletedEvent(
                    command="assistant",
                    success=success,
                    tokens_used=runtime.total_usage.total_tokens if runtime else 0,
                    cost_usd=runtime.total_usage.estimated_cost_usd if runtime else 0,
                    latency_ms=(time.monotonic() - started_at) * 1000,
                    error=failure,
                )
            )
