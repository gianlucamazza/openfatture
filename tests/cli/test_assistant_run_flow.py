"""Control flow of the assistant command: resume, one-shot, piped and interactive turns."""

from __future__ import annotations

import asyncio
import io
import json
from collections.abc import AsyncIterator, Iterator
from types import SimpleNamespace
from typing import Any, cast

import pytest
import typer
from rich.console import Console

import openfatture.ai.runtime as ai_runtime
from openfatture.ai.domain.response import AgentResponse, ResponseStatus, UsageMetrics
from openfatture.ai.runtime.durability import UncertainToolOutcome
from openfatture.cli import assistant_ui
from openfatture.cli.assistant_ui import translate
from openfatture.cli.commands import assistant
from openfatture.events.ai_events import AICommandCompletedEvent, AICommandStartedEvent
from openfatture.platform import extras
from openfatture.storage.database import base

LOCALE = "en"


def _t(key: str, **values: Any) -> str:
    return translate(key, LOCALE, **values)


class FakeRuntime:
    """Scripted assistant runtime: outcomes map an input to success, failure or an error."""

    def __init__(self, outcomes: dict[str, bool | BaseException], pending: str | None) -> None:
        self.outcomes = outcomes
        self.pending_user_input = pending
        self.session_id: str | None = None
        self.calls: list[tuple[str, str]] = []
        self.last_response: AgentResponse | None = None
        self.total_usage = UsageMetrics(total_tokens=7, estimated_cost_usd=0.5)

    def _response(self, text: str) -> AgentResponse:
        outcome = self.outcomes.get(text, True)
        if isinstance(outcome, BaseException):
            raise outcome
        status = ResponseStatus.SUCCESS if outcome else ResponseStatus.ERROR
        return AgentResponse(content=f"reply:{text}", status=status)

    async def stream(self, text: str) -> AsyncIterator[str]:
        self.calls.append(("stream", text))
        self.last_response = self._response(text)
        yield self.last_response.content

    async def run(self, text: str) -> AgentResponse:
        self.calls.append(("run", text))
        return self._response(text)

    def clear_session(self) -> bool:
        return True


class Bus:
    def __init__(self) -> None:
        self.events: list[Any] = []

    def publish(self, event: Any) -> None:
        self.events.append(event)


class Harness(SimpleNamespace):
    console: Console
    output: io.StringIO
    bus: Bus
    runtime: FakeRuntime | None
    factory_kwargs: dict[str, Any]

    def configure(
        self,
        *,
        outcomes: dict[str, bool | BaseException] | None = None,
        pending: str | None = None,
        inputs: list[str | BaseException] | None = None,
        stdin: str = "",
        debug: bool = False,
    ) -> None:
        self.outcomes = outcomes or {}
        self.pending = pending
        self.inputs = list(inputs or [])
        self.stdin = stdin
        self.settings.debug_config.enable_debug_logging = debug

    def run(
        self,
        message: str | None,
        *,
        stream: bool = True,
        format_type: str = "rich",
        session_id: str | None = None,
    ) -> int:
        self.monkeypatch.setattr("sys.stdin", io.StringIO(self.stdin))
        try:
            ctx = cast(typer.Context, SimpleNamespace(obj={"format": format_type}))
            asyncio.run(assistant._run_assistant(ctx, message, stream, session_id))
        except typer.Exit as exc:
            return int(exc.exit_code)
        return 0

    @property
    def text(self) -> str:
        return self.output.getvalue()

    @property
    def completed(self) -> AICommandCompletedEvent:
        event = self.bus.events[-1]
        assert isinstance(event, AICommandCompletedEvent)
        return event


