"""Starting the assistant with a missing setup: init in a terminal, a clear refusal elsewhere."""

from __future__ import annotations

import io
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
import typer
from rich.console import Console

from openfatture.cli.commands import assistant, init
from openfatture.platform.config import Settings


def _settings(tmp_path: Path, **values: Any) -> Settings:
    base: dict[str, Any] = {
        "cedente_partita_iva": "12345678903",
        "cedente_denominazione": "Acme SRL",
        "database_url": f"sqlite:///{tmp_path / 'app.db'}",
        "archivio_dir": tmp_path / "archivio",
        "ai_provider": "openai",
        "ai_api_key": "",
    }
    base.update(values)
    return cast(Settings, SimpleNamespace(**base))


def _ready_database(settings: Settings) -> None:
    from openfatture.storage.schema import upgrade_database

    upgrade_database(str(settings.database_url))
    settings.archivio_dir.mkdir()


def test_gap_reports_the_first_missing_piece(tmp_path: Path) -> None:
    assert init.setup_gap(_settings(tmp_path, cedente_denominazione=" ")) == "profile"
    settings = _settings(tmp_path)
    assert init.setup_gap(settings) == "database"
    assert not (tmp_path / "app.db").exists()  # the check never creates the database
    _ready_database(settings)
    assert init.setup_gap(settings) == "ai_key"
    settings.ai_api_key = "sk-test"
    assert init.setup_gap(settings) is None
    assert init.setup_gap(_settings(tmp_path, ai_provider="Ollama")) is None


@pytest.fixture
def output(monkeypatch: pytest.MonkeyPatch) -> io.StringIO:
    buffer = io.StringIO()
    monkeypatch.setattr(assistant, "console", Console(file=buffer, width=200))
    return buffer


def _terminal(monkeypatch: pytest.MonkeyPatch, buffer: io.StringIO) -> None:
    monkeypatch.setattr(
        assistant,
        "console",
        Console(file=buffer, width=200, force_terminal=True, color_system=None),
    )
    monkeypatch.setattr("sys.stdin", SimpleNamespace(isatty=lambda: True))


def _gaps(monkeypatch: pytest.MonkeyPatch, *gaps: str | None) -> list[tuple[str, bool]]:
    remaining = list(gaps)
    runs: list[tuple[str, bool]] = []
    settings = SimpleNamespace(ai_provider="anthropic")
    monkeypatch.setattr(assistant, "get_settings", lambda: settings)
    monkeypatch.setattr("openfatture.platform.config.reload_settings", lambda: settings)
    monkeypatch.setattr(init, "setup_gap", lambda _settings: remaining.pop(0))
    monkeypatch.setattr(
        init, "run_setup", lambda _settings, *, wizard: runs.append(("setup", wizard))
    )
    return runs


@pytest.mark.parametrize(("gap", "wizard"), [("profile", True), ("database", False)])
def test_terminal_runs_init_then_starts(
    monkeypatch: pytest.MonkeyPatch, output: io.StringIO, gap: str, wizard: bool
) -> None:
    _terminal(monkeypatch, output)
    runs = _gaps(monkeypatch, gap, None)
    assistant._ensure_setup("rich")
    assert runs == [("setup", wizard)]
    assert "Configurazione mancante: avvio openfatture init." in output.getvalue()


def test_terminal_still_refuses_when_init_left_a_gap(
    monkeypatch: pytest.MonkeyPatch, output: io.StringIO
) -> None:
    _terminal(monkeypatch, output)
    _gaps(monkeypatch, "profile", "profile")
    with pytest.raises(typer.Exit) as exc:
        assistant._ensure_setup("rich")
    assert exc.value.exit_code == assistant.SETUP_REQUIRED_EXIT
    assert "esegui `openfatture init`" in output.getvalue()


def test_missing_key_is_explained_without_running_init(
    monkeypatch: pytest.MonkeyPatch, output: io.StringIO
) -> None:
    _terminal(monkeypatch, output)
    runs = _gaps(monkeypatch, "ai_key")
    with pytest.raises(typer.Exit) as exc:
        assistant._ensure_setup("rich")
    assert exc.value.exit_code == assistant.SETUP_REQUIRED_EXIT
    assert runs == []
    assert "Nessuna chiave API per anthropic" in output.getvalue()


def test_without_terminal_nothing_is_created(
    monkeypatch: pytest.MonkeyPatch, output: io.StringIO
) -> None:
    runs = _gaps(monkeypatch, "database")
    with pytest.raises(typer.Exit) as exc:
        assistant._ensure_setup("rich")
    assert exc.value.exit_code == assistant.SETUP_REQUIRED_EXIT
    assert runs == []
    assert "Configurazione mancante: esegui `openfatture init`." in output.getvalue()


@pytest.mark.parametrize(
    ("gap", "code"),
    [
        ("profile", "setup_required"),
        ("newer_database", "newer_database"),
        ("ai_key", "ai_key_missing"),
    ],
)
def test_structured_refusal_has_a_code(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], gap: str, code: str
) -> None:
    _gaps(monkeypatch, gap)
    with pytest.raises(typer.Exit) as exc:
        assistant._ensure_setup("json")
    assert exc.value.exit_code == assistant.SETUP_REQUIRED_EXIT
    payload = json.loads(capsys.readouterr().out)
    assert payload["success"] is False
    assert payload["error"]["code"] == code
