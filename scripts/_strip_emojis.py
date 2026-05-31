#!/usr/bin/env python
"""Strip emoji / pictographic characters from text files in place.

Removes emoji and common pictographic/dingbat/arrow ranges, then normalises the
whitespace they leave behind (e.g. ``"💰 Payment"`` -> ``"Payment"``,
``"Done ✅"`` -> ``"Done"``). Operates line by line so code structure is untouched.

Usage:
    python scripts/_strip_emojis.py <file> [<file> ...]
    python scripts/_strip_emojis.py --check <file> ...   # exit 1 if any emoji found

Designed for a one-off repo sweep; review the diff and run the test suite after.
"""

from __future__ import annotations

import re
import sys

# Pictographic ranges to remove. Deliberately excludes ranges that carry real
# textual meaning in this codebase: we keep currency/letters/punctuation.
_EMOJI = (
    "\U0001f000-\U0001faff"  # symbols & pictographs, emoji, supplemental
    "☀-➿"  # misc symbols + dingbats
    "⬀-⯿"  # misc symbols and arrows (stars, etc.)
    "⌀-⏿"  # misc technical (gear, hourglass, ...)
    "←-⇿"  # arrows (decorative)
    "︀-️"  # variation selectors
    "‍"  # zero-width joiner
    "⃣"  # combining enclosing keycap
    "™ℹ"  # trademark, information source
    "Ⓜ"  # circled M
    "\U0001f1e6-\U0001f1ff"  # regional indicators (flags)
)
_EMOJI_RE = re.compile(f"[{_EMOJI}]")

# Collapse "<emoji><spaces>" and "<spaces><emoji>" tidily: remove the emoji and
# one adjacent run of spaces, but never touch newlines/indentation logic because
# we only ever delete spaces that were directly next to an emoji.
_EMOJI_TRAILING_SPACE = re.compile(f"(?:{_EMOJI_RE.pattern})[ \\t]*")
_LEADING_SPACE_EMOJI = re.compile(f"[ \\t]*(?:{_EMOJI_RE.pattern})")


def strip_line(line: str) -> str:
    if not _EMOJI_RE.search(line):
        return line
    newline = "\n" if line.endswith("\n") else ""
    body = line[: -len(newline)] if newline else line
    # Drop emoji together with the spaces that follow, then with spaces before,
    # then any stray emoji left.
    body = _EMOJI_TRAILING_SPACE.sub("", body)
    body = _LEADING_SPACE_EMOJI.sub("", body)
    body = _EMOJI_RE.sub("", body)
    # Preserve leading indentation; collapse only internal runs of spaces.
    indent_len = len(body) - len(body.lstrip(" \t"))
    indent, rest = body[:indent_len], body[indent_len:]
    rest = re.sub(r"  +", " ", rest)
    return (indent + rest).rstrip() + newline


def process(path: str, check: bool) -> bool:
    with open(path, encoding="utf-8") as fh:
        content = fh.read()
    if check:
        return bool(_EMOJI_RE.search(content))
    new_lines = [strip_line(ln) for ln in content.splitlines(keepends=True)]
    new = "".join(new_lines)
    if new != content:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new)
        return True
    return False


def main(argv: list[str]) -> int:
    check = "--check" in argv
    files = [a for a in argv if a != "--check"]
    found = False
    for path in files:
        try:
            changed = process(path, check)
        except (OSError, UnicodeDecodeError) as exc:
            print(f"skip {path}: {exc}", file=sys.stderr)
            continue
        if check and changed:
            print(path)
            found = True
        elif changed:
            print(f"stripped {path}")
    return 1 if (check and found) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
