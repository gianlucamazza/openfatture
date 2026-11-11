"""Contract tests for the intentionally small public CLI."""

import re

from typer.testing import CliRunner

from openfatture.cli.main import app

runner = CliRunner()


def test_public_commands_are_agent_first() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    # Core commands
    for command in ("assistant", "init", "config", "status"):
        assert command in result.stdout
    # SDI resolutions that need a person's evidence (docs/CLI_REFERENCE.md)
    assert "fattura" in result.stdout
    # Commands that should remain hidden/removed
    for removed in (
        "interactive",
        "cliente",
        "preventivo",
        "payment",
        "pagamento",
        "ai",
        "plugin",
        "web-scraper",
    ):
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
    databases: list[str] = []
    monkeypatch.setattr(init, "init_db", databases.append)

    result = runner.invoke(app, ["init", "--no-interactive"])

    assert result.exit_code == 0, result.output
    assert "Configurazione completata" in result.stdout
    assert databases == [settings.database_url]
    assert settings.data_dir.is_dir()
    assert settings.archivio_dir.is_dir()
    assert settings.certificates_dir.is_dir()


def test_no_command_starts_the_same_session_as_assistant(monkeypatch):
    from openfatture.cli.commands import assistant

    calls = []

    async def record(ctx, message, stream, json_output, session):
        calls.append((ctx.obj["format"], message, stream, json_output, session))

    monkeypatch.setattr(assistant, "_run_assistant", record)
    for args in ([], ["assistant"]):
        result = runner.invoke(app, args)
        assert result.exit_code == 0, result.output
        assert "Usage:" not in result.stdout
    assert calls == [("rich", None, True, False, None)] * 2


def test_default_assistant_rejects_structured_output_without_a_request():
    import json

    for args in (["--format", "json"], ["--format", "json", "assistant"]):
        result = runner.invoke(app, args)
        assert result.exit_code == 2, result.output
        assert json.loads(result.stdout)["error"]["code"] == "interactive_format"


def test_help_and_version_do_not_start_the_assistant(monkeypatch):
    from openfatture.cli.commands import assistant

    def unexpected(*args, **kwargs):
        raise AssertionError("Assistant must not start for help or version")

    monkeypatch.setattr(assistant, "run_sync_with_lifespan", unexpected)
    for args in (["--help"], ["--version"], ["status", "--help"]):
        result = runner.invoke(app, args)
        assert result.exit_code == 0, result.output


def test_help_groups_commands():
    result = runner.invoke(app, ["--help"], terminal_width=120)
    assert result.exit_code == 0
    for panel in ("Assistente", "Verifiche SDI", "Configurazione e diagnostica"):
        assert panel in result.stdout
    assert "openfatture assistant" in result.stdout


def test_removed_interactive_command_is_rejected(monkeypatch):
    from openfatture.cli.commands import assistant

    def unexpected(*args, **kwargs):
        raise AssertionError("Removed command must not start the assistant")

    monkeypatch.setattr(assistant, "run_sync_with_lifespan", unexpected)
    result = runner.invoke(app, ["interactive", "start"])
    assert result.exit_code == 2
    assert "inesistente" in result.output


def test_cli_does_not_duplicate_assistant_tools():
    """Data operations the assistant can perform have no second CLI path."""
    duplicated = (
        ["cliente", "list"],
        ["fattura", "list"],
        ["fattura", "show", "1"],
        ["fattura", "create"],
        ["fattura", "generate-pdf", "1"],
        ["fattura", "set-status", "1", "bozza"],
        ["fattura", "generate-xml", "1"],
        ["pagamento", "record", "10"],
        ["pagamento", "migrate"],
    )
    for args in duplicated:
        result = runner.invoke(app, args)
        assert result.exit_code == 2, (args, result.output)
        assert "inesistente" in result.output


def _commands(group, path=()):
    import click

    for name, command in group.commands.items():
        yield (*path, name), command
        if isinstance(command, click.Group):
            yield from _commands(command, (*path, name))


def test_every_command_and_parameter_is_described(monkeypatch):
    """`--help` explains every command, argument and option, without the database."""
    import typer

    from openfatture.cli.commands import fattura

    def no_database():
        raise AssertionError("--help must not open the database")

    monkeypatch.setattr(fattura, "ensure_database", no_database)

    root = typer.main.get_command(app)
    undocumented = []
    for path, command in _commands(root):
        if not (command.help or command.short_help):
            undocumented.append(" ".join(path))
        for param in command.params:
            if param.name != "help" and not getattr(param, "help", None):
                undocumented.append(f"{' '.join(path)} {param.name}")
        result = runner.invoke(app, [*path, "--help"])
        assert result.exit_code == 0, (path, result.output)
        plain = re.sub(r"\x1b\[[0-9;]*m", "", result.output)
        text = " ".join(plain.replace("│", " ").split())
        assert "Mostra questo messaggio ed esci." in text, path
    assert undocumented == []


def test_empty_sdi_journal_says_so(runtime_db):
    result = runner.invoke(app, ["fattura", "sdi-journal"])
    assert result.exit_code == 0
    assert "Nessun invio o ricevuta SDI registrati." in result.stdout
