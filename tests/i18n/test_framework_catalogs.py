"""Click and Typer messages: complete, compiled and switched with the locale."""

from __future__ import annotations

import gettext
import io
import os
import re
from pathlib import Path

import click
import pytest
import typer
from babel.messages.extract import extract_from_dir
from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po

from openfatture.cli import framework_i18n

CATALOGS = framework_i18n.CATALOGS
LOCALES = sorted(path.name for path in CATALOGS.iterdir() if path.is_dir())
PLACEHOLDER = re.compile(r"\{[^}]*\}|%\([a-z]+\)s")


def _catalog(locale: str):
    path = CATALOGS / locale / "LC_MESSAGES" / f"{framework_i18n.DOMAIN}.po"
    with path.open("rb") as source:
        return read_po(source)


def _framework_messages() -> set[str | tuple[str, ...]]:
    messages: set[str | tuple[str, ...]] = set()
    for package in (click, typer):
        assert package.__file__ is not None
        root = Path(package.__file__).parent
        for _file, _line, message, _comments, _context in extract_from_dir(
            str(root), method_map=[("**.py", "python")]
        ):
            messages.add(message if isinstance(message, str) else tuple(message))
    return messages


def test_catalogs_cover_italian_and_the_other_supported_locales():
    assert LOCALES == ["de", "es", "fr", "it"]


def _messages(translations: gettext.GNUTranslations) -> dict[object, str]:
    return {key: value for key, value in translations._catalog.items() if key != ""}  # type: ignore[attr-defined]


@pytest.mark.parametrize("locale", LOCALES)
def test_compiled_catalog_matches_its_source(locale):
    compiled = io.BytesIO()
    write_mo(compiled, _catalog(locale))
    compiled.seek(0)
    mo = CATALOGS / locale / "LC_MESSAGES" / f"{framework_i18n.DOMAIN}.mo"
    with mo.open("rb") as committed:
        assert _messages(gettext.GNUTranslations(committed)) == _messages(
            gettext.GNUTranslations(compiled)
        ), "Stale .mo: run `uv run python scripts/compile_cli_catalogs.py`"


@pytest.mark.parametrize("locale", LOCALES)
def test_every_click_and_typer_message_is_translated(locale):
    catalog = _catalog(locale)
    missing = []
    for message in _framework_messages():
        key = message[0] if isinstance(message, tuple) else message
        entry = catalog.get(key)
        if entry is None or not entry.string or not all(entry.string):
            missing.append(message)
    assert not missing, f"{locale} lacks translations (Click/Typer upgrade?): {missing}"


@pytest.mark.parametrize("locale", LOCALES)
def test_translations_keep_their_placeholders(locale):
    for entry in _catalog(locale):
        if not entry.id:
            continue
        sources = entry.id if isinstance(entry.id, tuple) else (entry.id,)
        targets = entry.string if isinstance(entry.string, tuple) else (entry.string,)
        expected = set().union(*(PLACEHOLDER.findall(text) for text in sources))
        for target in targets:
            assert set(PLACEHOLDER.findall(target)) <= expected, (locale, entry.id, target)


@pytest.fixture
def restore_gettext(monkeypatch):
    from typer import rich_utils

    monkeypatch.setenv("LANGUAGE", os.environ.get("LANGUAGE", ""))
    previous_domain = gettext.textdomain()
    labels = {name: getattr(rich_utils, name) for name in framework_i18n._TYPER_LABELS}
    yield
    gettext.textdomain(previous_domain)
    for name, value in labels.items():
        setattr(rich_utils, name, value)


@pytest.mark.parametrize(
    "locale, options, error",
    [("it", "Opzioni", "Errore: {message}"), ("en", "Options", "Error: {message}")],
)
def test_install_switches_framework_language(restore_gettext, locale, options, error):
    from typer import rich_utils

    framework_i18n.install(locale)

    assert rich_utils.OPTIONS_PANEL_TITLE == options
    assert gettext.gettext("Error: {message}") == error
