"""Persistence helpers for the application configuration."""

from pathlib import Path

import tomlkit

from openfatture.platform.config import Settings


def save_config(settings: Settings, path: Path) -> None:
    """Persist user-editable settings as TOML."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = settings.model_dump(mode="json", exclude_none=True)
    excluded = {
        "data_dir",
        "archivio_dir",
        "certificates_dir",
        "vector_store_path",
        "ai_chat_sessions_dir",
        "debug_config",
    }
    path.write_text(
        tomlkit.dumps({key: value for key, value in data.items() if key not in excluded}),
        encoding="utf-8",
    )
