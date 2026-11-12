"""Unit tests for status readiness guidance (honest next_steps)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from openfatture.cli.commands.status import _readiness
from openfatture.platform.config import Settings


def _settings(
    *,
    partita_iva: str = "12345678903",
    denominazione: str = "Acme SRL",
    data_dir: Path,
    ai_provider: str = "openai",
    ai_api_key: str = "",
) -> Settings:
    """Build a structural stand-in that exercises the shipped _readiness path."""
    return cast(
        Settings,
        SimpleNamespace(
            cedente_partita_iva=partita_iva,
            cedente_denominazione=denominazione,
            data_dir=data_dir,
            archivio_dir=data_dir / "archivio",
            cedente_codice_fiscale="RSSMRA80A01H501U",
            cedente_regime_fiscale="RF19",
            cedente_indirizzo="Via Roma 1",
            cedente_cap="00100",
            cedente_comune="Roma",
            cedente_provincia="RM",
            cedente_nazione="IT",
            pec_address="",
            pec_password="",
            ai_provider=ai_provider,
            ai_api_key=ai_api_key,
        ),
    )


def test_readiness_ai_extra_without_key_does_not_say_enable_extra(tmp_path: Path) -> None:
    """When ai extra is installed but credentials missing, guide to key/ollama only."""
    data = tmp_path / "data"
    data.mkdir()
    (data / "archivio").mkdir()
    settings = _settings(data_dir=data, ai_provider="openai", ai_api_key="")
    extras = {"ai": True, "rag": False}

    result = _readiness(settings, extras)

    assert result["core_ready"] is True
    assert result["assistant_ready"] is False
    assert result["checks"]["ai_extra"] is True
    assert result["checks"]["ai_credentials"] is False
    steps = result["next_steps"]
    assert any("AI_API_KEY" in s or "ollama" in s.lower() for s in steps)
    assert not any("enable the ai extra" in s.lower() for s in steps)
    assert not any("uv sync --extra ai" in s for s in steps)


def test_readiness_missing_ai_extra_suggests_sync(tmp_path: Path) -> None:
    data = tmp_path / "data"
    data.mkdir()
    (data / "archivio").mkdir()
    settings = _settings(data_dir=data)
    extras = {"ai": False, "rag": False}

    result = _readiness(settings, extras)

    assert result["core_ready"] is True
    assert result["assistant_ready"] is False
    assert any("uv sync --extra ai" in s for s in result["next_steps"])
    assert any("installa l'extra ai" in s for s in result["next_steps"])


def test_readiness_full_ready_suggests_assistant(tmp_path: Path) -> None:
    data = tmp_path / "data"
    data.mkdir()
    (data / "archivio").mkdir()
    settings = _settings(data_dir=data, ai_provider="openai", ai_api_key="sk-test")
    extras = {"ai": True}

    result = _readiness(settings, extras)

    assert result["core_ready"] is True
    assert result["assistant_ready"] is True
    assert any('openfatture -m "' in s for s in result["next_steps"])


def test_partial_fiscal_profile_explains_not_ready(tmp_path):
    settings = _settings(data_dir=tmp_path, ai_api_key="synthetic")
    settings.cedente_codice_fiscale = ""
    settings.cedente_regime_fiscale = ""
    result = _readiness(settings, {"ai": True})
    assert not result["core_ready"]
    assert not result["checks"]["fiscal_profile"]
    assert result["missing_fields"] == ["cedente_codice_fiscale", "cedente_regime_fiscale"]
    assert any("cedente_codice_fiscale" in step for step in result["next_steps"])
    assert result["assistant_authenticated"] is None


def test_invalid_fiscal_identifiers_block_core(tmp_path: Path) -> None:
    (tmp_path / "archivio").mkdir()
    settings = _settings(data_dir=tmp_path, partita_iva="12345678901")
    settings.cedente_codice_fiscale = "NOT-A-CODE"
    settings.cedente_regime_fiscale = "RF99"
    result = _readiness(settings, {"ai": False})
    assert result["core_ready"] is False
    assert result["missing_fields"] == []
    assert result["invalid_fields"] == [
        "cedente_partita_iva",
        "cedente_codice_fiscale",
        "cedente_regime_fiscale",
    ]
    assert result["checks"]["fiscal_profile"] is False
    assert result["next_steps"] == [
        "Esegui: openfatture init",
        "openfatture config set cedente_partita_iva '<valore>'",
        "openfatture config set cedente_codice_fiscale '<valore>'",
        "openfatture config set cedente_regime_fiscale '<valore>'",
        "Per l'assistente: uv sync --extra ai",
    ]


def test_partita_iva_is_accepted_as_fiscal_code(tmp_path: Path) -> None:
    (tmp_path / "archivio").mkdir()
    settings = _settings(data_dir=tmp_path, ai_provider="Ollama")
    settings.cedente_codice_fiscale = "12345678903"
    settings.pec_address = "pec@example.it"
    settings.pec_password = "secret"
    result = _readiness(settings, {"ai": True})
    assert result["invalid_fields"] == []
    assert result["core_ready"] is True
    assert result["delivery_configured"] is True
    assert result["assistant_ready"] is True
    assert result["checks"]["ai_credentials"] is True
    assert result["next_steps"] == ['Prova: openfatture -m "Elenca le fatture aperte"']


def test_missing_company_and_directories(tmp_path: Path) -> None:
    settings = _settings(data_dir=tmp_path / "absent", partita_iva="", denominazione=" ")
    result = _readiness(settings, {})
    assert result["checks"]["company_profile"] is False
    assert result["checks"]["data_dir"] is False
    assert result["checks"]["archive_dir"] is False
    assert result["core_ready"] is result["invoice_ready"] is False
    assert result["delivery_configured"] is False
    assert result["invalid_fields"] == []
    assert result["next_steps"] == [
        "Esegui: openfatture init",
        "Per l'assistente: uv sync --extra ai",
    ]


def test_core_not_ready_with_ai_extra_but_no_key(tmp_path: Path) -> None:
    settings = _settings(data_dir=tmp_path / "absent")
    result = _readiness(settings, {"ai": True})
    assert result["next_steps"] == [
        "Esegui: openfatture init",
        "openfatture config set ai_api_key '<chiave>' (oppure ai_provider ollama)",
    ]


def test_status_text_exposes_blocking_fields(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    from openfatture.cli.commands import status

    settings = _settings(data_dir=tmp_path, ai_api_key="synthetic")
    settings.cedente_codice_fiscale = ""
    settings.cedente_regime_fiscale = ""
    settings.locale = "it"
    data: dict[str, Any] = {
        "readiness": _readiness(settings, {"ai": True}),
        "extras": {"ai": True},
        "configuration": {"config_file": str(tmp_path / "config.toml"), "secret_backend": "file"},
        "extensions": {
            "hooks_dir": str(tmp_path),
            "hooks_scripts": [],
            "in_process_plugins": "unsupported",
        },
    }
    for key in (
        "version",
        "database",
        "data_dir",
        "archive_dir",
        "ai_provider",
        "ai_model",
        "ai_api_key_configured",
        "assistant_backend",
        "assistant_backend_id",
    ):
        data[key] = "test"
    from openfatture.platform.config import Settings as RealSettings
    from openfatture.platform.data_flows import data_destinations

    data["data_destinations"] = data_destinations(RealSettings(ai_provider="ollama"))
    monkeypatch.setattr(status, "_build_status", lambda: data)
    monkeypatch.setattr(status, "get_settings", lambda: settings)
    result = CliRunner().invoke(status.app, [], terminal_width=120)
    assert result.exit_code == 0
    assert "cedente_codice_fiscale" in result.stdout
    assert "cedente_regime_fiscale" in result.stdout
    assert "Da completare" in result.stdout
    assert "openfatture --help" not in result.stdout


def test_status_reports_configuration_sources(tmp_path, monkeypatch):
    import json

    from typer.testing import CliRunner

    from openfatture.cli.main import app

    config_dir = tmp_path / "profile"
    config_dir.mkdir()
    (config_dir / "config.toml").write_text('ai_api_key = "plaintext"\n')
    monkeypatch.setenv("OPENFATTURE_CONFIG_DIR", str(config_dir))
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("AI_PROVIDER=ollama\n")

    result = CliRunner().invoke(app, ["status", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    configuration = payload["configuration"]
    assert configuration["config_file"] == str(config_dir / "config.toml")
    assert configuration["secret_backend"] == "file"
    assert configuration["plaintext_secrets"] == ["ai_api_key"]
    assert configuration["ignored_dotenv"] is True
    assert payload["database_schema"] in {"empty", "current", "unversioned"}
    steps = " ".join(payload["readiness"]["next_steps"])
    assert "openfatture config migrate" in steps
    assert "--env-file .env" in steps
