"""Persistence helpers for the user configuration and its secrets."""

from __future__ import annotations

from typing import Any

import tomlkit
from pydantic import BaseModel, TypeAdapter, ValidationError

from openfatture.platform.config import Settings
from openfatture.platform.secrets import (
    SECRET_FIELDS,
    SecretStore,
    config_file_path,
    write_private_text,
)


def resolve_setting(key: str) -> tuple[list[str], Any]:
    """Resolve ``key`` (``a`` or ``a.b``) to its path and type annotation."""
    parts = key.split(".")
    model: type[BaseModel] = Settings
    for index, part in enumerate(parts):
        info = model.model_fields.get(part)
        if info is None:
            raise KeyError(key)
        annotation = info.annotation
        if index == len(parts) - 1:
            return parts, annotation
        if not (isinstance(annotation, type) and issubclass(annotation, BaseModel)):
            raise KeyError(key)
        model = annotation
    raise KeyError(key)


def coerce_setting(key: str, raw: str) -> Any:
    """Validate ``raw`` against the type of ``key``; return a TOML-ready value.

    Raises ``KeyError`` for unknown keys and ``ValueError`` for invalid values.
    """
    _parts, annotation = resolve_setting(key)
    adapter: TypeAdapter[Any] = TypeAdapter(annotation)
    try:
        value = adapter.validate_python(raw)
    except ValidationError as exc:
        raise ValueError(exc.errors()[0]["msg"]) from exc
    return adapter.dump_python(value, mode="json")


def env_override(key: str) -> str | None:
    """Name of the environment variable that overrides top-level ``key``, if set."""
    import os

    top = key.split(".")[0]
    for name in os.environ:
        if name.lower() == top:
            return name
    return None


def update_config(changes: dict[str, Any], *, remove: tuple[str, ...] = ()) -> None:
    """Change only the given keys of ``config.toml``, preserving everything else.

    Keys may be dotted (``debug_config.enable_debug_logging``) and are stored as
    TOML tables. The file is replaced atomically with owner-only permissions.
    """
    path = config_file_path()
    document = (
        tomlkit.parse(path.read_text(encoding="utf-8")) if path.exists() else tomlkit.document()
    )
    for key, value in changes.items():
        *tables, leaf = key.split(".")
        target: Any = document
        for table in tables:
            if table not in target:
                target[table] = tomlkit.table()
            target = target[table]
        target[leaf] = value
    for key in remove:
        *tables, leaf = key.split(".")
        target = document
        for table in tables:
            target = target.get(table) if hasattr(target, "get") else None
            if target is None:
                break
        if target is not None and leaf in target:
            del target[leaf]
    write_private_text(path, tomlkit.dumps(document))


def is_secret(key: str) -> bool:
    return key in SECRET_FIELDS


def store_secret(key: str, value: str) -> str:
    """Save a secret and return the backend name used."""
    store = SecretStore()
    store.set(key, value)
    return store.backend
