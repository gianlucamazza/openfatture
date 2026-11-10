"""Agentic assistant entry point for the public CLI."""

from __future__ import annotations

import asyncio
import sys
import time
import traceback
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from openfatture.ai.runtime.service import AssistantRuntime
    from openfatture.cli.assistant_ui import ChatPresentation
    from openfatture.events import GlobalEventBus
    from openfatture.platform.config import Settings

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
    elif cmd == "/pending":
        from openfatture.platform.logging import redact_sensitive

        console.print(Text(str(redact_sensitive(runtime.uncertain_tools()))))
    elif cmd == "/reconcile":
        import json

        try:
            payload = json.loads(user_input.split(maxsplit=1)[1])
            runtime.reconcile_tool(payload["call_id"], payload["result"], payload["evidence"])
            console.print(Text(_text("assistant-reconciled")))
        except (ValueError, KeyError, IndexError, TypeError):
            console.print(Text(_text("assistant-reconcile-invalid")))
    elif cmd == "/clear":
        try:
            cleared = runtime.clear_session()
        except ValueError:
            console.print(Text(_text("assistant-resolve-pending-first")))
        else:
            console.print(Text(_text("assistant-cleared" if cleared else "assistant-no-session")))
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
    if message is None and (json_output or (ctx.obj or {}).get("format", "rich") != "rich"):
        from openfatture.cli.formatters.utils import get_format_from_context
        from openfatture.cli.output import emit

        emit(
            {
                "success": False,
                "data": None,
                "warnings": [],
                "error": {
                    "code": "interactive_format",
                    "message": "Provide a single request when using a structured output format",
                },
            },
            get_format_from_context(ctx, json_output),
        )
        raise typer.Exit(2)
    run_sync_with_lifespan(_run_assistant(ctx, message, stream, json_output, session))


@dataclass
class _AssistantSession:
    """One assistant command invocation: the runtime, its presentation and its outcome."""

    runtime: AssistantRuntime
    ui: ChatPresentation
    settings: Settings
    format_type: str
    stream: bool
    success: bool = False

    @property
    def machine(self) -> bool:
        return self.format_type != "rich"

    async def execute(self, text: str) -> bool:
        from openfatture.cli.assistant_ui import interruptible_turn
        from openfatture.cli.formatters.utils import render_response

        async with interruptible_turn():
            if self.stream and not self.machine:
                await self.ui.render(self.runtime.stream(text))
                response = self.runtime.last_response
                if response is None:
                    raise RuntimeError("Assistant stream finished without a response")
            else:
                response = await self.runtime.run(text)
                render_response(response, self.format_type, console, show_metrics=False)
            if not response.success and not self.machine:
                console.print(Text(self.ui.text("assistant-turn-failed")))
            return bool(response.success)

    async def converse(self, message: str | None) -> None:
        """Resume an interrupted turn, then serve the request, piped input or the chat."""
        if await self._resume_pending(message):
            return
        if message is not None:
            self.success = await self.execute(message)
            if not self.success:
                raise typer.Exit(1)
            return
        if self.machine:
            # One JSON/other formatted response per input line; no interactive banners.
            for line in sys.stdin:
                if line.strip():
                    await self.execute(line.strip())
            self.success = True
            return
        await self._chat()

    async def _resume_pending(self, message: str | None) -> bool:
        """Run the turn left pending by a previous session; True when it was ``message``."""
        pending = self.runtime.pending_user_input
        if not isinstance(pending, str):
            return False
        if not self.machine:
            console.print(Text(self.ui.text("assistant-resuming")))
        from openfatture.ai.runtime.durability import UncertainToolOutcome

        one_shot = self.machine or message is not None
        try:
            self.success = await self.execute(pending)
        except UncertainToolOutcome:
            if one_shot:
                raise
            console.print(Text(self.ui.text("assistant-uncertain-tool")))
            self.success = False
        if not self.success and one_shot:
            raise typer.Exit(1)
        return message == pending

    async def _chat(self) -> None:
        console.print(Text(f"OpenFatture · {self.settings.ai_model}"))
        console.print(Text(self.ui.text("assistant-describe-what-you-need")))
        while (user_input := await self._next_request()) is not None:
            await self._chat_turn(user_input)
            console.print()
        self.success = True

    async def _next_request(self) -> str | None:
        """Read input until a request for the model arrives; None ends the chat."""
        while True:
            try:
                user_input = (await self.ui.read()).strip()
            except (EOFError, KeyboardInterrupt):
                console.print()
                return None
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit", "q"}:
                return None
            if user_input.lower() == "/resume":
                pending = self.runtime.pending_user_input
                if not pending:
                    console.print(Text(self.ui.text("assistant-no-pending")))
                    continue
                user_input = pending
            slash = _handle_slash_command(user_input, runtime=self.runtime)
            if slash == "exit":
                return None
            if not slash:
                return user_input

    async def _chat_turn(self, user_input: str) -> None:
        from openfatture.platform.logging import redact_sensitive

        try:
            await self.execute(user_input)
        except (asyncio.CancelledError, KeyboardInterrupt):
            console.print(Text(self.ui.text("assistant-interrupted")))
        except Exception:
            console.print(Text(self.ui.text("assistant-request-error")))
            if self.settings.debug_config.enable_debug_logging:
                console.print(Text(redact_sensitive(traceback.format_exc())))


