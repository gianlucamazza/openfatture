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
  honoured only when ``source="human"``. The CLI assistant may prompt on a
  TTY after opting in; a TTY alone is not enough. A non-interactive
  session refuses. Nothing auto-confirms.
"""

from __future__ import annotations

import asyncio
import os
import sys
import threading
from typing import TYPE_CHECKING, Any, Literal

from openfatture.ai.tools.models import Tool, ToolRisk
from openfatture.platform.config import AiToolAccess, parse_enabled_tools

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
    "standard": frozenset({ToolRisk.READ, ToolRisk.LOOKUP, ToolRisk.LOCAL_ARTIFACT}),
    "full": frozenset({ToolRisk.READ, ToolRisk.LOOKUP, ToolRisk.LOCAL_ARTIFACT, ToolRisk.MUTATE}),
}


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
    if tool.risk is ToolRisk.LOOKUP and settings.ai_offline:
        return False
    return tool.enabled and (
        tool.risk in ACCESS_RISKS[settings.ai_tool_access] or tool.name in extra
    )


OFFLINE_COMMAND = "openfatture config set ai_offline false"


def access_command(level: AiToolAccess) -> str:
    """The command that sets ``ai_tool_access`` to ``level``."""
    return f"openfatture config set ai_tool_access {level}"


def disabled_remediation(tool: Tool, settings: Settings | None = None) -> str:
    """The configuration command that would expose ``tool`` to the assistant."""
    if tool.risk is ToolRisk.LOOKUP and settings is not None and settings.ai_offline:
        return OFFLINE_COMMAND
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


_INTERACTIVE_ENV = "OPENFATTURE_INTERACTIVE"
_TRUTHY_ENV = frozenset({"1", "true", "yes", "on"})
_FALSY_ENV = frozenset({"0", "false", "no", "off"})

# The CLI assistant opts in for the duration of a run. A TTY alone must not
# make a server started from a terminal prompt on its own stdin.
_interactive_session = False


def set_interactive_session(enabled: bool) -> None:
    """Opt this process in or out of TTY confirmation prompts."""
    global _interactive_session
    _interactive_session = bool(enabled)


def _env_interactive_override() -> bool | None:
    raw = os.environ.get(_INTERACTIVE_ENV)
    if raw is None or not raw.strip():
        return None
    value = raw.strip().lower()
    if value in _TRUTHY_ENV:
        return True
    if value in _FALSY_ENV:
        return False
    return None


def _stdin_stdout_are_tty() -> bool:
    stdin_isatty = getattr(sys.stdin, "isatty", None)
    stdout_isatty = getattr(sys.stdout, "isatty", None)
    return bool(
        callable(stdin_isatty) and stdin_isatty() and callable(stdout_isatty) and stdout_isatty()
    )


def is_interactive() -> bool:
    """Return True when a CLI (or env) session opted in and stdin/stdout are a TTY.

    A TTY is required but not sufficient. ``set_interactive_session(True)`` is
    called by the CLI assistant; ``OPENFATTURE_INTERACTIVE=1`` is the same
    opt-in for other human-facing callers. ``OPENFATTURE_INTERACTIVE=0``
    forces a refusal even inside the CLI.
    """
    override = _env_interactive_override()
    if override is False:
        return False
    if not (override is True or _interactive_session):
        return False
    return _stdin_stdout_are_tty()


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


def _comparable_value(value: Any) -> Any:
    """Normalize a model or DB value so '1220' and 1220.0 compare equal."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return float(value)
    text = " ".join(str(value).split())
    try:
        return float(text)
    except ValueError:
        return text.casefold()


def _values_differ(model: Any, database: Any) -> bool:
    if model in (None, "") or database in (None, ""):
        return False
    return bool(_comparable_value(model) != _comparable_value(database))


def _describe_field(label: str, *, database: Any, model: Any) -> str | None:
    """Prefer a database value; label a model-only value or a mismatch."""
    if database not in (None, ""):
        text = f"{label} {_safe_display(database)}"
        if _values_differ(model, database):
            text += f" (from database; model provided {_safe_display(model)})"
        return text
    if model not in (None, ""):
        return f"{label} {_safe_display(model)} (model provided)"
    return None


