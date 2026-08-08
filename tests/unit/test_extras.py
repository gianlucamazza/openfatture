"""Tests for optional extras helpers."""

import pytest

from openfatture.platform.extras import (
    MissingExtraError,
    available_extras,
    has_extra,
    install_hint,
    require_extra,
)


def test_available_extras_keys() -> None:
    extras = available_extras()
    assert set(extras) == {"ai", "rag", "ml"}
    assert all(isinstance(v, bool) for v in extras.values())


def test_install_hint() -> None:
    assert "--extra ai" in install_hint("ai")
    assert "openfatture[ai]" in install_hint("ai") or "uv sync" in install_hint("ai")


def test_unknown_extra_raises() -> None:
    with pytest.raises(ValueError, match="Unknown extra"):
        has_extra("not-a-real-extra")


def test_require_extra_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "openfatture.platform.extras.has_extra",
        lambda extra: False,
    )
    with pytest.raises(MissingExtraError, match="optional 'ai' extra"):
        require_extra("ai", feature="the assistant")
