#!/usr/bin/env python3
"""Repair Fluent values whose block content starts with Rich ``[markup]``.

Fluent parses an indented block value whose first content line starts with
``[`` as a (invalid, standalone) *variant key*, so the message is silently
dropped and lookups fall back to the raw key. For example:

    cli-report-iva-title =

        [bold blue]VAT Report - { $anno }[/bold blue]

never registers. The same content works inline:

    cli-report-iva-title = [bold blue]VAT Report - { $anno }[/bold blue]

This script rewrites every ``id =`` (message / term / attribute) whose value is
a single indented line starting with ``[`` into the inline form, dropping the
intervening blank line(s). It is idempotent and leaves all other entries
untouched.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ID_LINE = re.compile(r"^(\s*)(-?\.?[A-Za-z][A-Za-z0-9_-]* =)\s*$")


def fix_text(text: str) -> tuple[str, int]:
    lines = text.split("\n")
    out: list[str] = []
    fixed = 0
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        m = ID_LINE.match(line)
        if m:
            # Collect any blank lines, then the indented block value lines.
            j = i + 1
            while j < n and lines[j].strip() == "":
                j += 1
            block_start = j
            while j < n and lines[j].startswith("    ") and lines[j].strip():
                j += 1
            block = lines[block_start:j]
            # Inline only a single-line block value that opens with '['.
            if len(block) == 1 and block[0].lstrip().startswith("["):
                indent, head = m.group(1), m.group(2)
                out.append(f"{indent}{head} {block[0].strip()}")
                fixed += 1
                i = j
                continue
        out.append(line)
        i += 1
    return "\n".join(out), fixed


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path("openfatture/i18n/locales")
    total = 0
    for ftl in sorted(root.rglob("*.ftl")):
        original = ftl.read_text(encoding="utf-8")
        fixed_text, count = fix_text(original)
        if count:
            ftl.write_text(fixed_text, encoding="utf-8")
            total += count
            print(f"{ftl}: inlined {count} entries")
    print(f"Total entries inlined: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