def format_confirmation_details(parameters: dict[str, Any]) -> str:
    """Describe what the call will send, preferring local DB values.

    Invoice ID comes from the call (it is the lookup key). Client, total and
    number come from the local database when present; a conflicting
    model-supplied value is labelled, and a value present only on the model
    is labelled as model-provided, so it cannot disguise the invoice.
    """
    invoice_id = _first_present(parameters, _INVOICE_ID_KEYS)
    model_number = _first_present(parameters, _INVOICE_NUMBER_KEYS)
    model_client = _first_present(parameters, _CLIENT_KEYS)
    model_total = _first_present(parameters, _TOTAL_KEYS)

    extras: dict[str, Any] = {}
    if invoice_id is not None:
        extras = _lookup_local_invoice_context(invoice_id)

    parts: list[str] = []
    if invoice_id is not None:
        parts.append(f"invoice ID {_safe_display(invoice_id)}")
    for field in (
        _describe_field("number", database=extras.get("numero"), model=model_number),
        _describe_field("client", database=extras.get("client"), model=model_client),
        _describe_field("total", database=extras.get("total"), model=model_total),
    ):
        if field is not None:
            parts.append(field)
    return ", ".join(parts)


def build_confirmation_prompt(tool_name: str, parameters: dict[str, Any] | None = None) -> str:
    """Build the TTY confirmation prompt, including invoice identity when present."""
    details = format_confirmation_details(parameters or {})
    suffix = "This can transmit or mutate data and cannot be undone"
    if details:
        return f"Execute {tool_name}? {details}. {suffix}"
    return f"Execute {tool_name}? {suffix}"


def _stdin_is_ready(timeout: float) -> bool:
    """Return True when stdin has data, without consuming it."""
    try:
        fd = sys.stdin.fileno()
    except (AttributeError, OSError, ValueError):
        return True
    try:
        import select

        ready, _, _ = select.select([fd], [], [], timeout)
        return bool(ready)
    except (OSError, ValueError, AttributeError):
        if os.name != "nt":
            return False
        try:
            import msvcrt
            import time

            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                if msvcrt.kbhit():  # type: ignore[attr-defined]
                    return True
                time.sleep(min(0.05, max(0.0, deadline - time.monotonic())))
            return False
        except Exception:
            return False


def _parse_yes_no(line: str) -> bool | None:
    """Interpret a confirmation line. None means the question should be repeated."""
    answer = line.strip().casefold()
    if answer in {"", "n", "no"}:
        return False
    if answer in {"y", "yes"}:
        return True
    return None


def _write_prompt(text: str) -> None:
    try:
        from rich.console import Console

        Console().print(text, end="")
    except Exception:
        print(text, end="", flush=True)


def _ask_tty_confirmation(prompt: str, cancelled: threading.Event | None = None) -> bool:
    """TTY ask that can stop without reading stdin if ``cancelled`` is set.

    Default is no. Any failure is a refusal. A stale prompt after cancel or
    timeout must not consume the next line of input, so this polls stdin
    and returns as soon as ``cancelled`` is set, without calling readline.
    """
    stop = cancelled if cancelled is not None else threading.Event()
    suffix = " [y/N]: "
    try:
        _write_prompt(prompt + suffix)
        while not stop.is_set():
            if not _stdin_is_ready(0.1):
                continue
            if stop.is_set():
                return False
            line = sys.stdin.readline()
            if stop.is_set():
                return False
            if line == "":
                return False
            parsed = _parse_yes_no(line)
            if parsed is not None:
                return parsed
            _write_prompt("Please enter Y or N" + suffix)
        return False
    except (EOFError, KeyboardInterrupt, OSError):
        return False


def _confirm_on_tty(
    tool_name: str,
    parameters: dict[str, Any],
    cancelled: threading.Event,
) -> bool:
    """Build the prompt (including the local DB lookup) and ask, off the event loop."""
    prompt = build_confirmation_prompt(tool_name, parameters)
    return _ask_tty_confirmation(prompt, cancelled)


async def prompt_human_confirmation(
    tool_name: str,
    parameters: dict[str, Any] | None = None,
) -> bool:
    """Ask on a TTY without blocking the event loop. Default is no.

    Refuses when the process has not opted into an interactive session or
    when stdin/stdout are not a TTY. The local invoice lookup and the
    blocking stdin read both run in a worker thread via ``asyncio.to_thread``.
    If this task is cancelled or times out, the worker is signalled so it
    does not swallow the next line of input.
    """
    if not is_interactive():
        return False
    cancelled = threading.Event()
    try:
        return bool(
            await asyncio.to_thread(_confirm_on_tty, tool_name, parameters or {}, cancelled)
        )
    except (EOFError, KeyboardInterrupt, OSError):
        return False
    finally:
        cancelled.set()


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
    the CLI assistant may prompt off the event loop on a TTY; otherwise
    this refuses.
    """
    if source == "human" and confirmed:
        return True
    if not is_interactive():
        return False
    return await prompt_human_confirmation(tool_name, parameters)
