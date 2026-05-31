"""Interactive AI chat command."""

import typer

from openfatture.ai.agents.chat_agent import ChatAgent
from openfatture.ai.domain.context import ChatContext
from openfatture.ai.providers.factory import create_provider
from openfatture.cli.lifespan import get_event_bus, run_sync_with_lifespan
from openfatture.core.events.ai_events import AICommandCompletedEvent, AICommandStartedEvent
from openfatture.i18n import _
from openfatture.utils.config import get_settings

from ._app import _convert_history, app, console, logger


@app.command("chat")
def ai_chat(
    ctx: typer.Context,
    message: str | None = typer.Argument(None, help=_("cli-ai-help-chat-message")),
    stream: bool = typer.Option(True, "--stream/--no-stream", help=_("cli-ai-help-stream")),
    json_output: bool = typer.Option(False, "--json", help=_("cli-ai-help-json-output")),
) -> None:
    """
    Interactive AI chat assistant for invoice and tax questions.

    This command provides a conversational interface to ask questions about:
    - Invoice creation and management
    - Tax regulations and VAT rates
    - Payment tracking and reconciliation
    - General business advice

    The assistant has access to your business data and can perform actions
    like creating invoices, checking compliance, and analyzing payments.

    Examples:
        openfatture ai chat "How do I create an invoice for consulting work?"
        openfatture ai chat --no-stream "What VAT rate applies to software development?"
        openfatture ai chat "Help me" --format json
        openfatture ai chat  # Interactive mode
    """
    run_sync_with_lifespan(_run_chat(ctx, message, stream, json_output))


async def _run_chat(
    ctx: typer.Context, message: str | None, stream: bool, json_output: bool
) -> None:
    """Run interactive chat session."""
    import time

    from openfatture.cli.formatters.utils import get_format_from_context, render_response

    format_type = get_format_from_context(ctx, json_output)

    # Track execution metrics
    start_time = time.time()
    success = False
    tokens_used = 0
    cost_usd = 0.0

    # Get event bus and settings
    event_bus = get_event_bus()
    settings = get_settings()

    # Publish AICommandStartedEvent (for single message mode)
    if message and event_bus:
        event_bus.publish(
            AICommandStartedEvent(
                command="chat",
                user_input=message,
                provider=settings.ai_provider,
                model=settings.ai_model,
                parameters={"stream": stream, "interactive": False},
            )
        )

    try:
        # Get debug configuration
        debug_config = settings.debug_config

        # Create chat agent
        provider = create_provider()
        agent = ChatAgent(provider=provider, enable_streaming=stream, debug_config=debug_config)

        if message:
            # Single message mode - use formatters
            context = ChatContext(user_input=message)
            if stream and format_type == "rich":
                console.print(f"{_('cli-ai-chat-assistant-label')} ", end="")
                async for chunk in agent.execute_stream(context):
                    console.print(chunk, end="")
                console.print()  # New line
            else:
                response = await agent.execute(context)
                if json_output or format_type == "json":
                    console.print_json(data=response.model_dump())
                elif format_type == "rich":
                    console.print(f"{_('cli-ai-chat-assistant-label')} {response.content}")
                else:
                    # Use formatter for other formats
                    render_response(response, format_type, console, show_metrics=False)

                # Track metrics for single message mode
                success = True
                tokens_used = response.usage.total_tokens
                cost_usd = response.usage.estimated_cost_usd
        else:
            # Interactive mode - publish started event
            if event_bus:
                event_bus.publish(
                    AICommandStartedEvent(
                        command="chat",
                        user_input="Interactive chat session",
                        provider=settings.ai_provider,
                        model=settings.ai_model,
                        parameters={"stream": stream, "interactive": True},
                    )
                )

            # Interactive mode
            console.print(_("cli-ai-chat-assistant-title"))
            console.print(f"{_('cli-ai-chat-instructions')}\n")

            conversation_history = []

            while True:
                try:
                    user_input = console.input(f"{_('cli-ai-chat-user-prompt')} ").strip()
                    if not user_input:
                        continue
                    if user_input.lower() in ("exit", "quit", "q"):
                        console.print(_("cli-ai-chat-exit-message"))
                        break

                    # Add to history
                    conversation_history.append({"role": "user", "content": user_input})

                    # Create context with history
                    context = ChatContext(
                        user_input=user_input,
                        conversation_history=_convert_history(conversation_history),
                    )

                    if stream:
                        console.print(f"{_('cli-ai-chat-assistant-label')} ", end="")
                        full_response = ""
                        async for event in agent.execute_stream(context):
                            if event.is_content():
                                text = event.get_text()
                                console.print(text, end="")
                                full_response += text
                        console.print()  # New line
                        # Add assistant response to history
                        conversation_history.append({"role": "assistant", "content": full_response})
                    else:
                        response = await agent.execute(context)
                        if json_output:
                            console.print_json(data=response.model_dump())
                        else:
                            console.print(f"{_('cli-ai-chat-assistant-label')} {response.content}")
                        # Add to history
                        conversation_history.append(
                            {"role": "assistant", "content": response.content}
                        )

                    console.print()  # Empty line between exchanges

                except KeyboardInterrupt:
                    console.print(f"\n{_('cli-ai-chat-interrupted')}")
                    continue
                except EOFError:
                    console.print(f"\n{_('cli-ai-chat-exit-message')}")
                    break

            # Interactive mode completed successfully
            success = True

    except Exception as e:
        logger.error("Chat execution failed", error=str(e))
        console.print(_("cli-ai-chat-error", error=str(e)))
        raise typer.Exit(1)
    finally:
        # Publish AICommandCompletedEvent (only for single message mode or on exit from interactive)
        if event_bus and message:  # Single message mode
            latency_ms = (time.time() - start_time) * 1000
            event_bus.publish(
                AICommandCompletedEvent(
                    command="chat",
                    success=success,
                    tokens_used=tokens_used,
                    cost_usd=cost_usd,
                    latency_ms=latency_ms,
                )
            )
        elif event_bus and not message:  # Interactive mode on exit
            latency_ms = (time.time() - start_time) * 1000
            event_bus.publish(
                AICommandCompletedEvent(
                    command="chat",
                    success=success,
                    tokens_used=0,  # Interactive mode - tokens tracked per message
                    cost_usd=0.0,  # Interactive mode - cost tracked per message
                    latency_ms=latency_ms,
                )
            )
