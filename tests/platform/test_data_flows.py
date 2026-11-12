"""What `status` reports as leaving the computer."""

from __future__ import annotations

import pytest

from openfatture.platform.config import Settings
from openfatture.platform.data_flows import data_destinations, embedding_provider


def test_defaults_name_the_provider_and_hide_sdi(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENFATTURE_RAG_EMBEDDING_PROVIDER", raising=False)
    flows = data_destinations(Settings(ai_provider="openai"))
    assert flows["model"] | {"carries": None} == {
        "provider": "openai",
        "host": "api.openai.com",
        "local": False,
        "carries": None,
    }
    assert flows["embeddings"]["provider"] == "openai"
    assert flows["lookups"]["enabled"] is True
    assert flows["sdi"] == flows["sdi"] | {"enabled": False, "host": None}


def test_ollama_and_offline_keep_everything_local(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENFATTURE_RAG_EMBEDDING_PROVIDER", raising=False)
    settings = Settings(ai_provider="ollama", ai_offline=True)
    flows = data_destinations(settings)
    assert flows["model"]["local"] is True
    assert flows["embeddings"]["local"] is True
    assert flows["lookups"]["enabled"] is False


def test_a_custom_base_url_is_the_model_host() -> None:
    flows = data_destinations(Settings(ai_provider="openai", ai_base_url="https://llm.example/v1"))
    assert flows["model"]["host"] == "llm.example"
    local = data_destinations(Settings(ai_provider="openai", ai_base_url="http://127.0.0.1:8080"))
    assert local["model"]["local"] is True


def test_sdi_flow_appears_only_when_sending_is_enabled() -> None:
    flows = data_destinations(
        Settings(ai_enabled_tools="send_invoice_to_sdi", pec_smtp_server="smtps.pec.example")
    )
    assert flows["sdi"]["enabled"] is True
    assert flows["sdi"]["host"] == "smtps.pec.example"


def test_embeddings_follow_the_configured_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ollama set in config.toml (not only in the environment) means local embeddings."""
    monkeypatch.delenv("OPENFATTURE_RAG_EMBEDDING_PROVIDER", raising=False)
    assert embedding_provider(Settings(ai_provider="ollama")) == "sentence-transformers"
    monkeypatch.setenv("OPENFATTURE_RAG_EMBEDDING_PROVIDER", "openai")
    assert embedding_provider(Settings(ai_provider="ollama")) == "openai"
