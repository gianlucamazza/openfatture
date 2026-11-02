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

import asyncio
import sys
from typing import Any, Literal

TRANSMIT_TOOL_NAMES = frozenset({"send_invoice_to_sdi"})

# Confirm-like keys only. ``source`` is a real tool parameter (knowledge search)
# and a separate keyword-only argument to ``execute_tool``.
CONFIRM_LIKE_PARAMETER_NAMES = frozenset({"confirm", "confirmed", "confirmation"})
RESERVED_TOOL_PARAMETER_NAMES = CONFIRM_LIKE_PARAMETER_NAMES

_INVOICE_ID_KEYS = ("fattura_id", "invoice_id")
_INVOICE_NUMBER_KEYS = ("numero", "invoice_number")
_CLIENT_KEYS = ("cliente", "cliente_nome", "client", "client_name", "denominazione")
_TOTAL_KEYS = ("totale", "total", "importo")

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
    """Drop confirm-like keys (case-insensitive) so the model cannot self-confirm."""
    return {
        key: value
        for key, value in parameters.items()
        if key.lower() not in CONFIRM_LIKE_PARAMETER_NAMES
    }


def is_interactive() -> bool:
    """Return True only when both stdin and stdout are a TTY."""
    stdin_isatty = getattr(sys.stdin, "isatty", None)
    stdout_isatty = getattr(sys.stdout, "isatty", None)
    return bool(
        callable(stdin_isatty) and stdin_isatty() and callable(stdout_isatty) and stdout_isatty()
    )


def _first_present(parameters: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in parameters and parameters[key] not in (None, ""):
            return parameters[key]
        for actual, value in parameters.items():
            if actual.lower() == key.lower() and value not in (None, ""):
                return value
    return None


def _safe_display(value: Any) -> str:
    """Render a model- or DB-provided value for a Rich prompt."""
    text = " ".join(str(value).split())
    if len(text) > 80:
        text = text[:77] + "..."
    try:
        from rich.markup import escape

        return escape(text)
    except Exception:
        return text.replace("[", "\\[")


def _lookup_local_invoice_context(fattura_id: Any) -> dict[str, Any]:
    """Best-effort local DB read. Never talks to SDI/PEC. Failures are empty."""
    try:
        invoice_id = int(fattura_id)
    except (TypeError, ValueError):
        return {}
    try:
        from openfatture.billing.application.invoice_queries import get_invoice_details

        details = get_invoice_details(invoice_id)
    except Exception:
        return {}
    if not isinstance(details, dict) or details.get("error"):
        return {}
    client = ""
    cliente = details.get("cliente") or {}
    if isinstance(cliente, dict):
        client = str(cliente.get("denominazione") or "")
    importi = details.get("importi") or {}
    total = importi.get("totale") if isinstance(importi, dict) else None
    return {
        "client": client,
        "total": total,
        "numero": details.get("numero"),
    }


def format_confirmation_details(parameters: dict[str, Any]) -> str:
    """Describe what the call will send, using parameters plus a cheap local lookup."""
    invoice_id = _first_present(parameters, _INVOICE_ID_KEYS)
    invoice_number = _first_present(parameters, _INVOICE_NUMBER_KEYS)
    client = _first_present(parameters, _CLIENT_KEYS)
    total = _first_present(parameters, _TOTAL_KEYS)

    extras: dict[str, Any] = {}
    if invoice_id is not None and (not client or total is None or not invoice_number):
        extras = _lookup_local_invoice_context(invoice_id)
        invoice_number = invoice_number or extras.get("numero")
        client = client or extras.get("client")
        if total is None:
            total = extras.get("total")

    parts: list[str] = []
    if invoice_id is not None:
        parts.append(f"invoice ID {_safe_display(invoice_id)}")
    if invoice_number not in (None, ""):
        parts.append(f"number {_safe_display(invoice_number)}")
    if client not in (None, ""):
        parts.append(f"client {_safe_display(client)}")
    if total not in (None, ""):
        parts.append(f"total {_safe_display(total)}")
    return ", ".join(parts)


def build_confirmation_prompt(tool_name: str, parameters: dict[str, Any] | None = None) -> str:
    """Build the TTY confirmation prompt, including invoice identity when present."""
    details = format_confirmation_details(parameters or {})
    suffix = "This can transmit or mutate data and cannot be undone"
    if details:
        return f"Execute {tool_name}? {details}. {suffix}"
    return f"Execute {tool_name}? {suffix}"


def _ask_tty_confirmation(prompt: str) -> bool:
    """Blocking TTY ask. Default is no. Any failure is a refusal."""
    try:
        from rich.prompt import Confirm

        return bool(Confirm.ask(prompt, default=False))
    except (EOFError, KeyboardInterrupt, OSError):
        return False


async def prompt_human_confirmation(
    tool_name: str,
    parameters: dict[str, Any] | None = None,
) -> bool:
    """Ask on a TTY without blocking the event loop. Default is no.

    Refuses when stdin/stdout are not a TTY (including a running loop with
    no interactive terminal). The blocking ``input()`` runs in a worker
    thread via ``asyncio.to_thread``.
    """
    if not is_interactive():
        return False
    prompt = build_confirmation_prompt(tool_name, parameters or {})
    try:
        return bool(await asyncio.to_thread(_ask_tty_confirmation, prompt))
    except (EOFError, KeyboardInterrupt, OSError):
        return False


async def has_human_confirmation(
    *,
    source: ToolSource,
    confirmed: bool,
    tool_name: str,
    parameters: dict[str, Any] | None = None,
) -> bool:
    """Return True only after an explicit human yes.

    ``confirmed`` is ignored unless ``source="human"``. The AI layer therefore
    cannot self-confirm by passing a flag. When no human path has confirmed,
    an interactive TTY may prompt off the event loop; otherwise this refuses.
    """
    if source == "human" and confirmed:
        return True
    if not is_interactive():
        return False
    return await prompt_human_confirmation(tool_name, parameters)