@pytest.fixture
def harness(monkeypatch: pytest.MonkeyPatch) -> Iterator[Harness]:
    output = io.StringIO()
    console = Console(file=output, force_terminal=False, width=200, color_system=None)
    settings = SimpleNamespace(
        locale=LOCALE,
        database_url="sqlite:///:memory:",
        debug_config=SimpleNamespace(enable_debug_logging=False),
        ai_provider="openai",
        ai_model="gpt-test",
    )
    h = Harness(
        console=console,
        output=output,
        bus=Bus(),
        runtime=None,
        factory_kwargs={},
        settings=settings,
        monkeypatch=monkeypatch,
    )
    h.configure()

    def factory(**kwargs: Any) -> FakeRuntime:
        h.factory_kwargs = kwargs
        h.runtime = FakeRuntime(h.outcomes, h.pending)
        return h.runtime

    async def read(self: assistant_ui.ChatPresentation) -> str:
        if not h.inputs:
            raise EOFError
        value = h.inputs.pop(0)
        if isinstance(value, BaseException):
            raise value
        return value

    monkeypatch.setattr(assistant, "console", console)
    monkeypatch.setattr(assistant, "get_settings", lambda: settings)
    monkeypatch.setattr(assistant, "get_event_bus", lambda: h.bus)
    monkeypatch.setattr(ai_runtime, "create_assistant_runtime", factory)
    # The runtime is faked: the flow must not depend on the ai extra being installed.
    monkeypatch.setattr(extras, "require_extra", lambda *args, **kwargs: None)
    monkeypatch.setattr(base, "init_db", lambda url: None)
    monkeypatch.setattr(assistant_ui.ChatPresentation, "read", read)
    yield h


def test_one_shot_streams_and_publishes_lifecycle(harness: Harness) -> None:
    assert harness.run("ciao", session_id="s1") == 0
    assert harness.runtime is not None
    assert harness.runtime.calls == [("stream", "ciao")]
    assert harness.factory_kwargs["persist_session"] is True
    assert harness.factory_kwargs["session_id"] == "s1"
    assert harness.factory_kwargs["interaction"] is None
    started, completed = harness.bus.events
    assert isinstance(started, AICommandStartedEvent)
    assert started.user_input == "ciao"
    assert started.parameters == {"stream": True, "interactive": False, "session_id": "s1"}
    assert completed.success is True
    assert completed.tokens_used == 7
    assert completed.error is None
    assert "reply:ciao" in harness.text


def test_one_shot_without_stream_renders_response(harness: Harness) -> None:
    assert harness.run("ciao", stream=False) == 0
    assert harness.runtime is not None
    assert harness.runtime.calls == [("run", "ciao")]
    assert harness.factory_kwargs["persist_session"] is False
    assert "reply:ciao" in harness.text


def test_one_shot_failure_exits_one(harness: Harness) -> None:
    harness.configure(outcomes={"ciao": False})
    assert harness.run("ciao") == 1
    assert _t("assistant-turn-failed") in harness.text
    assert harness.completed.success is False
    assert harness.completed.error is None


def test_machine_failure_does_not_print_human_hint(harness: Harness) -> None:
    harness.configure(outcomes={"ciao": False})
    assert harness.run("ciao", format_type="json") == 1
    assert _t("assistant-turn-failed") not in harness.text
    assert harness.runtime is not None
    assert harness.runtime.calls == [("run", "ciao")]


def test_pending_turn_resumes_before_request(harness: Harness) -> None:
    harness.configure(pending="earlier")
    assert harness.run("ciao") == 0
    assert harness.runtime is not None
    assert harness.runtime.calls == [("stream", "earlier"), ("stream", "ciao")]
    assert _t("assistant-resuming") in harness.text


def test_pending_turn_equal_to_request_runs_once(harness: Harness) -> None:
    harness.configure(pending="ciao")
    assert harness.run("ciao") == 0
    assert harness.runtime is not None
    assert harness.runtime.calls == [("stream", "ciao")]
    assert harness.completed.success is True


def test_failed_pending_turn_stops_one_shot(harness: Harness) -> None:
    harness.configure(pending="earlier", outcomes={"earlier": False})
    assert harness.run("ciao") == 1
    assert harness.runtime is not None
    assert harness.runtime.calls == [("stream", "earlier")]


def test_failed_pending_turn_continues_interactively(harness: Harness) -> None:
    harness.configure(pending="earlier", outcomes={"earlier": False}, inputs=["exit"])
    assert harness.run(None) == 0
    assert harness.completed.success is True


def test_uncertain_pending_turn_is_reported_interactively(harness: Harness) -> None:
    harness.configure(pending="earlier", outcomes={"earlier": UncertainToolOutcome("x")})
    assert harness.run(None) == 0
    assert _t("assistant-uncertain-tool") in harness.text
    assert harness.completed.success is True


def test_uncertain_pending_turn_fails_one_shot(harness: Harness) -> None:
    harness.configure(pending="earlier", outcomes={"earlier": UncertainToolOutcome("x")})
    assert harness.run("ciao") == 1
    assert _t("assistant-request-error") in harness.text
    assert harness.completed.error == "UncertainToolOutcome"


