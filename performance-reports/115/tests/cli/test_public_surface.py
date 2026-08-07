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
    import json

    result = runner.invoke(app, ["status", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "version" in payload
    assert "ai_provider" in payload
    assert "extras" in payload
    assert isinstance(payload["extras"], dict)
    assert payload["extensions"]["in_process_plugins"] == "unsupported"
    assert "hooks_dir" in payload["extensions"]
    assert payload["feature_flags"]["lightning_allow_mock"] is False
    assert "limitations" in payload
    readiness = payload["readiness"]
    assert "core_ready" in readiness
    assert "assistant_ready" in readiness
    assert "checks" in readiness
    assert "next_steps" in readiness
    assert isinstance(readiness["next_steps"], list)
