"""Settings never create files in the current working directory."""

import pytest


def test_ai_and_rag_settings_do_not_touch_cwd(tmp_path, monkeypatch):
    pytest.importorskip("openai")
    monkeypatch.chdir(tmp_path)

    from openfatture.ai.config.settings import AISettings
    from openfatture.ai.rag.auto_update.config import AutoUpdateConfig
    from openfatture.ai.rag.config import RAGConfig
    from openfatture.platform.config import Settings

    Settings()
    AISettings()
    RAGConfig()
    AutoUpdateConfig()

    assert list(tmp_path.iterdir()) == []
