"""Boundaries between core, feature extras, and extensions."""

from __future__ import annotations

import importlib
import json

import pytest
from typer.testing import CliRunner

from openfatture.cli.main import app
from openfatture.platform.extras import available_extras

runner = CliRunner()


def test_core_packages_import_without_optional_ai_stack() -> None:
    """Core product modules must import without requiring plugin APIs."""
    for name in (
        "openfatture.billing",
        "openfatture.sdi",
        "openfatture.payment",
        "openfatture.pdf",
        "openfatture.storage",
        "openfatture.events",
        "openfatture.hooks",
        "openfatture.platform",
        "openfatture.cli.main",
    ):
        importlib.import_module(name)


def test_plugins_package_is_not_part_of_product() -> None:
    """In-process plugins were removed; the extension path is hooks."""
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("openfatture.plugins")


def test_extras_markers_match_feature_modules_only() -> None:
    extras = available_extras()
    assert set(extras) == {"ai", "rag", "ml"}
    assert "scraper" not in extras
    assert "voice" not in extras
    assert "plugin" not in extras


def test_status_json_reports_hooks_and_unsupported_plugins() -> None:
    result = runner.invoke(app, ["status", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "extras" in payload
    assert "extensions" in payload
    assert payload["extensions"]["in_process_plugins"] == "unsupported"
    assert "hooks_dir" in payload["extensions"]
    assert payload["feature_flags"]["assistant_available"] is bool(payload["extras"].get("ai"))
