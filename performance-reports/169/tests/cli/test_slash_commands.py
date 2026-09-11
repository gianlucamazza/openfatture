"""In-chat slash commands for the interactive assistant."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from openfatture.cli.commands.assistant import _handle_slash_command


def test_slash_help_is_handled() -> None:
    runtime = SimpleNamespace(session_id="abc")
    assert _handle_slash_command("/help", runtime=runtime) == "handled"


def test_slash_exit() -> None:
    runtime = SimpleNamespace(session_id=None)
    assert _handle_slash_command("/exit", runtime=runtime) == "exit"
    assert _handle_slash_command("/quit", runtime=runtime) == "exit"


def test_normal_message_passes_through() -> None:
    runtime = SimpleNamespace(session_id=None)
    assert _handle_slash_command("lista fatture", runtime=runtime) is None


def test_slash_session() -> None:
    runtime = SimpleNamespace(session_id="sess-1")
    assert _handle_slash_command("/session", runtime=runtime) == "handled"


def test_slash_clear_persisted_session() -> None:
    session = MagicMock()
    store = MagicMock()
    runtime = SimpleNamespace(_session=session, _session_store=store, session_id="s")
    assert _handle_slash_command("/clear", runtime=runtime) == "handled"
    session.clear_messages.assert_called_once()
    store.save.assert_called_once_with(session)


def test_unknown_slash_is_handled() -> None:
    runtime = SimpleNamespace(session_id=None)
    assert _handle_slash_command("/nope", runtime=runtime) == "handled"
