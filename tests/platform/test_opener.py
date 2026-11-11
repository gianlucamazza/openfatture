"""Opening generated documents with the default application."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from openfatture.platform import opener
from openfatture.platform.config import Settings


@pytest.fixture
def settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Settings:
    data = tmp_path / "data"
    (data / "exports" / "riepiloghi").mkdir(parents=True)
    (tmp_path / "archivio" / "xml").mkdir(parents=True)
    fake = cast(
        Settings, SimpleNamespace(exports_dir=data / "exports", archivio_dir=tmp_path / "archivio")
    )
    monkeypatch.setattr(opener, "get_settings", lambda: fake)
    return fake


class _Launcher:
    """A launcher process that exits with ``code``, or keeps running when None."""

    def __init__(self, code: int | None) -> None:
        self.code = code

    def wait(self, timeout: float) -> int:
        if self.code is None:
            raise opener.subprocess.TimeoutExpired("xdg-open", timeout)
        return self.code


def _file(path: Path) -> Path:
    path.write_bytes(b"%PDF-1.4")
    return path


def test_documents_in_exports_and_archive_resolve(settings: Settings) -> None:
    pdf = _file(settings.exports_dir / "riepiloghi" / "r.pdf")
    xml = _file(settings.archivio_dir / "xml" / "IT1_00001.xml")
    assert opener.resolve_document(str(pdf)) == pdf.resolve()
    assert opener.resolve_document("riepiloghi/r.pdf") == pdf.resolve()  # relative to exports
    assert opener.resolve_document(str(xml)) == xml.resolve()


@pytest.mark.parametrize(
    ("make", "reason"),
    [
        (lambda s, t: _file(t / "outside.pdf"), "Only documents in"),
        (lambda s, t: _file(s.exports_dir / "script.sh"), "Only .csv, .p7m, .pdf, .xml"),
        (lambda s, t: s.exports_dir / "missing.pdf", "not found"),
        (lambda s, t: s.exports_dir / ".." / ".." / "outside.pdf", "Only documents in"),
    ],
)
def test_other_paths_are_refused(
    settings: Settings, tmp_path: Path, make: Any, reason: str
) -> None:
    _file(tmp_path / "outside.pdf")
    with pytest.raises(opener.DocumentNotOpenable, match=reason):
        opener.resolve_document(str(make(settings, tmp_path)))


def test_a_link_cannot_escape_the_roots(settings: Settings, tmp_path: Path) -> None:
    target = _file(tmp_path / "secret.pdf")
    link = settings.exports_dir / "link.pdf"
    link.symlink_to(target)
    with pytest.raises(opener.DocumentNotOpenable, match="Only documents in"):
        opener.resolve_document(str(link))


def test_documents_in_reads_path_fields_only(settings: Settings, tmp_path: Path) -> None:
    pdf = _file(settings.exports_dir / "a.pdf")
    csv = _file(settings.exports_dir / "b.csv")
    data = {
        "pdf_path": str(pdf),
        "message": str(pdf),
        "results": [{"output_path": str(csv)}, {"output_path": str(tmp_path / "outside.pdf")}],
        "xml_path": None,
    }
    assert opener.documents_in(data) == [pdf.resolve(), csv.resolve()]
    assert opener.documents_in("not a dict") == []


def _desktop(
    monkeypatch: pytest.MonkeyPatch, *, tty: bool = True, display: str | None = ":0"
) -> None:
    monkeypatch.setattr(opener.sys, "platform", "linux")
    monkeypatch.setattr(opener.sys, "stdin", SimpleNamespace(isatty=lambda: tty))
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    if display:
        monkeypatch.setenv("DISPLAY", display)
    else:
        monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.setattr(opener.shutil, "which", lambda name: f"/usr/bin/{name}")


def test_can_open_needs_a_terminal_and_a_graphical_session(monkeypatch: pytest.MonkeyPatch) -> None:
    _desktop(monkeypatch)
    assert opener.can_open() is True
    _desktop(monkeypatch, tty=False)
    assert opener.can_open() is False
    _desktop(monkeypatch, display=None)
    assert opener.can_open() is False


def test_open_document_starts_the_default_app_detached(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    pdf = _file(settings.exports_dir / "a.pdf")
    _desktop(monkeypatch)
    calls: list[tuple[list[str], dict[str, Any]]] = []

    def popen(cmd: list[str], **kwargs: Any) -> _Launcher:
        calls.append((cmd, kwargs))
        return _Launcher(None)

    monkeypatch.setattr(opener.subprocess, "Popen", popen)
    result = opener.open_document("a.pdf")
    assert result["opened"] is True
    assert calls[0][0] == ["xdg-open", str(pdf.resolve())]
    assert calls[0][1]["start_new_session"] is True


def test_open_document_without_desktop_returns_the_path(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    pdf = _file(settings.exports_dir / "a.pdf")
    _desktop(monkeypatch, display=None)
    monkeypatch.setattr(opener.subprocess, "Popen", lambda *a, **k: pytest.fail("must not open"))
    result = opener.open_document(str(pdf))
    assert result == {
        "success": False,
        "opened": False,
        "path": str(pdf.resolve()),
        "message": "No graphical session at this terminal: give the user the path instead",
    }


def test_open_document_reports_refused_paths(settings: Settings, tmp_path: Path) -> None:
    assert "Only documents in" in opener.open_document(str(_file(tmp_path / "x.pdf")))["error"]


def test_launch_failure_is_an_error(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    _file(settings.exports_dir / "a.pdf")
    _desktop(monkeypatch)

    def fail(*args: Any, **kwargs: Any) -> None:
        raise OSError("no handler")

    monkeypatch.setattr(opener.subprocess, "Popen", fail)
    assert "Cannot start the default application" in opener.open_document("a.pdf")["error"]


def test_signed_xml_and_folders_can_be_opened(settings: Settings) -> None:
    signed = _file(settings.archivio_dir / "xml" / "IT1_00001.xml.p7m")
    assert opener.resolve_document(str(signed)) == signed.resolve()
    assert opener.resolve_document(".") == settings.exports_dir.resolve()
    assert opener.resolve_document(str(settings.archivio_dir / "xml")).is_dir()
    # A folder named in a tool result is not offered as a document to open.
    assert opener.documents_in({"output_path": str(settings.exports_dir)}) == []


@pytest.mark.parametrize(("code", "opened"), [(0, True), (None, True), (3, False)])
def test_launcher_exit_code_tells_a_missing_application(
    settings: Settings, monkeypatch: pytest.MonkeyPatch, code: int | None, opened: bool
) -> None:
    _file(settings.exports_dir / "a.pdf")
    _desktop(monkeypatch)
    monkeypatch.setattr(opener.subprocess, "Popen", lambda *a, **k: _Launcher(code))
    result = opener.open_document("a.pdf")
    if opened:
        assert result["opened"] is True
    else:
        assert "No application opened a.pdf" in result["error"]
