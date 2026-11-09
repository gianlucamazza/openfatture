"""One output contract for non-conversational public CLI commands."""

import io
import json
from contextlib import redirect_stdout
from contextvars import ContextVar
from html import escape
from typing import Any
from unittest.mock import patch

import click
import typer
from rich.console import Console
from rich.table import Table
from typer.core import TyperGroup

from openfatture.platform.logging import redact_sensitive

FORMAT_NAMES = {"rich", "json", "markdown", "html", "stream-json"}
_result: ContextVar[Any] = ContextVar("cli_result", default=None)


def remember_result(value: Any) -> None:
    _result.set(value)


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


class OutputGroup(TyperGroup):
    def invoke(self, ctx: click.Context) -> Any:
        kind = ctx.params.get("format_type", "rich")
        if kind not in FORMAT_NAMES:
            raise click.BadParameter(
                "Supported formats: " + ", ".join(sorted(FORMAT_NAMES)), param_hint="--format"
            )
        args = [*getattr(ctx, "_protected_args", []), *ctx.args]
        if kind == "rich" or (args and args[0] == "assistant"):
            return super().invoke(ctx)
        if args and args[0] == "interactive":
            emit(
                {
                    "success": False,
                    "error": {
                        "code": "interactive_format",
                        "message": "Use assistant with a single request for machine-readable output",
                    },
                },
                kind,
            )
            raise click.exceptions.Exit(2)
        buffer = io.StringIO()
        tables = []
        token = _result.set(None)
        original_print, original_confirm, original_prompt = (
            Console.print,
            typer.confirm,
            typer.prompt,
        )

        def capture(console: Console, *values: Any, **kwargs: Any) -> None:
            if not console.stderr:
                for value in values:
                    if isinstance(value, Table):
                        tables.append(
                            {
                                "title": str(value.title or ""),
                                "columns": [str(c.header) for c in value.columns],
                                "rows": [
                                    [str(c._cells[i]) for c in value.columns]
                                    for i in range(value.row_count)
                                ],
                            }
                        )
            return original_print(console, *values, **kwargs)

        def confirm(*args: Any, **kwargs: Any) -> Any:
            kwargs["err"] = True
            return original_confirm(*args, **kwargs)

        def prompt(*args: Any, **kwargs: Any) -> Any:
            kwargs["err"] = True
            return original_prompt(*args, **kwargs)

        error, code = None, 0
        try:
            with (
                redirect_stdout(buffer),
                patch.object(Console, "print", capture),
                patch.object(typer, "confirm", confirm),
                patch.object(typer, "prompt", prompt),
            ):
                try:
                    returned = super().invoke(ctx)
                except click.exceptions.Exit as exc:
                    code = exc.exit_code
                    returned = None
                except click.Abort:
                    code, returned = 1, None
                    error = {"code": "cancelled", "message": "Operation cancelled"}
                except Exception as exc:
                    code, returned = 1, None
                    error = {
                        "code": "usage_error"
                        if isinstance(exc, click.UsageError)
                        else "operation_failed",
                        "message": str(exc),
                    }
                    if isinstance(exc, click.UsageError):
                        code = 2
            data = _result.get()
            if data is None and returned is not None:
                data = returned
            if data is None:
                try:
                    data = json.loads(buffer.getvalue())
                except ValueError:
                    data = {"tables": tables, "messages": buffer.getvalue().strip()}
            if isinstance(data, dict) and data.get("error"):
                code = code or 1
                error = {
                    "code": data.get("error_code", "operation_failed"),
                    "message": str(data["error"]),
                }
            if code and error is None:
                error = {
                    "code": "operation_failed",
                    "message": buffer.getvalue().strip() or "Operation failed",
                }
            emit({"success": code == 0, "data": data, "warnings": [], "error": error}, kind)
            if code:
                raise click.exceptions.Exit(code)
            return returned
        finally:
            _result.reset(token)
