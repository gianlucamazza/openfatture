"""Unit tests for status readiness guidance (honest next_steps)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

from openfatture.cli.commands.status import _readiness
from openfatture.platform.config import Settings


def _settings(
    *,
    partita_iva: str = "12345678901",
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
    extras = {"ai": True, "rag": False, "ml": False}

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
    extras = {"ai": False, "rag": False, "ml": False}

    result = _readiness(settings, extras)

    assert result["core_ready"] is True
    assert result["assistant_ready"] is False
    assert any("uv sync --extra ai" in s for s in result["next_steps"])
    assert any("enable the ai extra" in s.lower() for s in result["next_steps"])


def test_readiness_full_ready_suggests_assistant(tmp_path: Path) -> None:
    data = tmp_path / "data"
    data.mkdir()
    (data / "archivio").mkdir()
    settings = _settings(data_dir=data, ai_provider="openai", ai_api_key="sk-test")
    extras = {"ai": True}

    result = _readiness(settings, extras)

    assert result["core_ready"] is True
    assert result["assistant_ready"] is True
    assert any("openfatture assistant" in s for s in result["next_steps"])
