"""Enablement and human-confirmation policy for AI tools.

Fail-closed defaults:

- Transmit tools (SDI/PEC send) are off unless their name is listed in
  ``ai_enabled_tools``. The value ``all`` does **not** enable them.
- ``ai_tools_require_confirmation`` defaults to True. When True, tools that
  require confirmation (including every transmit tool) refuse unless a human
  has approved. When False, confirmation is skipped, but transmit tools still
  require an explicit ``ai_enabled_tools`` opt-in.
- The model / AI tool layer cannot grant confirmation. ``confirmed=True`` is
  honoured only when ``source="human"``. An interactive TTY may prompt; a
  non-interactive session refuses. Nothing auto-confirms.
"""

from __future__ import annotations

import sys
from typing import Any, Literal

TRANSMIT_TOOL_NAMES = frozenset({"send_invoice_to_sdi"})

RESERVED_TOOL_PARAMETER_NAMES = frozenset({"confirm", "confirmed", "confirmation", "source"})

ToolSource = Literal["ai", "human"]


def parse_enabled_tools(raw: str) -> frozenset[str] | None:
    """Parse ``ai_enabled_tools``.

    Returns a set of tool names, or ``None`` when the value means every
    non-transmit tool (empty string or ``all``).
    """
    text = (raw or "").strip()
    if not text or text.lower() == "all":
        return None
    return frozenset(part.strip() for part in text.split(",") if part.strip())


def is_transmit_tool(tool_name: str) -> bool:
    """Return True when the tool transmits to SDI/PEC or another network."""
    return tool_name in TRANSMIT_TOOL_NAMES


def is_tool_enabled_for_agent(
    tool_name: str,
    enabled_tools: str,
    *,
    apply_allowlist: bool,
    tool_enabled: bool,
) -> bool:
    """Return whether the AI agent may see or execute ``tool_name``."""
    allowlist = parse_enabled_tools(enabled_tools)
    if is_transmit_tool(tool_name):
        return allowlist is not None and tool_name in allowlist
    if apply_allowlist:
        if allowlist is None:
            return tool_enabled
        return tool_enabled and tool_name in allowlist
    return tool_enabled


def confirmation_required(
    tool_name: str,
    *,
    tool_requires_confirmation: bool,
    require_confirmation: bool,
) -> bool:
    """Return whether a human yes is required before execution."""
    if is_transmit_tool(tool_name):
        return require_confirmation
    return tool_requires_confirmation and require_confirmation


def strip_reserved_parameters(parameters: dict[str, Any]) -> dict[str, Any]:
    """Drop confirm/source keys so the model cannot smuggle a self-confirm."""
    return {
        key: value for key, value in parameters.items() if key not in RESERVED_TOOL_PARAMETER_NAMES
    }


def is_interactive() -> bool:
    """Return True only when both stdin and stdout are a TTY."""
    stdin_isatty = getattr(sys.stdin, "isatty", None)
    stdout_isatty = getattr(sys.stdout, "isatty", None)
    return bool(
        callable(stdin_isatty) and stdin_isatty() and callable(stdout_isatty) and stdout_isatty()
    )


def prompt_human_confirmation(tool_name: str) -> bool:
    """Ask on a TTY. Default is no. Any prompt failure is a refusal."""
    try:
        from rich.prompt import Confirm

        return bool(
            Confirm.ask(
                f"Execute {tool_name}? This can transmit or mutate data and cannot be undone",
                default=False,
            )
        )
    except (EOFError, KeyboardInterrupt, OSError):
        return False


def has_human_confirmation(
    *,
    source: ToolSource,
    confirmed: bool,
    tool_name: str,
) -> bool:
    """Return True only after an explicit human yes.

    ``confirmed`` is ignored unless ``source="human"``. The AI layer therefore
    cannot self-confirm by passing a flag. When no human path has confirmed,
    an interactive TTY may prompt; otherwise this refuses.
    """
    if source == "human" and confirmed:
        return True
    if not is_interactive():
        return False
    return prompt_human_confirmation(tool_name)
