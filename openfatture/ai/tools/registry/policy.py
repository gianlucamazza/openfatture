"""Enablement and human-confirmation policy for AI tools.

Access is decided by each tool's :class:`ToolRisk`, not by a list of names:

- ``ai_tool_access`` picks which risk classes the agent sees:
  ``read`` (lookups only), ``standard`` (lookups plus local files in the
  exports directory: PDF, CSV export) or ``full`` (also creates, changes and
  deletes records, each behind a human confirmation).
- ``ai_enabled_tools`` adds single tools by name on top of that level. It is
  the only way to enable a transmit tool (SDI/PEC send); no access level does.
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
from typing import TYPE_CHECKING, Any, Literal

from openfatture.ai.tools.models import Tool, ToolRisk
from openfatture.platform.config import AiToolAccess

if TYPE_CHECKING:
    from openfatture.platform.config import Settings

# Confirm-like keys only. ``source`` is a real tool parameter (knowledge search)
# and a separate keyword-only argument to ``execute_tool``.
CONFIRM_LIKE_PARAMETER_NAMES = frozenset({"confirm", "confirmed", "confirmation"})
RESERVED_TOOL_PARAMETER_NAMES = CONFIRM_LIKE_PARAMETER_NAMES

_INVOICE_ID_KEYS = ("fattura_id", "invoice_id")
_INVOICE_NUMBER_KEYS = ("numero", "invoice_number")
_CLIENT_KEYS = ("cliente", "cliente_nome", "client", "client_name", "denominazione")
_TOTAL_KEYS = ("totale", "total", "importo")

ToolSource = Literal["ai", "human"]
ACCESS_RISKS: dict[AiToolAccess, frozenset[ToolRisk]] = {
    "read": frozenset({ToolRisk.READ}),
    "standard": frozenset({ToolRisk.READ, ToolRisk.LOCAL_ARTIFACT}),
    "full": frozenset({ToolRisk.READ, ToolRisk.LOCAL_ARTIFACT, ToolRisk.MUTATE}),
}


def parse_enabled_tools(raw: str) -> frozenset[str]:
    """Parse ``ai_enabled_tools`` into the set of extra tool names."""
    return frozenset(part.strip() for part in (raw or "").split(",") if part.strip())


def is_transmit_tool(tool: Tool) -> bool:
    """Return True when the tool transmits to SDI/PEC or another network."""
    return tool.risk is ToolRisk.TRANSMIT


def minimum_access_for(risk: ToolRisk) -> AiToolAccess | None:
    """Lowest ``ai_tool_access`` that exposes ``risk``; None for transmit."""
    return next((level for level, risks in ACCESS_RISKS.items() if risk in risks), None)


def is_tool_enabled_for_agent(tool: Tool, settings: Settings, *, apply_access: bool) -> bool:
    """Return whether the AI agent may see or execute ``tool``.

    ``apply_access`` is False for registries that do not serve the assistant
    (tests, human callers): they honour only the tool flag. Transmit tools need
    an explicit name in ``ai_enabled_tools`` in every case.
    """
    extra = parse_enabled_tools(settings.ai_enabled_tools)
    if is_transmit_tool(tool):
        return tool.name in extra
    if not apply_access:
        return tool.enabled
    return tool.enabled and (
        tool.risk in ACCESS_RISKS[settings.ai_tool_access] or tool.name in extra
    )


def access_command(level: AiToolAccess) -> str:
    """The command that sets ``ai_tool_access`` to ``level``."""
    return f"openfatture config set ai_tool_access {level}"


def disabled_remediation(tool: Tool) -> str:
    """The configuration command that would expose ``tool`` to the assistant."""
    level = minimum_access_for(tool.risk)
    if level is None:
        return f"openfatture config set ai_enabled_tools {tool.name}"
    return access_command(level)


def confirmation_required(tool: Tool, *, require_confirmation: bool) -> bool:
    """Return whether a human yes is required before execution."""
    if is_transmit_tool(tool):
        return require_confirmation
    return tool.requires_confirmation and require_confirmation


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
