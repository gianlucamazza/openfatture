"""Contract tests for the intentionally small public CLI."""

from typer.testing import CliRunner

from openfatture.cli.main import app

runner = CliRunner()


def test_public_commands_are_agent_first() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    for command in ("assistant", "interactive", "init", "config", "status"):
        assert command in result.stdout
    for removed in ("cliente", "fattura", "preventivo", "payment", "ai", "plugin", "web-scraper"):
        assert removed not in result.stdout


def test_status_supports_machine_readable_output() -> None:
    result = runner.invoke(app, ["status", "--json"])

    assert result.exit_code == 0
    assert '"version"' in result.stdout
    assert '"ai_provider"' in result.stdout