def _start_runtime(
    settings: Settings,
    ui: ChatPresentation,
    *,
    message: str | None,
    stream: bool,
    session_id: str | None,
) -> AssistantRuntime:
    from openfatture.platform.extras import require_extra
    from openfatture.storage.database.base import init_db

    require_extra("ai", feature="the business assistant")
    from openfatture.ai.runtime import create_assistant_runtime

    init_db(str(settings.database_url))
    runtime: AssistantRuntime = create_assistant_runtime(
        enable_streaming=stream,
        debug_config=settings.debug_config,
        persist_session=message is None or session_id is not None,
        session_id=session_id,
        interaction=ui if ui.interactive else None,
    )
    return runtime


def _publish_started(
    event_bus: GlobalEventBus | None,
    settings: Settings,
    *,
    message: str | None,
    stream: bool,
    session_id: str | None,
) -> None:
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


def _publish_completed(
    event_bus: GlobalEventBus | None,
    session: _AssistantSession | None,
    *,
    started_at: float,
    failure: str | None,
) -> None:
    if event_bus:
        event_bus.publish(
            AICommandCompletedEvent(
                command="assistant",
                success=session.success if session else False,
                tokens_used=session.runtime.total_usage.total_tokens if session else 0,
                cost_usd=session.runtime.total_usage.estimated_cost_usd if session else 0,
                latency_ms=(time.monotonic() - started_at) * 1000,
                error=failure,
            )
        )


def _report_failure(
    exc: BaseException, ui: ChatPresentation, settings: Settings, format_type: str
) -> None:
    """Explain a failed command; call only while ``exc`` is being handled."""
    from openfatture.cli.formatters.utils import render_response
    from openfatture.platform.extras import MissingExtraError
    from openfatture.platform.logging import redact_sensitive

    if format_type != "rich":
        from openfatture.ai.domain.response import AgentResponse, ResponseStatus

        render_response(
            AgentResponse(content="", status=ResponseStatus.ERROR, error=type(exc).__name__),
            format_type,
            console,
            show_metrics=False,
        )
        return
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


async def _run_assistant(
    ctx: typer.Context | None,
    message: str | None,
    stream: bool,
    json_output: bool,
    session_id: str | None,
) -> None:
    from openfatture.cli.assistant_ui import ChatPresentation
    from openfatture.cli.formatters.utils import get_format_from_context

    format_type = get_format_from_context(ctx, json_output)
    settings = get_settings()
    ui = ChatPresentation(
        console,
        settings.locale,
        interactive=console.is_terminal and sys.stdin.isatty() and format_type == "rich",
    )
    session: _AssistantSession | None = None
    started_at = time.monotonic()
    event_bus = get_event_bus()
    failure = None
    try:
        runtime = _start_runtime(
            settings, ui, message=message, stream=stream, session_id=session_id
        )
        session = _AssistantSession(runtime, ui, settings, format_type, stream)
        _publish_started(event_bus, settings, message=message, stream=stream, session_id=session_id)
        await session.converse(message)
    except typer.Exit:
        raise
    except (Exception, asyncio.CancelledError) as exc:
        failure = type(exc).__name__
        _report_failure(exc, ui, settings, format_type)
        raise typer.Exit(1) from exc
    finally:
        _publish_completed(event_bus, session, started_at=started_at, failure=failure)
