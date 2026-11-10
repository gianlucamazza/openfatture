"""Precedence of platform AI_* settings over AISettings defaults, field by field."""

import os
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import SecretStr

from openfatture.ai.config import settings as ai_settings
from openfatture.ai.config.settings import AISettings, hydrate_ai_settings_from_platform

# AISettings defaults to the openai provider, so it never shows in the delta.
BASE: dict[str, Any] = {
    "ai_provider": None,
    "ai_model": None,
    "ai_api_key": None,
    "ai_base_url": None,
    "ai_temperature": 0.3,
    "ai_max_tokens": 321,
    "ai_tools_enabled": False,
}
TUNING = {"temperature": 0.3, "max_tokens": 321, "tools_enabled": False}


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(os.environ):
        if key.upper().startswith("OPENFATTURE_AI_"):
            monkeypatch.delenv(key, raising=False)


def _delta(before: AISettings, after: AISettings) -> dict[str, Any]:
    def plain(value: Any) -> Any:
        return value.get_secret_value() if isinstance(value, SecretStr) else value

    old, new = before.model_dump(), after.model_dump()
    return {k: plain(v) for k, v in new.items() if plain(v) != plain(old[k])}


def _hydrate(
    monkeypatch: pytest.MonkeyPatch, ai: AISettings | None = None, **platform: Any
) -> tuple[AISettings, AISettings]:
    plat = SimpleNamespace(**{**BASE, **platform})
    monkeypatch.setattr("openfatture.platform.config.get_settings", lambda: plat)
    before = ai or AISettings()
    return before, hydrate_ai_settings_from_platform(before)


@pytest.mark.parametrize(
    ("platform", "env", "expected"),
    [
        (
            {"ai_provider": " OpenAI ", "ai_model": "gpt-x", "ai_api_key": "k"},
            {},
            {"openai_model": "gpt-x", "openai_api_key": "k"},
        ),
        (
            {"ai_provider": "anthropic", "ai_model": "c-x", "ai_api_key": "k"},
            {"OPENFATTURE_AI_ANTHROPIC_API_KEY": "env", "OPENFATTURE_AI_ANTHROPIC_MODEL": "m"},
            {"provider": "anthropic"},
        ),
        (
            {"ai_provider": "openai", "ai_api_key": "k"},
            {"OPENFATTURE_AI_OPENAI_API_KEY": "env"},
            {},
        ),
        (
            {"ai_provider": "anthropic", "ai_api_key": "k"},
            {},
            {"provider": "anthropic", "anthropic_api_key": "k"},
        ),
        (
            {
                "ai_provider": "ollama",
                "ai_model": "llama",
                "ai_api_key": "k",
                "ai_base_url": "http://h:1",
            },
            {},
            {"provider": "ollama", "ollama_model": "llama", "ollama_base_url": "http://h:1"},
        ),
        (
            {"ai_provider": "ollama", "ai_base_url": "http://h:1"},
            {"OPENFATTURE_AI_OLLAMA_BASE_URL": "http://env"},
            {"provider": "ollama"},
        ),
        ({"ai_provider": "mistral", "ai_model": "m"}, {}, {"openai_model": "m"}),
        (
            {"ai_provider": "openai", "ai_base_url": "http://h:1"},
            {"OPENFATTURE_AI_PROVIDER": "anthropic"},
            {},
        ),
    ],
)
def test_platform_fields_apply_unless_env_overrides(
    monkeypatch: pytest.MonkeyPatch,
    platform: dict[str, Any],
    env: dict[str, str],
    expected: dict[str, Any],
):
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    before, after = _hydrate(monkeypatch, **platform)
    assert _delta(before, after) == {**TUNING, **expected}


def test_unknown_current_provider_ignores_model_and_key(monkeypatch: pytest.MonkeyPatch):
    custom = AISettings().model_copy(update={"provider": "custom"})
    before, after = _hydrate(monkeypatch, custom, ai_model="m", ai_api_key="k")
    assert _delta(before, after) == TUNING


def test_nothing_to_apply_returns_same_instance(monkeypatch: pytest.MonkeyPatch):
    for name in ("TEMPERATURE", "MAX_TOKENS", "TOOLS_ENABLED"):
        monkeypatch.setenv(f"OPENFATTURE_AI_{name}", "1" if name != "TEMPERATURE" else "0.5")
    before, after = _hydrate(monkeypatch)
    assert after is before


def test_env_lookup_is_case_insensitive(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("openfatture_ai_temperature", "0.9")
    assert ai_settings._env_has("OPENFATTURE_AI_TEMPERATURE")
    assert not ai_settings._env_has("")
