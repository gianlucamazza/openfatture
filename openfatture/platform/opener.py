"""Open a generated document with the system's default application.

Only what OpenFatture produces can be opened: PDF, XML, signed XML (``.p7m``)
and CSV documents, or a folder, inside the exports or the archive directory. Opening needs a person at the
terminal and a graphical session; otherwise callers show the path instead.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from openfatture.platform.config import Settings, get_settings

OPENABLE_SUFFIXES = frozenset({".pdf", ".xml", ".p7m", ".csv"})
LAUNCH_CHECK_SECONDS = 2.0
"""How long to wait for the launcher to report a missing default application."""


class DocumentNotOpenable(ValueError):
    """The path is not a document OpenFatture may open."""


def document_roots(settings: Settings | None = None) -> tuple[Path, ...]:
    """Directories whose documents may be opened: exports and archive."""
    settings = settings or get_settings()
    return (settings.exports_dir.resolve(), settings.archivio_dir.resolve())


def resolve_document(path: str | Path, settings: Settings | None = None) -> Path:
    """Return the real path of an openable document or folder, or raise :class:`DocumentNotOpenable`.

    A relative path is taken from the exports directory (``.`` is the exports
    directory itself). Symbolic links are resolved before the check, so a link
    cannot point outside the roots.
    """
    roots = document_roots(settings)
    candidate = Path(path).expanduser()
    resolved = (candidate if candidate.is_absolute() else roots[0] / candidate).resolve()
    if not any(resolved.is_relative_to(root) for root in roots):
        raise DocumentNotOpenable(
            f"Only documents in {' or '.join(str(r) for r in roots)} can be opened: {path}"
        )
    if resolved.is_dir():
        return resolved
    if resolved.suffix.lower() not in OPENABLE_SUFFIXES:
        raise DocumentNotOpenable(
            f"Only {', '.join(sorted(OPENABLE_SUFFIXES))} documents can be opened: {path}"
        )
    if not resolved.is_file():
        raise DocumentNotOpenable(f"Document not found: {path}")
    return resolved


def documents_in(data: Any, settings: Settings | None = None) -> list[Path]:
    """Openable documents (files, not folders) named by the ``*_path`` fields of a tool result."""
    found: list[Path] = []
    for value in _path_values(data):
        try:
            document = resolve_document(value, settings)
        except DocumentNotOpenable:
            continue
        if document.is_dir():
            continue
        if document not in found:
            found.append(document)
    return found


def _path_values(data: Any) -> Iterator[str]:
    if isinstance(data, dict):
        for key, value in data.items():
            if key.endswith("_path") and isinstance(value, str) and value:
                yield value
            elif isinstance(value, dict | list):
                yield from _path_values(value)
    elif isinstance(data, list):
        for item in data:
            yield from _path_values(item)


def can_open() -> bool:
    """Whether a person at this terminal can see a document opened now."""
    if not sys.stdin.isatty():
        return False
    if sys.platform in ("win32", "darwin"):
        return True
    graphical = os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
    return bool(graphical) and shutil.which("xdg-open") is not None


def open_in_default_app(document: Path) -> None:
    """Start the default application for ``document`` without waiting for it.

    The application runs detached, so it neither blocks the chat nor writes
    into it. Raises ``OSError`` when it cannot be started, including when the
    launcher reports within :data:`LAUNCH_CHECK_SECONDS` that no application
    handles the file type.
    """
    if sys.platform == "win32":
        os.startfile(document)
        return
    command = ["open", str(document)] if sys.platform == "darwin" else ["xdg-open", str(document)]
    # A fixed launcher; resolve_document has already checked the path.
    launcher = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        code = launcher.wait(timeout=LAUNCH_CHECK_SECONDS)
    except subprocess.TimeoutExpired:
        return  # still running: the application is up (or in the foreground)
    if code != 0:
        raise OSError(f"No application opened {document.name} (launcher exit code {code})")


def open_document(path: str) -> dict[str, Any]:
    """Open a generated document for the person at the terminal."""
    try:
        document = resolve_document(path)
    except DocumentNotOpenable as exc:
        return {"error": str(exc)}
    if not can_open():
        return {
            "success": False,
            "opened": False,
            "path": str(document),
            "message": "No graphical session at this terminal: give the user the path instead",
        }
    try:
        open_in_default_app(document)
    except OSError as exc:
        return {"error": f"Cannot start the default application: {exc}", "path": str(document)}
    return {
        "success": True,
        "opened": True,
        "path": str(document),
        "message": f"Opened {document.name} with the default application",
    }
