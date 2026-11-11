"""In-chat slash commands for the interactive assistant."""

from __future__ import annotations

from unittest.mock import MagicMock

from openfatture.ai.runtime.service import AssistantRuntime
from openfatture.cli.commands.assistant import _handle_slash_command


def test_slash_help_is_handled() -> None:
    runtime = MagicMock(spec=AssistantRuntime, session_id="abc")
    assert _handle_slash_command("/help", runtime=runtime) == "handled"


def test_slash_exit() -> None:
    runtime = MagicMock(spec=AssistantRuntime, session_id=None)
    assert _handle_slash_command("/exit", runtime=runtime) == "exit"
    assert _handle_slash_command("/quit", runtime=runtime) == "exit"


def test_normal_message_passes_through() -> None:
    runtime = MagicMock(spec=AssistantRuntime, session_id=None)
    assert _handle_slash_command("lista fatture", runtime=runtime) is None


def test_slash_session() -> None:
    runtime = MagicMock(spec=AssistantRuntime, session_id="sess-1")
    assert _handle_slash_command("/session", runtime=runtime) == "handled"


def test_slash_clear_persisted_session() -> None:
    clear = MagicMock(return_value=True)
    runtime = MagicMock(spec=AssistantRuntime, clear_session=clear, session_id="s")
    assert _handle_slash_command("/clear", runtime=runtime) == "handled"
    clear.assert_called_once_with()


def test_unknown_slash_is_handled() -> None:
    runtime = MagicMock(spec=AssistantRuntime, session_id=None)
    assert _handle_slash_command("/nope", runtime=runtime) == "handled"


def _open(monkeypatch, command: str, documents: list, *, desktop: bool = True) -> tuple[str, list]:
    from io import StringIO

    from rich.console import Console

    from openfatture.cli.commands import assistant
    from openfatture.platform import opener

    output = StringIO()
    opened: list = []
    monkeypatch.setattr(assistant, "console", Console(file=output, width=200))
    monkeypatch.setattr(opener, "can_open", lambda: desktop)
    monkeypatch.setattr(opener, "open_in_default_app", opened.append)
    runtime = MagicMock(spec=AssistantRuntime, session_id=None)
    assert _handle_slash_command(command, runtime=runtime, documents=documents) == "handled"
    return output.getvalue(), opened


def test_open_starts_the_latest_document(monkeypatch, tmp_path) -> None:
    first, second = tmp_path / "a.pdf", tmp_path / "b.pdf"
    text, opened = _open(monkeypatch, "/open", [first, second])
    assert opened == [second]
    assert "Aperto: b.pdf" in text
    _text, opened = _open(monkeypatch, "/open 2", [first, second])
    assert opened == [first]


def test_open_explains_what_is_missing(monkeypatch, tmp_path) -> None:
    document = tmp_path / "a.pdf"
    assert "Nessun documento" in _open(monkeypatch, "/open", [])[0]
    text, opened = _open(monkeypatch, "/open 3", [document])
    assert opened == [] and "da 1 a 1" in text
    text, opened = _open(monkeypatch, "/open", [document], desktop=False)
    assert opened == [] and str(document) in text


def _slash(monkeypatch, tmp_path, command: str) -> str:
    from io import StringIO

    from rich.console import Console

    from openfatture.ai import memory
    from openfatture.ai.memory.store import MemoryStore
    from openfatture.cli.commands import assistant

    store = MemoryStore(tmp_path / "memory.json")
    monkeypatch.setattr(memory, "get_memory_store", lambda: store)
    output = StringIO()
    monkeypatch.setattr(assistant, "console", Console(file=output, width=200))
    runtime = MagicMock(spec=AssistantRuntime, session_id=None)
    if command != "/memory-empty":
        store.add("Alloca dalla fattura più vecchia")
    assert _handle_slash_command(command.replace("-empty", ""), runtime=runtime) == "handled"
    return output.getvalue()


def test_memory_lists_the_notes(monkeypatch, tmp_path) -> None:
    assert "Nessuna nota salvata" in _slash(monkeypatch, tmp_path, "/memory-empty")
    assert "[1] Alloca dalla fattura più vecchia" in _slash(monkeypatch, tmp_path, "/memory")


def test_forget_deletes_a_note(monkeypatch, tmp_path) -> None:
    assert "Nota cancellata: Alloca" in _slash(monkeypatch, tmp_path, "/forget 1")
    assert "/forget 2" in _slash(monkeypatch, tmp_path, "/forget x")
