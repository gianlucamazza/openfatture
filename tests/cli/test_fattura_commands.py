"""Tests for the SDI commands that need a person's evidence."""

from typer.testing import CliRunner

from openfatture.cli.main import app

runner = CliRunner()


def test_resolve_unknown_submission_is_localized(runtime_db):
    result = runner.invoke(
        app,
        ["fattura", "resolve-submission", "424242", "--sent", "--evidence", "PEC ref"],
        input="y\n",
    )

    assert result.exit_code == 1
    assert "Tentativo di invio non trovato." in result.stdout
    assert "Traceback" not in result.output


def test_json_keeps_the_service_error_and_code(runtime_db):
    import json

    result = runner.invoke(
        app,
        [
            "--format",
            "json",
            "fattura",
            "resolve-submission",
            "424242",
            "--sent",
            "--evidence",
            "PEC ref",
        ],
        input="y\n",
    )

    error = json.loads(result.stdout)["error"]
    assert error["code"] == "submission_not_found"
