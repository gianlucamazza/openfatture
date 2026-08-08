"""Optional feature extras detection and install hints.

Feature stacks live behind PEP 621 extras declared in ``pyproject.toml``:

- ``ai`` — LLM providers, agents, tools, LangGraph workflows
- ``rag`` — ChromaDB + embeddings (includes ``ai``)
- ``ml`` — Prophet / XGBoost forecasting stack (optional; not on default path)
- ``all`` — union of the above

Core install (no extras) supports billing, SDI, payment, PDF, config, and status.
Voice, regulatory scraping, and experimental Lightning Network support were
removed from the product surface.
"""

from __future__ import annotations

from importlib import import_module
from typing import Final

# Extra name -> importable marker module that is only present when the extra
# (or an equivalent manual install) is available.
_EXTRA_MARKERS: Final[dict[str, str]] = {
    "ai": "openai",
    "rag": "chromadb",
    "ml": "prophet",
}

_INSTALL_HINT: Final[str] = (
    "Install with: uv sync --extra {extra}   # or: pip install 'openfatture[{extra}]'"
)


class MissingExtraError(ImportError):
    """Raised when code requires an optional extra that is not installed."""

    def __init__(
        self, extra: str, *, feature: str | None = None, cause: BaseException | None = None
    ):
        self.extra = extra
        self.feature = feature
        what = feature or f"the '{extra}' feature"
        message = (
            f"{what} requires the optional '{extra}' extra. {_INSTALL_HINT.format(extra=extra)}"
        )
        super().__init__(message)
        if cause is not None:
            self.__cause__ = cause


def has_extra(extra: str) -> bool:
    """Return True if the marker package for *extra* can be imported."""
    marker = _EXTRA_MARKERS.get(extra)
    if marker is None:
        raise ValueError(f"Unknown extra: {extra!r}. Known: {sorted(_EXTRA_MARKERS)}")
    try:
        import_module(marker)
    except ImportError:
        return False
    return True


def available_extras() -> dict[str, bool]:
    """Map every known optional extra to its availability."""
    return {name: has_extra(name) for name in _EXTRA_MARKERS}


def require_extra(extra: str, *, feature: str | None = None) -> None:
    """Raise :class:`MissingExtraError` if *extra* is not installed."""
    if not has_extra(extra):
        raise MissingExtraError(extra, feature=feature)


def install_hint(extra: str) -> str:
    """Return a short install command for *extra*."""
    return _INSTALL_HINT.format(extra=extra)
