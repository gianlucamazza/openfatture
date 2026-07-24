"""Agentic assistant entry point for the public CLI."""

import time
from typing import TYPE_CHECKING

import typer
from rich.console import Console

from openfatture.cli.lifespan import get_event_bus, run_sync_with_lifespan
from openfatture.core.events.ai_events import AICommandCompletedEvent, AICommandStartedEvent
from openfatture.utils.config import get_settings
from openfatture.utils.logging import get_logger

if TYPE_CHECKING:
    from openfatture.ai.domain.message import ConversationHistory

app = typer.Typer(no_args_is_help=True)
console = Console()
logger = get_logger(__name__)


def _history(items: list[dict[str, str]]) -> ConversationHistory:
    from openfatture.ai.domain.message import ConversationHistory, Message, Role

    history = ConversationHistory()
    for item in items:
        try:
            role = Role(item.get("role", "user"))
        except ValueError:
            role = Role.USER
        history.add_message(Message(role=role, content=item.get("content", "")))
    return history


@app.command()
def assistant(
    ctx: typer.Context,
    message: str | None = typer.Argument(None, help="A request for the OpenFatture assistant."),
    stream: bool = typer.Option(True, "--stream/--no-stream", help="Stream the response."),
    json_output: bool = typer.Option(False, "--json", help="Emit the response as JSON."),
) -> None:
    """Ask the assistant to explain, inspect, or perform an invoicing task."""
    run_sync_with_lifespan(_run_assistant(ctx, message, stream, json_output))


async def run_assistant_session(message: str | None = None) -> None:
    """Run the conversational assistant session used by interactive mode."""
    await _run_assistant(None, message, True, False)


async def _run_assistant(
    ctx: typer.Context | None, message: str | None, stream: bool, json_output: bool
) -> None:
    from openfatture.ai.agents.chat_agent import ChatAgent
    from openfatture.ai.domain.context import ChatContext
    from openfatture.ai.providers.factory import create_provider
    from openfatture.cli.formatters.utils import get_format_from_context, render_response

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
                parameters={"stream": stream, "interactive": message is None},
            )
        )

    try:
        agent = ChatAgent(
            provider=create_provider(),
            enable_streaming=stream,
            debug_config=settings.debug_config,
        )
        if message:
            context = ChatContext(user_input=message)
            if stream and format_type == "rich":
                console.print("Assistant: ", end="")
                async for chunk in agent.execute_stream(context):
                    console.print(chunk, end="")
                console.print()
            else:
                response = await agent.execute(context)
                render_response(response, format_type, console, show_metrics=False)
                tokens_used = response.usage.total_tokens
                cost_usd = response.usage.estimated_cost_usd
            success = True
            return

        console.print("[bold]OpenFatture assistant[/bold]")
        console.print("Describe what you need, or type 'exit' to end the session.\n")
        conversation: list[dict[str, str]] = []
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
            conversation.append({"role": "user", "content": user_input})
            context = ChatContext(
                user_input=user_input, conversation_history=_history(conversation)
            )
            if stream:
                console.print("Assistant: ", end="")
                answer = ""
                async for event in agent.execute_stream(context):
                    if event.is_content():
                        text = event.get_text()
                        console.print(text, end="")
                        answer += text
                console.print()
            else:
                response = await agent.execute(context)
                answer = response.content
                console.print(f"Assistant: {answer}")
            conversation.append({"role": "assistant", "content": answer})
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
