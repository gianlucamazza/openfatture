"""Contract tests for the intentionally small public CLI."""

from typer.testing import CliRunner

from openfatture.cli.main import app

runner = CliRunner()


def test_public_commands_are_agent_first() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    # Core commands
    for command in ("assistant", "interactive", "init", "config", "status"):
        assert command in result.stdout
    # First-class data commands (added per UX improvements)
    for command in ("cliente", "fattura"):
        assert command in result.stdout
    # Commands that should remain hidden/removed
    for removed in ("preventivo", "payment", "ai", "plugin", "web-scraper"):
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
    assert "assistant_available" in payload["feature_flags"]
    assert "limitations" in payload
    readiness = payload["readiness"]
    assert "core_ready" in readiness
    assert "assistant_ready" in readiness
    assert "checks" in readiness
    assert "next_steps" in readiness
    assert isinstance(readiness["next_steps"], list)


def test_init_runs_directly_without_nested_subcommand(tmp_path, monkeypatch) -> None:
    from types import SimpleNamespace

    from openfatture.cli.commands import init

    settings = SimpleNamespace(
        data_dir=tmp_path / "data",
        archivio_dir=tmp_path / "archive",
        certificates_dir=tmp_path / "certificates",
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
    )
    monkeypatch.setattr(init, "get_settings", lambda: settings)
    databases = []
    monkeypatch.setattr(init, "init_db", databases.append)

    result = runner.invoke(app, ["init", "--no-interactive"])

    assert result.exit_code == 0, result.output
    assert "Setup Complete" in result.stdout
    assert databases == [settings.database_url]
    assert settings.data_dir.is_dir()
    assert settings.archivio_dir.is_dir()
    assert settings.certificates_dir.is_dir()


def test_no_command_shows_help_without_error():
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "Usage:" in result.stdout
    assert "assistant" in result.stdout
