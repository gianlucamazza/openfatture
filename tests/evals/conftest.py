"""The configured provider for the opt-in model scenarios."""

from __future__ import annotations

import os

import pytest


@pytest.fixture(scope="session")
def provider_env() -> dict[str, str]:
    """Provider, model, key and base URL from the user's real configuration.

    Session-scoped fixtures are set up before the per-test isolation of the
    user's configuration, so this is the one place that reads it; it runs only
    for the opt-in scenarios (``OPENFATTURE_EVAL=1``).
    """
    if os.environ.get("OPENFATTURE_EVAL") != "1":
        pytest.skip("calls the configured model: set OPENFATTURE_EVAL=1 to run")
    from openfatture.platform.config import Settings

    settings = Settings()
    values = {
        "AI_PROVIDER": settings.ai_provider,
        "AI_MODEL": settings.ai_model,
        "AI_API_KEY": settings.ai_api_key or "",
        "AI_BASE_URL": settings.ai_base_url or "",
    }
    return {name: value for name, value in values.items() if value}
