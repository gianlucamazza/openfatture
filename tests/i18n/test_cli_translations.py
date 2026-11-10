"""Every message id referenced by the code exists in every locale."""

import ast
import re
from pathlib import Path

import pytest

from openfatture.i18n import _
from openfatture.i18n.loader import SUPPORTED_LOCALES, get_bundle

ROOT = Path(__file__).resolve().parents[2] / "openfatture"
LOCALES = Path(ROOT / "i18n" / "locales")
KEY = re.compile(r"^([a-z][a-z0-9-]*)\s*=", re.M)


def _defined(locale: str) -> set[str]:
    return set(KEY.findall((LOCALES / locale / "cli.ftl").read_text(encoding="utf-8")))


def _referenced() -> set[str]:
    known = set().union(*(_defined(locale) for locale in SUPPORTED_LOCALES))
    literals: set[str] = set()
    for path in ROOT.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                literals.add(node.value)
    referenced = known & literals
    # Keys built at runtime from a constant prefix ("cli-invoice-" + status).
    referenced |= {key for key in known if key.startswith("cli-invoice-")}
    return referenced


@pytest.mark.parametrize("locale", sorted(SUPPORTED_LOCALES))
def test_every_referenced_message_exists(locale):
    missing = sorted(_referenced() - _defined(locale))
    assert not missing, f"{locale} is missing: {missing}"


@pytest.mark.parametrize("locale", sorted(SUPPORTED_LOCALES))
def test_no_orphan_messages(locale):
    orphans = sorted(_defined(locale) - _referenced())
    assert not orphans, f"{locale} defines unused messages: {orphans}"


@pytest.mark.parametrize(
    "locale, expected",
    [("it", "Sessione: abc"), ("en", "Session: abc"), ("de", "Sitzung: abc")],
)
def test_variable_interpolation(locale, expected):
    assert _("assistant-session", locale=locale, session="abc") == expected


def test_bundles_load_for_every_locale():
    for locale in SUPPORTED_LOCALES:
        assert get_bundle(locale).has_message("assistant-help")
