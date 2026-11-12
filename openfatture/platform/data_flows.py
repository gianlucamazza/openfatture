"""Where data goes when it leaves the computer (read-only, no AI imports).

Shared by `openfatture status` and the components that open those flows, so
the report and the behaviour cannot disagree.
"""

from __future__ import annotations

import os
from typing import Any, Literal
from urllib.parse import urlparse

from openfatture.platform.config import Settings, parse_enabled_tools

EmbeddingProvider = Literal["openai", "sentence-transformers"]

_PROVIDER_HOSTS = {
    "openai": "api.openai.com",
    "anthropic": "api.anthropic.com",
    "ollama": "localhost:11434",
}
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
VIES_HOST = "ec.europa.eu"
SDI_SEND_TOOL = "send_invoice_to_sdi"


def embedding_provider(settings: Settings) -> EmbeddingProvider:
    """``OPENFATTURE_RAG_EMBEDDING_PROVIDER``, else local with Ollama, else OpenAI."""
    explicit = os.getenv("OPENFATTURE_RAG_EMBEDDING_PROVIDER")
    if explicit == "openai":
        return "openai"
    if explicit == "sentence-transformers":
        return "sentence-transformers"
    provider = (settings.ai_provider or "").strip().lower()
    return "sentence-transformers" if provider == "ollama" else "openai"


def model_host(settings: Settings) -> str:
    """Host that receives every assistant request (prompt, history, tool results)."""
    if settings.ai_base_url:
        parsed = urlparse(settings.ai_base_url)
        return parsed.netloc or settings.ai_base_url
    provider = (settings.ai_provider or "").strip().lower()
    return _PROVIDER_HOSTS.get(provider, provider or "unknown")


def is_local_host(host: str) -> bool:
    name = host.rsplit(":", 1)[0] if host.count(":") == 1 else host
    return name.strip("[]") in _LOCAL_HOSTS


def data_destinations(settings: Settings) -> dict[str, Any]:
    """Every flow that can carry data off the computer, and whether it is on."""
    host = model_host(settings)
    embeddings = embedding_provider(settings)
    sdi_enabled = SDI_SEND_TOOL in parse_enabled_tools(settings.ai_enabled_tools)
    return {
        "model": {
            "provider": settings.ai_provider,
            "host": host,
            "local": is_local_host(host),
            "carries": "assistant requests: prompt, conversation, saved notes, tool results",
        },
        "embeddings": {
            "provider": embeddings,
            "host": None if embeddings == "sentence-transformers" else "api.openai.com",
            "local": embeddings == "sentence-transformers",
            "carries": "bundled knowledge-base texts, when search_knowledge_base indexes them",
        },
        "lookups": {
            "enabled": not settings.ai_offline,
            "host": VIES_HOST,
            "carries": "the VAT number checked and the issuer's partita IVA (VIES)",
        },
        "sdi": {
            "enabled": sdi_enabled,
            "host": settings.pec_smtp_server if sdi_enabled else None,
            "carries": "the FatturaPA XML of an invoice sent to SDI by PEC, after confirmation",
        },
    }
