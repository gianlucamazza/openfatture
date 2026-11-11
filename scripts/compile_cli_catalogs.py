"""Compile the gettext catalogs that translate Click and Typer messages.

Click and Typer translate their own text (panel titles, ``--help``, usage
errors) through the standard ``gettext`` module. The sources are the ``.po``
files in ``openfatture/i18n/gettext``; this script writes the ``.mo`` files
next to them. ``tests/i18n/test_framework_catalogs.py`` fails when a ``.mo``
is stale or when an installed Click/Typer release adds an untranslated message.

    uv run python scripts/compile_cli_catalogs.py
"""

from __future__ import annotations

from pathlib import Path

from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po

CATALOGS = Path(__file__).resolve().parents[1] / "openfatture" / "i18n" / "gettext"


def compile_catalogs() -> list[Path]:
    written = []
    for po_path in sorted(CATALOGS.glob("*/LC_MESSAGES/*.po")):
        with po_path.open("rb") as source:
            catalog = read_po(source)
        mo_path = po_path.with_suffix(".mo")
        with mo_path.open("wb") as target:
            write_mo(target, catalog)
        written.append(mo_path)
    return written


if __name__ == "__main__":
    for path in compile_catalogs():
        print(path.relative_to(CATALOGS.parents[2]))
