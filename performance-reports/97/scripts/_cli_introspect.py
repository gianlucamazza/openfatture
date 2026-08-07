#!/usr/bin/env python
"""Dump a Typer app's command tree (names + parameters) for refactor verification.

Usage:
    uv run python scripts/_cli_introspect.py <import.path:app_attr>

Example:
    uv run python scripts/_cli_introspect.py openfatture.payment.cli:app

Prints a deterministic, sorted representation of every command path and its
parameter names so a split refactor can be proven behaviour-preserving by
diffing the output captured before and after.
"""

from __future__ import annotations

import importlib
import sys
from typing import Any


def _params(callback: Any) -> list[str]:
    import inspect

    try:
        sig = inspect.signature(callback)
    except (TypeError, ValueError):
        return []
    return list(sig.parameters)


def _walk(app: Any, prefix: str, out: list[str]) -> None:
    # Direct commands on this app
    for cmd in getattr(app, "registered_commands", []) or []:
        name = cmd.name or (cmd.callback.__name__.replace("_", "-") if cmd.callback else "?")
        params = ",".join(sorted(_params(cmd.callback))) if cmd.callback else ""
        out.append(f"{prefix} {name} ({params})".strip())
    # Sub-typers / groups
    for grp in getattr(app, "registered_groups", []) or []:
        sub = grp.typer_instance
        gname = grp.name or "?"
        _walk(sub, f"{prefix} {gname}".strip(), out)


def main() -> int:
    if len(sys.argv) != 2 or ":" not in sys.argv[1]:
        print("usage: _cli_introspect.py <module.path:app_attr>", file=sys.stderr)
        return 2
    mod_path, attr = sys.argv[1].split(":", 1)
    module = importlib.import_module(mod_path)
    app = getattr(module, attr)
    out: list[str] = []
    _walk(app, "", out)
    for line in sorted(out):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