def test_machine_pending_turn_is_silent(harness: Harness) -> None:
    harness.configure(pending="earlier")
    assert harness.run("earlier", format_type="json") == 0
    assert _t("assistant-resuming") not in harness.text
    assert harness.runtime is not None
    assert harness.runtime.calls == [("run", "earlier")]

    assert _t("assistant-describe-what-you-need") not in harness.text


def test_interactive_loop_handles_commands_and_errors(harness: Harness) -> None:
    harness.configure(
        outcomes={"boom": RuntimeError("boom"), "stop": asyncio.CancelledError()},
        inputs=["", "  ", "/resume", "/help", "boom", "stop", "fine", "QUIT", "never"],
    )
    assert harness.run(None) == 0
    assert harness.runtime is not None
    assert harness.runtime.calls == [("stream", "boom"), ("stream", "stop"), ("stream", "fine")]
    text = harness.text
    assert "OpenFatture · gpt-test" in text
    assert _t("assistant-describe-what-you-need") in text
    assert _t("assistant-no-pending") in text
    assert _t("assistant-request-error") in text
    assert _t("assistant-interrupted") in text
    assert "Traceback" not in text
    assert harness.completed.success is True


def test_interactive_error_shows_traceback_in_debug(harness: Harness) -> None:
    harness.configure(outcomes={"boom": RuntimeError("boom")}, inputs=["boom"], debug=True)
    assert harness.run(None) == 0
    assert "Traceback" in harness.text


def test_interactive_keyboard_interrupt_on_turn(harness: Harness) -> None:
    harness.configure(outcomes={"stop": KeyboardInterrupt()}, inputs=["stop", "/exit", "never"])
    assert harness.run(None) == 0
    assert _t("assistant-interrupted") in harness.text
    assert harness.runtime is not None
    assert harness.runtime.calls == [("stream", "stop")]


def test_interactive_resume_runs_pending_turn(harness: Harness) -> None:
    harness.configure(pending="earlier", inputs=["/resume"])
    assert harness.run(None) == 0
    assert harness.runtime is not None
    assert harness.runtime.calls == [("stream", "earlier"), ("stream", "earlier")]


def test_interactive_read_interrupt_ends_session(harness: Harness) -> None:
    harness.configure(inputs=[KeyboardInterrupt(), "never"])
    assert harness.run(None) == 0
    assert harness.completed.success is True


def test_missing_extra_is_explained(harness: Harness, monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(extra: str, *, feature: str | None = None) -> None:
        raise extras.MissingExtraError(extra, feature=feature)

    monkeypatch.setattr(extras, "require_extra", missing)
    assert harness.run("ciao") == 1
    assert _t("assistant-missing-extra") in harness.text
    assert harness.runtime is None
    assert len(harness.bus.events) == 1
    assert harness.completed.success is False
    assert harness.completed.tokens_used == 0
    assert harness.completed.cost_usd == 0
    assert harness.completed.error == "MissingExtraError"


def test_startup_failure_in_debug_shows_traceback(
    harness: Harness, monkeypatch: pytest.MonkeyPatch
) -> None:
    harness.configure(debug=True)

    def broken(url: str) -> None:
        raise RuntimeError("database down")

    monkeypatch.setattr(base, "init_db", broken)
    assert harness.run("ciao") == 1
    assert _t("assistant-request-error") in harness.text
    assert "Traceback" in harness.text
    assert harness.completed.error == "RuntimeError"


def test_machine_failure_renders_structured_error(
    harness: Harness, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def broken(url: str) -> None:
        raise RuntimeError("database down")

    monkeypatch.setattr(base, "init_db", broken)
    assert harness.run("ciao", format_type="json") == 1
    rendered = harness.text + capsys.readouterr().out
    payload = json.loads(rendered[rendered.index("{") :])
    assert payload["error"] == "RuntimeError"
    assert _t("assistant-request-error") not in rendered


def test_cancelled_turn_fails_one_shot(harness: Harness) -> None:
    harness.configure(outcomes={"ciao": asyncio.CancelledError()})
    assert harness.run("ciao") == 1
    assert harness.completed.error == "CancelledError"


def test_without_event_bus_nothing_is_published(
    harness: Harness, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(assistant, "get_event_bus", lambda: None)
    assert harness.run("ciao") == 0
    assert harness.bus.events == []
