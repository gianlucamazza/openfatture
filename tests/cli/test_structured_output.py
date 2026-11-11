"""Public command outputs are parseable and retain normal error exit codes."""

import json

import pytest
from typer.testing import CliRunner

from openfatture.cli.main import app

runner = CliRunner()


@pytest.mark.parametrize("command", [["status"], ["fattura", "sdi-journal"]])
def test_json_is_one_business_envelope(runtime_db, command):
    result = runner.invoke(app, ["--format", "json", *command])
    assert result.exit_code == 0, result.output
    envelope = json.loads(result.stdout)
    assert envelope["success"] is True
    assert "data" in envelope
    assert envelope["error"] is None


def test_domain_error_is_json(runtime_db):
    result = runner.invoke(
        app,
        ["--format", "json", "fattura", "associate-receipt", "999", "1", "--evidence", "x"],
        input="y\n",
    )
    assert result.exit_code == 1
    assert json.loads(result.stdout)["success"] is False


@pytest.mark.parametrize("kind", ["markdown", "html", "stream-json"])
def test_other_declared_formats(runtime_db, kind):
    result = runner.invoke(app, ["--format", kind, "status"])
    assert result.exit_code == 0, result.output
    if kind == "html":
        assert "<pre>" in result.stdout
    elif kind == "markdown":
        assert result.stdout.startswith("```json")
    else:
        assert json.loads(result.stdout)["type"] == "complete"


def test_unknown_format_is_usage_error():
    assert runner.invoke(app, ["--format", "invalid", "status"]).exit_code == 2


def test_interactive_init_refused_in_machine_format(runtime_db):
    result = runner.invoke(app, ["--format", "json", "init"])
    assert result.exit_code == 2
    assert json.loads(result.stdout)["success"] is False


def test_interactive_assistant_refused_as_json(runtime_db):
    result = runner.invoke(app, ["--format", "json"])
    assert result.exit_code == 2
    assert json.loads(result.stdout)["error"]["code"] == "interactive_format"


def test_secret_redaction_preserves_usage_counts():
    from openfatture.cli.output import clean

    assert clean({"access_token": "private", "tokens_used": 123, "api_key_configured": True}) == {
        "access_token": "[redacted]",
        "tokens_used": 123,
        "api_key_configured": True,
    }


def test_denied_confirmation_returns_cancelled_json_without_traceback(runtime_db):
    result = runner.invoke(
        app,
        ["--format", "json", "fattura", "associate-receipt", "1", "1", "--evidence", "PEC"],
        input="n\n",
    )
    assert result.exit_code == 1
    assert json.loads(result.stdout)["error"]["code"] == "cancelled"
    assert "Associare la ricevuta" in result.stderr
    assert "Traceback" not in result.stderr
