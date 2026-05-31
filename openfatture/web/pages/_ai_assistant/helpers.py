"""Helper functions for the AI Assistant page.

Extracted from ``5_🤖_AI_Assistant.py`` to keep the page thin and make the
logic independently importable and testable.
"""

from collections.abc import Callable
from typing import Any

import streamlit as st

from openfatture.utils.retry import RetryConfig, retry_async
from openfatture.web.utils.i18n import get_translator

# Initialize translator (same instance/interface used by the page)
t = get_translator()


async def retry_with_backoff(
    func: Callable[[], Any],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
) -> Any:
    """
    Execute a function with exponential backoff retry logic.

    This is a thin wrapper around :func:`openfatture.utils.retry.retry_async`
    that preserves the original public signature and observable semantics:

    - The function is attempted up to ``max_retries + 1`` times (the original
      ``for attempt in range(max_retries + 1)`` loop).
    - The same exception is propagated when all attempts fail.
    - A user-facing ``st.warning`` is shown before each retry, using the same
      ``page-ai-retry-message`` translation as before.

    Args:
        func: Async function to execute
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        backoff_factor: Factor to multiply delay by on each retry

    Returns:
        Result of the function call

    Raises:
        Exception: Last exception if all retries fail
    """
    # The original implementation computed the warned delay as
    # ``min(base_delay * backoff_factor ** (attempt + 1), max_delay)`` for the
    # 0-indexed retry attempt. ``RetryConfig.calculate_delay`` (without jitter)
    # uses ``min(base_delay * backoff_factor ** attempt, max_delay)``, so we
    # offset by one to reproduce the exact message and sleep duration.
    config = RetryConfig(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        backoff_factor=backoff_factor,
        jitter=False,
    )

    async def on_retry(error: Exception, attempt: int) -> None:
        # ``attempt`` here is 1-indexed (retry_async passes attempt + 1).
        delay = config.calculate_delay(attempt)
        retry_msg = t(
            "page-ai-retry-message",
            attempt=attempt,
            max_retries=max_retries + 1,
            delay=delay,
        )
        st.warning(retry_msg)

    return await retry_async(func, config=config, on_retry=on_retry)


def handle_chat_error(error: Exception, context: str = "chat") -> str:
    """
    Handle chat-related errors with user-friendly messages.

    Args:
        error: The exception that occurred
        context: Context where the error occurred

    Returns:
        User-friendly error message
    """
    error_str = str(error).lower()

    # Network/API errors
    if any(keyword in error_str for keyword in ["connection", "timeout", "network", "api"]):
        return t("page-ai-error-connection")

    # Authentication errors
    elif any(keyword in error_str for keyword in ["auth", "token", "key", "unauthorized"]):
        return t("page-ai-error-auth")

    # Rate limiting
    elif any(keyword in error_str for keyword in ["rate", "limit", "quota"]):
        return t("page-ai-error-rate-limit")

    # Model/service unavailable
    elif any(keyword in error_str for keyword in ["model", "service", "unavailable"]):
        return t("page-ai-error-service-unavailable")

    # Generic error
    else:
        return t("page-ai-error-generic", error=str(error)[:100])


def handle_slash_command(
    user_input: str,
    custom_commands_service: Any,
    history: list[dict[str, str]],
) -> tuple[str | None, str | None]:
    """
    Handle slash commands in chat input.

    Args:
        user_input: User input that may contain a slash command
        custom_commands_service: Custom commands service instance
        history: Current conversation history (used by ``/stats``)

    Returns:
        Tuple of (expanded_message, command_feedback)
        - expanded_message: The expanded command or None if not a command
        - command_feedback: User feedback message about command execution
    """
    if not user_input.startswith("/"):
        return None, None

    # Parse command
    parts = user_input.split()
    command = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []

    # Handle built-in commands
    if command == "/help":
        feedback = t("page-ai-command-help-feedback")
        return None, feedback

    elif command == "/tools":
        # Show available AI tools
        tools_info = t("page-ai-command-tools-feedback")
        return None, tools_info

    elif command == "/stats":
        # Show conversation statistics
        total_messages = len(history)
        user_messages = len([msg for msg in history if msg["role"] == "user"])
        assistant_messages = len([msg for msg in history if msg["role"] == "assistant"])

        # Calculate approximate token usage (rough estimate)
        total_chars = sum(len(msg["content"]) for msg in history)
        estimated_tokens = total_chars // 4  # Rough approximation

        feedback = t(
            "page-ai-command-stats-feedback",
            total_messages=total_messages,
            user_messages=user_messages,
            assistant_messages=assistant_messages,
            total_chars=total_chars,
            estimated_tokens=estimated_tokens,
        )
        return None, feedback

    elif command == "/custom":
        commands = custom_commands_service.list_commands()
        if not commands:
            feedback = t("page-ai-command-custom-no-commands")
        else:
            feedback = t("page-ai-command-custom-header", count=len(commands)) + "\n\n"
            for cmd in commands:
                aliases = f" ({', '.join(cmd['aliases'])})" if cmd["aliases"] else ""
                feedback += f"- `/{cmd['name']}`{aliases}: {cmd['description']}\n"
            feedback += "\n" + t("page-ai-command-custom-footer")
        return None, feedback

    elif command == "/reload":
        try:
            result = custom_commands_service.reload_commands()
            feedback = t(
                "page-ai-command-reload-success",
                old_count=result["old_count"],
                new_count=result["new_count"],
                added=result["added"],
                removed=result["removed"],
            )
        except Exception as e:
            feedback = t("page-ai-command-reload-error", error=str(e))
        return None, feedback

    elif command == "/clear":
        # This will be handled by the clear button, just show feedback
        return None, t("page-ai-command-clear-feedback")

    # Handle custom commands
    elif custom_commands_service.has_command(command):
        try:
            expanded = custom_commands_service.execute_command(command, args)
            feedback = t("page-ai-command-custom-expanded", command=command, length=len(expanded))
            return expanded, feedback
        except ValueError as e:
            return None, t("page-ai-command-custom-error", error=str(e))

    # Unknown command
    else:
        return (None, t("page-ai-command-unknown", command=command))
