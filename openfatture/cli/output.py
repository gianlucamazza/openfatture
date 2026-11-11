"""One output contract for non-conversational public CLI commands."""

import io
import json
from collections.abc import Callable, Iterator
from contextlib import contextmanager, redirect_stdout
from contextvars import ContextVar
from html import escape
from importlib import import_module
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import typer
from rich.console import Console
from rich.table import Table
from typer.core import TyperGroup

if TYPE_CHECKING:
    import click
else:
    try:
        click = import_module("typer._click")
    except ModuleNotFoundError:
        click = import_module("click")

from openfatture.i18n import _
from openfatture.platform.logging import redact_sensitive

FORMAT_NAMES = {"rich", "json", "markdown", "html", "stream-json"}
_result: ContextVar[Any] = ContextVar("cli_result", default=None)


def remember_result(value: Any) -> None:
    _result.set(value)


# Refusals that application services identify with an ``error_code``. Their
# ``error`` text stays English for the assistant; the CLI shows it localized.
_ERROR_MESSAGES = {
    "invoice_not_found": "cli-error-invoice-not-found",
    "invoice_issued_elsewhere": "cli-error-invoice-issued-elsewhere",
    "xml_invalid": "cli-error-xml-invalid",
    "xml_failed": "cli-error-xml-failed",
    "receipt_not_associable": "cli-error-receipt-not-associable",
    "evidence_required": "cli-error-evidence-required",
    "submission_not_found": "cli-error-submission-not-found",
    "submission_already_resolved": "cli-error-submission-already-resolved",
    "sdi_evidence_contradicts": "cli-error-sdi-evidence-contradicts",
    "submission_concurrent_update": "cli-error-submission-concurrent-update",
}


def error_message(result: dict[str, Any]) -> str:
    """The refusal in ``result`` in the user's language, else the service text."""
    key = _ERROR_MESSAGES.get(str(result.get("error_code")))
    return _(key, detail=str(result["error"])) if key else str(result["error"])


def clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(k): (
                "[redacted]"
                if (
                    any(part in str(k).lower() for part in ("password", "api_key", "secret"))
                    or str(k).lower() in ("token", "access_token", "refresh_token", "authorization")
                )
                and not str(k).endswith("_configured")
                and not str(k).endswith("_tokens")
                else clean(v)
            )
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [clean(item) for item in value]
    if isinstance(value, str):
        return redact_sensitive(value)
    return value


def emit(envelope: dict[str, Any], kind: str) -> None:
    data = json.dumps(clean(envelope), ensure_ascii=False, default=str)
    if kind == "html":
        click.echo(
            '<!doctype html><html><meta charset="utf-8"><body><pre>'
            + escape(data)
            + "</pre></body></html>"
        )
    elif kind == "markdown":
        click.echo("```json\n" + data.replace("```", "\\u0060\\u0060\\u0060") + "\n```")
    elif kind == "stream-json":
        click.echo(json.dumps({"type": "complete", **json.loads(data)}, ensure_ascii=False))
    else:
        click.echo(data)


def _table_snapshot(table: Table) -> dict[str, Any]:
    return {
        "title": str(table.title or ""),
        "columns": [str(c.header) for c in table.columns],
        "rows": [[str(c._cells[i]) for c in table.columns] for i in range(table.row_count)],
    }


class _CapturedOutput:
    """Stdout text and rich tables printed by a command in a machine format."""

    def __init__(self) -> None:
        self.buffer = io.StringIO()
        self.tables: list[dict[str, Any]] = []

    @contextmanager
    def active(self) -> Iterator[None]:
        """Capture stdout and stdout tables; send prompts and confirmations to stderr."""
        original_print, original_confirm, original_prompt = (
            Console.print,
            typer.confirm,
            typer.prompt,
        )
        tables = self.tables

        def capture(console: Console, *values: Any, **kwargs: Any) -> None:
            if not console.stderr:
                tables.extend(_table_snapshot(v) for v in values if isinstance(v, Table))
            return original_print(console, *values, **kwargs)

        def confirm(*args: Any, **kwargs: Any) -> Any:
            kwargs["err"] = True
            return original_confirm(*args, **kwargs)

        def prompt(*args: Any, **kwargs: Any) -> Any:
            kwargs["err"] = True
            return original_prompt(*args, **kwargs)

        with (
            redirect_stdout(self.buffer),
            patch.object(Console, "print", capture),
            patch.object(typer, "confirm", confirm),
            patch.object(typer, "prompt", prompt),
        ):
            yield

    def text(self) -> str:
        return self.buffer.getvalue()


def _invoke_guarded(
    invoke: Callable[[click.Context], Any], ctx: click.Context
) -> tuple[Any, int, dict[str, str] | None]:
    """Run ``invoke`` and turn how it ended into (returned, exit code, error)."""
    try:
        return invoke(ctx), 0, None
    except typer.Exit as exc:
        return None, exc.exit_code, None
    except typer.Abort:
        return None, 1, {"code": "cancelled", "message": "Operation cancelled"}
    except Exception as exc:
        usage = isinstance(exc, click.exceptions.UsageError)
        return (
            None,
            2 if usage else 1,
            {"code": "usage_error" if usage else "operation_failed", "message": str(exc)},
        )


def _result_data(returned: Any, output: _CapturedOutput) -> Any:
    """The remembered result, else the returned value, else what was printed."""
    data = _result.get()
    if data is None and returned is not None:
        data = returned
    if data is None:
        try:
            data = json.loads(output.text())
        except ValueError:
            data = {"tables": output.tables, "messages": output.text().strip()}
    return data


def _final_error(
    data: Any, code: int, error: dict[str, str] | None, output: _CapturedOutput
) -> tuple[int, dict[str, str] | None]:
    """A domain error in the data fails the command; a failing code always has an error."""
    if isinstance(data, dict) and data.get("error"):
        code = code or 1
        error = {
            "code": data.get("error_code", "operation_failed"),
            "message": str(data["error"]),
        }
    if code and error is None:
        error = {
            "code": "operation_failed",
            "message": output.text().strip() or "Operation failed",
        }
    return code, error


class OutputGroup(TyperGroup):
    # Typer adds the completion options with fixed English help text.
    # They are appended after the group is built, so localize them on use.
    _COMPLETION_HELP = {
        "install_completion": "cli-help-install-completion",
        "show_completion": "cli-help-show-completion",
    }

    def get_params(self, ctx: click.Context) -> list[click.Parameter]:
        params = super().get_params(ctx)
        for param in params:
            key = self._COMPLETION_HELP.get(param.name or "")
            if key and hasattr(param, "help"):
                param.help = _(key)
        return params

    def invoke(self, ctx: click.Context) -> Any:
        kind = ctx.params.get("format_type", "rich")
        if kind not in FORMAT_NAMES:
            raise click.exceptions.BadParameter(
                _("cli-output-unsupported-format", formats=", ".join(sorted(FORMAT_NAMES))),
                param_hint="--format",
            )
        args = [*getattr(ctx, "_protected_args", []), *ctx.args]
        if kind == "rich" or not args or args[0] == "assistant":
            return super().invoke(ctx)
        output = _CapturedOutput()
        token = _result.set(None)
        try:
            with output.active():
                returned, code, error = _invoke_guarded(super().invoke, ctx)
            data = _result_data(returned, output)
            code, error = _final_error(data, code, error, output)
            emit({"success": code == 0, "data": data, "warnings": [], "error": error}, kind)
            if code:
                raise typer.Exit(code)
            return returned
        finally:
            _result.reset(token)
