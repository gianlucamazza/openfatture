"""Smoke + unit tests for the AI Assistant Streamlit page.

The page (``openfatture/web/pages/5_🤖_AI_Assistant.py``) previously had no
tests at all. This module adds:

1. A Streamlit ``AppTest`` smoke test that runs the page top-to-bottom with the
   service factories mocked, asserting it raises no unhandled exception and
   renders all four tabs.
2. Pure unit tests for the extracted helpers (``handle_slash_command`` and
   ``retry_with_backoff``) so the logic is covered independently of Streamlit.
"""

from unittest.mock import MagicMock, patch

import pytest
from streamlit.testing.v1 import AppTest

PAGE_PATH = "openfatture/web/pages/5_🤖_AI_Assistant.py"


def _make_ai_service() -> MagicMock:
    svc = MagicMock()
    svc.is_available.return_value = True
    return svc


def _make_custom_commands_service() -> MagicMock:
    svc = MagicMock()
    svc.list_commands.return_value = []
    svc.has_command.return_value = False
    return svc


def _make_session_service() -> MagicMock:
    svc = MagicMock()
    svc.list_sessions.return_value = []
    return svc


def _make_voice_service() -> MagicMock:
    svc = MagicMock()
    # Voice tab calls st.stop() when unavailable; keep it unavailable so the
    # smoke test exercises the (simpler) not-configured branch deterministically.
    svc.is_available.return_value = False
    return svc


def _build_apptest() -> AppTest:
    """Build an AppTest for the page.

    Service factory functions are patched by the caller (the page resolves them
    via ``from ... import get_*`` at run time, so patching the source modules is
    sufficient because the page module is (re)imported on ``run()``).
    """
    return AppTest.from_file(PAGE_PATH)


class TestAIAssistantPageSmoke:
    """End-to-end smoke test using Streamlit's AppTest harness."""

    def test_page_runs_without_exception_and_has_four_tabs(self):
        with (
            patch(
                "openfatture.web.services.ai_service.get_ai_service",
                _make_ai_service,
            ),
            patch(
                "openfatture.web.services.custom_commands_service.get_custom_commands_service",
                _make_custom_commands_service,
            ),
            patch(
                "openfatture.web.services.session_service.get_session_service",
                _make_session_service,
            ),
            patch(
                "openfatture.web.services.feedback_service.get_feedback_service",
                MagicMock,
            ),
            patch(
                "openfatture.web.services.voice_service.get_voice_service",
                _make_voice_service,
            ),
        ):
            at = _build_apptest()
            # Generous timeout: the page imports heavy modules (pydantic,
            # structlog, AI services) which can exceed the 3s AppTest default
            # on a cold import.
            at.run(timeout=60)

        # The page must run to completion without an unhandled exception.
        assert not at.exception, f"Page raised: {at.exception}"

        # All four tabs must be present.
        assert len(at.tabs) == 4

        # Title is rendered.
        assert len(at.title) >= 1


class TestHandleSlashCommand:
    """Unit tests for the extracted handle_slash_command helper."""

    def test_non_command_returns_none_none(self):
        from openfatture.web.pages._ai_assistant.helpers import handle_slash_command

        svc = MagicMock()
        expanded, feedback = handle_slash_command("hello there", svc, [])
        assert expanded is None
        assert feedback is None
        svc.has_command.assert_not_called()

    def test_help_command_returns_feedback_only(self):
        from openfatture.web.pages._ai_assistant.helpers import handle_slash_command

        svc = MagicMock()
        expanded, feedback = handle_slash_command("/help", svc, [])
        assert expanded is None
        assert feedback is not None

    def test_stats_command_uses_history(self):
        from openfatture.web.pages._ai_assistant.helpers import handle_slash_command

        svc = MagicMock()
        history = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ]
        # Must not raise even though /stats inspects history (was a latent
        # global-dependency bug in the original code).
        expanded, feedback = handle_slash_command("/stats", svc, history)
        assert expanded is None
        assert feedback is not None

    def test_custom_command_is_expanded(self):
        from openfatture.web.pages._ai_assistant.helpers import handle_slash_command

        svc = MagicMock()
        svc.has_command.return_value = True
        svc.execute_command.return_value = "EXPANDED PROMPT"
        expanded, feedback = handle_slash_command("/mycmd arg1", svc, [])
        assert expanded == "EXPANDED PROMPT"
        assert feedback is not None
        svc.execute_command.assert_called_once_with("/mycmd", ["arg1"])


class TestRetryWithBackoff:
    """Unit tests for the retry_with_backoff wrapper around utils.retry."""

    @pytest.mark.asyncio
    async def test_returns_value_on_first_success(self):
        from openfatture.web.pages._ai_assistant import helpers

        calls = {"n": 0}

        async def func():
            calls["n"] += 1
            return "ok"

        with patch.object(helpers.st, "warning"):
            result = await helpers.retry_with_backoff(func, max_retries=2, base_delay=0.0001)

        assert result == "ok"
        assert calls["n"] == 1

    @pytest.mark.asyncio
    async def test_retries_then_succeeds(self):
        from openfatture.web.pages._ai_assistant import helpers

        calls = {"n": 0}

        async def func():
            calls["n"] += 1
            if calls["n"] < 3:
                raise ConnectionError("transient")
            return "recovered"

        with patch.object(helpers.st, "warning"):
            result = await helpers.retry_with_backoff(func, max_retries=2, base_delay=0.0001)

        assert result == "recovered"
        # 2 failures + 1 success == 3 attempts (max_retries + 1).
        assert calls["n"] == 3

    @pytest.mark.asyncio
    async def test_propagates_after_exhausting_retries(self):
        from openfatture.web.pages._ai_assistant import helpers

        calls = {"n": 0}

        async def func():
            calls["n"] += 1
            raise ValueError("always fails")

        with patch.object(helpers.st, "warning"):
            with pytest.raises(ValueError, match="always fails"):
                await helpers.retry_with_backoff(func, max_retries=2, base_delay=0.0001)

        # max_retries + 1 total attempts.
        assert calls["n"] == 3
