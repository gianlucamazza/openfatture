"""The structured-output envelope of ``OutputGroup`` for every way a command ends."""

import json
from typing import Any

import pytest
import typer
from rich.console import Console
from rich.table import Table
from typer.testing import CliRunner

from openfatture.cli.output import OutputGroup, click, remember_result

runner = CliRunner()
app = typer.Typer(cls=OutputGroup)


@app.callback()
def _root(format_type: str = typer.Option("rich", "--format")) -> None:
    """Synthetic root mirroring the public CLI."""


@app.command("table")
def _table() -> None:
    table = Table(title="Elenco")
    table.add_column("A")
    table.add_row("1")
    Console().print(table)
    Console(stderr=True).print(Table(title="ignored"))
    Console().print("done")


@app.command("prompt")
def _prompt() -> None:
    remember_result({"name": typer.prompt("Nome"), "ok": typer.confirm("Sicuro?")})


@app.command("returns")
def _returns() -> dict[str, int]:
    return {"value": 1}


@app.command("json")
def _json() -> None:
    print(json.dumps({"printed": True}))


@app.command("fail")
def _fail(kind: str) -> None:
    if kind == "exit":
        raise typer.Exit(3)
    if kind == "abort":
        raise typer.Abort()
    if kind == "usage":
        raise click.exceptions.UsageError("wrong usage")
    if kind == "domain":
        remember_result({"error": "nope", "error_code": "not_found"})
        return
    raise RuntimeError("bad")


def _envelope(args: list[str], code: int, **kwargs: Any) -> dict[str, Any]:
    result = runner.invoke(app, ["--format", "json", *args], **kwargs)
    assert result.exit_code == code, result.output
    envelope: dict[str, Any] = json.loads(result.stdout.splitlines()[-1])
    return envelope


def test_tables_and_messages_are_captured_from_stdout_only():
    envelope = _envelope(["table"], 0)
    assert envelope["data"]["tables"] == [{"title": "Elenco", "columns": ["A"], "rows": [["1"]]}]
    assert "done" in envelope["data"]["messages"]


def test_prompts_go_to_stderr():
    result = runner.invoke(app, ["--format", "json", "prompt"], input="Ada\ny\n")
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["data"] == {"name": "Ada", "ok": True}
    assert "Nome" not in result.stdout


def test_returned_value_is_the_data():
    assert _envelope(["returns"], 0)["data"] == {"value": 1}


def test_printed_json_is_the_data():
    assert _envelope(["json"], 0)["data"] == {"printed": True}


@pytest.mark.parametrize(
    ("kind", "code", "error"),
    [
        ("exit", 3, {"code": "operation_failed", "message": "Operation failed"}),
        ("abort", 1, {"code": "cancelled", "message": "Operation cancelled"}),
        ("usage", 2, {"code": "usage_error", "message": "wrong usage"}),
        ("crash", 1, {"code": "operation_failed", "message": "bad"}),
        ("domain", 1, {"code": "not_found", "message": "nope"}),
    ],
)
def test_failures_are_enveloped(kind: str, code: int, error: dict[str, str]):
    envelope = _envelope(["fail", kind], code)
    assert envelope["success"] is False
    assert envelope["error"] == error


def test_rich_format_is_untouched():
    result = runner.invoke(app, ["returns"])
    assert result.exit_code == 0
    assert result.stdout == ""
