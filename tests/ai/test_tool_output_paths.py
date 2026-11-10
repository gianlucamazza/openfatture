"""Model-chosen output paths stay inside the exports directory."""

from pathlib import Path

import pytest

from openfatture.ai.tools import output_paths
from openfatture.ai.tools.output_paths import confine_output_path, confined_output
from openfatture.ai.tools.registry.core import ToolRegistry
from openfatture.ai.tools.registry.defaults import _register_default_tools


@pytest.fixture
def exports(tmp_path, monkeypatch) -> Path:
    base = tmp_path / "exports"
    monkeypatch.setattr(output_paths, "exports_dir", lambda: base)
    return base.resolve()


def test_relative_path_is_placed_in_exports(exports):
    assert confine_output_path("2026/fatture.csv") == str(exports / "2026" / "fatture.csv")
    assert (exports / "2026").is_dir()


@pytest.mark.parametrize("path", ["../escape.csv", "/etc/passwd", "a/../../escape.pdf"])
def test_paths_outside_exports_are_refused(exports, path):
    with pytest.raises(ValueError):
        confine_output_path(path)


def test_absolute_path_inside_exports_is_allowed(exports):
    target = exports / "ok.pdf"
    assert confine_output_path(str(target)) == str(target)


def test_wrapper_returns_error_and_does_not_call_tool(exports):
    calls: list[dict] = []

    @confined_output
    def tool(**kwargs):
        calls.append(kwargs)
        return {"ok": True}

    assert "error" in tool(output_path="/tmp/x.csv", anno=2026)
    assert calls == []
    assert tool(anno=2026) == {"ok": True}
    assert tool(output_path="x.csv") == {"ok": True}
    assert calls[-1]["output_path"] == str(exports / "x.csv")


def test_file_writing_tools_are_confined():
    registry = ToolRegistry()
    _register_default_tools(registry)
    for name in (
        "export_invoices_to_csv",
        "export_clients_to_csv",
        "generate_invoice_pdf",
        "generate_preventivo_pdf",
    ):
        tool = registry.get_tool(name)
        assert tool is not None, name
        assert getattr(tool.func, "__wrapped__", None) is not None, name


def test_broken_tool_module_fails_registration(monkeypatch):
    from openfatture.ai.tools import report_tools

    def broken():
        raise ImportError("missing dependency")

    monkeypatch.setattr(report_tools, "get_report_tools", broken)
    with pytest.raises(ImportError):
        _register_default_tools(ToolRegistry())
