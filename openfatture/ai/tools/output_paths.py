"""Confine model-chosen output paths to the exports directory."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any

from openfatture.platform.config import get_settings
from openfatture.platform.errors import describe_error


def exports_dir() -> Path:
    return get_settings().exports_dir


def confine_output_path(output_path: str) -> str:
    """Resolve ``output_path`` inside the exports directory or raise ``ValueError``.

    Relative paths are placed under the exports directory; absolute paths and
    ``..`` segments must still resolve inside it.
    """
    base = exports_dir().resolve()
    candidate = Path(output_path)
    resolved = (candidate if candidate.is_absolute() else base / candidate).resolve()
    if not resolved.is_relative_to(base):
        raise ValueError(f"Output path must be inside {base}: {output_path}")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return str(resolved)


def confined_output(func: Callable[..., dict[str, Any]]) -> Callable[..., dict[str, Any]]:
    """Wrap a tool function so a model-supplied ``output_path`` is confined.

    Without ``output_path`` the application default file name is kept.
    """

    @wraps(func)
    def wrapper(*args: Any, output_path: str | None = None, **kwargs: Any) -> dict[str, Any]:
        if output_path is None:
            return func(*args, **kwargs)
        try:
            safe = confine_output_path(output_path)
        except ValueError as exc:
            return {"error": describe_error(exc)}
        return func(*args, output_path=safe, **kwargs)

    return wrapper
