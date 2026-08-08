"""Single-source-of-truth contracts for version, backends, and AI credentials."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from openfatture import __version__ as pkg_version
from openfatture.platform.assistant_backends import (
    ASSISTANT_BACKEND_CHAT,
    ASSISTANT_BACKEND_LANGGRAPH,
    BACKEND_CHAT,
    BACKEND_LANGGRAPH,
    DEFAULT_ASSISTANT_BACKEND,
    resolve_backend_id,
)
from openfatture.platform.extras import available_extras


def test_package_version_settings_ssot() -> None:
    from openfatture.platform.config import Settings

    assert Settings().app_version == pkg_version


def test_lightning_version_reexports_package() -> None:
    from openfatture.lightning import __version__ as ln_version

    assert ln_version == pkg_version


@pytest.mark.skipif(not available_extras().get("ai"), reason="ai extra not installed")
def test_ai_subpackage_versions_reexport_package() -> None:
    from openfatture.ai import __version__ as ai_version
    from openfatture.ai.orchestration import __version__ as orch_version
    from openfatture.ai.streaming import __version__ as stream_version

    assert ai_version == pkg_version
    assert orch_version == pkg_version
    assert stream_version == pkg_version


def test_assistant_backend_default_and_ids() -> None:
    from openfatture.platform.config import Settings

    assert DEFAULT_ASSISTANT_BACKEND == ASSISTANT_BACKEND_LANGGRAPH
    assert Settings().assistant_backend == DEFAULT_ASSISTANT_BACKEND
    assert resolve_backend_id("chat") == BACKEND_CHAT
    assert resolve_backend_id("langgraph") == BACKEND_LANGGRAPH
    assert resolve_backend_id(ASSISTANT_BACKEND_CHAT) == BACKEND_CHAT


def test_status_backend_ids_match_ssot() -> None:
    from openfatture.cli.commands.status import _build_status

    data = _build_status()
    assert data["assistant_backend"] == DEFAULT_ASSISTANT_BACKEND
    assert data["assistant_backend_id"] == resolve_backend_id(DEFAULT_ASSISTANT_BACKEND)
    assert data["version"] == pkg_version


@pytest.mark.skipif(not available_extras().get("ai"), reason="ai extra not installed")
def test_ai_settings_hydrate_from_platform_ai_star(monkeypatch: pytest.MonkeyPatch) -> None:
    """init/docs write AI_*; factory must see them via get_ai_settings()."""
    from openfatture.ai.config.settings import (
        AISettings,
        hydrate_ai_settings_from_platform,
        reset_ai_settings,
    )
    from openfatture.platform.config import Settings

    for key in list(os.environ):
        if key.upper().startswith("OPENFATTURE_AI_"):
            monkeypatch.delenv(key, raising=False)

    plat = Settings(
        ai_provider="anthropic",
        ai_model="claude-test",
        ai_api_key="sk-ant-test",
        ai_temperature=0.2,
        ai_max_tokens=123,
    )
    with patch("openfatture.platform.config.get_settings", return_value=plat):
        reset_ai_settings()
        hydrated = hydrate_ai_settings_from_platform(AISettings())

    assert hydrated.provider == "anthropic"
    assert hydrated.anthropic_model == "claude-test"
    assert hydrated.get_api_key_for_provider() == "sk-ant-test"
    assert hydrated.temperature == 0.2
    assert hydrated.max_tokens == 123


@pytest.mark.skipif(not available_extras().get("ai"), reason="ai extra not installed")
def test_openfatture_ai_env_wins_over_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    from openfatture.ai.config.settings import AISettings, hydrate_ai_settings_from_platform
    from openfatture.platform.config import Settings

    monkeypatch.setenv("OPENFATTURE_AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENFATTURE_AI_OPENAI_API_KEY", "sk-openai-advanced")
    monkeypatch.setenv("OPENFATTURE_AI_OPENAI_MODEL", "gpt-advanced")

    plat = Settings(
        ai_provider="anthropic",
        ai_model="claude-test",
        ai_api_key="sk-ant-test",
    )
    with patch("openfatture.platform.config.get_settings", return_value=plat):
        ai = AISettings()
        hydrated = hydrate_ai_settings_from_platform(ai)

    assert hydrated.provider == "openai"
    assert hydrated.openai_model == "gpt-advanced"
    assert hydrated.get_api_key_for_provider() == "sk-openai-advanced"
