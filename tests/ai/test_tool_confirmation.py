"""Refusal and confirmation gates for SDI/PEC transmit tools.

No test in this module talks to a network or uses real credentials.
The transmit function is always a MagicMock.
"""

from __future__ import annotations

import asyncio
import os
import select
import sys
import threading
import time
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import typer

from openfatture.ai.tools.invoice_tools import get_invoice_tools
from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType, ToolRisk
from openfatture.ai.tools.registry import ToolRegistry
from openfatture.ai.tools.registry.defaults import _register_default_tools
from openfatture.ai.tools.registry.policy import (
    build_confirmation_prompt,
    confirmation_required,
    disabled_remediation,
    is_interactive,
    is_tool_enabled_for_agent,
    prompt_human_confirmation,
    set_interactive_session,
    strip_reserved_parameters,
)
from openfatture.platform.config import Settings, parse_enabled_tools


@pytest.fixture(autouse=True)
def _reset_interactive_session() -> Any:
    set_interactive_session(False)
    yield
    set_interactive_session(False)


class _Tty:
    def isatty(self) -> bool:
        return True


def _settings(
    *,
    enabled_tools: str = "",
    access: str = "standard",
    require_confirmation: bool = True,
) -> Settings:
    return Settings(
        ai_tool_access=access,
        ai_enabled_tools=enabled_tools,
        ai_tools_require_confirmation=require_confirmation,
    )


def _send_tool(func: MagicMock) -> Tool:
    return Tool(
        name="send_invoice_to_sdi",
        risk=ToolRisk.TRANSMIT,
        description="Send invoice to SDI via PEC",
        category="invoices",
        parameters=[
            ToolParameter(
                name="fattura_id",
                type=ToolParameterType.INTEGER,
                description="Invoice ID",
                required=True,
            )
        ],
        func=func,
        requires_confirmation=True,
        enabled=False,
        tags=["write", "send", "transmit"],
    )


def _registry_with_send(func: MagicMock, *, apply_ai_settings: bool = False) -> ToolRegistry:
    registry = ToolRegistry(apply_ai_settings=apply_ai_settings)
    registry.register(_send_tool(func))
    return registry


class TestParseEnabledTools:
    def test_empty_means_no_extra_tools(self) -> None:
        assert parse_enabled_tools("") == frozenset()

    def test_names_are_parsed_and_trimmed(self) -> None:
        names = parse_enabled_tools(" search_invoices , send_invoice_to_sdi ")
        assert names == {"search_invoices", "send_invoice_to_sdi"}


def _tool(risk: ToolRisk, *, name: str = "probe", enabled: bool = True) -> Tool:
    return Tool(name=name, description="probe", func=lambda: None, risk=risk, enabled=enabled)


class TestPolicyHelpers:
    @pytest.mark.parametrize(
        ("access", "visible"),
        [
            ("read", {ToolRisk.READ}),
            ("standard", {ToolRisk.READ, ToolRisk.LOOKUP, ToolRisk.LOCAL_ARTIFACT}),
            (
                "full",
                {ToolRisk.READ, ToolRisk.LOOKUP, ToolRisk.LOCAL_ARTIFACT, ToolRisk.MUTATE},
            ),
        ],
    )
    def test_access_level_exposes_risk_classes(self, access: str, visible: set[ToolRisk]) -> None:
        settings = _settings(access=access)
        for risk in ToolRisk:
            enabled = is_tool_enabled_for_agent(_tool(risk), settings, apply_access=True)
            assert enabled is (risk in visible), (access, risk)

    def test_transmit_requires_explicit_name_at_every_level(self) -> None:
        send = _tool(ToolRisk.TRANSMIT, name="send_invoice_to_sdi", enabled=False)
        for access in ("read", "standard", "full"):
            assert not is_tool_enabled_for_agent(send, _settings(access=access), apply_access=True)
            assert not is_tool_enabled_for_agent(send, _settings(access=access), apply_access=False)
        opted_in = _settings(access="read", enabled_tools="send_invoice_to_sdi")
        assert is_tool_enabled_for_agent(send, opted_in, apply_access=True)

    def test_named_extra_tool_is_added_on_top_of_level(self) -> None:
        create = _tool(ToolRisk.MUTATE, name="create_invoice")
        assert not is_tool_enabled_for_agent(create, _settings(), apply_access=True)
        assert is_tool_enabled_for_agent(
            create, _settings(enabled_tools="create_invoice"), apply_access=True
        )

    def test_tool_flag_off_is_never_enabled_by_level(self) -> None:
        off = _tool(ToolRisk.READ, enabled=False)
        assert not is_tool_enabled_for_agent(off, _settings(access="full"), apply_access=True)

    def test_remediation_names_lowest_level(self) -> None:
        assert disabled_remediation(_tool(ToolRisk.LOCAL_ARTIFACT)).endswith(
            "ai_tool_access standard"
        )
        assert disabled_remediation(_tool(ToolRisk.MUTATE)).endswith("ai_tool_access full")
        assert disabled_remediation(_tool(ToolRisk.TRANSMIT, name="send_invoice_to_sdi")) == (
            "openfatture config set ai_enabled_tools send_invoice_to_sdi"
        )

    def test_confirmation_honours_setting_for_transmit(self) -> None:
        send = _tool(ToolRisk.TRANSMIT, name="send_invoice_to_sdi")
        assert confirmation_required(send, require_confirmation=True)
        assert not confirmation_required(send, require_confirmation=False)

    def test_reserved_parameters_are_stripped(self) -> None:
        cleaned = strip_reserved_parameters(
            {"fattura_id": 1, "confirm": True, "confirmed": True, "source": "human"}
        )
        assert cleaned == {"fattura_id": 1, "source": "human"}

    def test_confirm_like_keys_stripped_case_insensitively(self) -> None:
        cleaned = strip_reserved_parameters(
            {
                "fattura_id": 2,
                "Confirm": True,
                "CONFIRMED": True,
                "Confirmation": "yes",
                "source": "human",
            }
        )
        assert cleaned == {"fattura_id": 2, "source": "human"}
        assert "Confirm" not in cleaned
        assert "CONFIRMED" not in cleaned
        assert "Confirmation" not in cleaned


class TestConfirmationPrompt:
    def test_prompt_text_includes_invoice_id(self) -> None:
        prompt = build_confirmation_prompt("send_invoice_to_sdi", {"fattura_id": 42})
        assert "42" in prompt
        assert "send_invoice_to_sdi" in prompt
        assert "invoice ID" in prompt

    def test_prompt_includes_cheap_local_invoice_context(self) -> None:
        with patch(
            "openfatture.ai.tools.registry.policy._lookup_local_invoice_context",
            return_value={"client": "Acme S.r.l.", "total": 1220.0, "numero": "10"},
        ):
            prompt = build_confirmation_prompt("send_invoice_to_sdi", {"fattura_id": 42})
        assert "42" in prompt
        assert "Acme S.r.l." in prompt
        assert "1220" in prompt
        assert "10" in prompt
        assert "model provided" not in prompt

    def test_prompt_prefers_database_values_over_model(self) -> None:
        with patch(
            "openfatture.ai.tools.registry.policy._lookup_local_invoice_context",
            return_value={"client": "Acme S.r.l.", "total": 1220.0, "numero": "10"},
        ):
            prompt = build_confirmation_prompt(
                "send_invoice_to_sdi",
                {
                    "fattura_id": 42,
                    "cliente": "Evildoer S.p.A.",
                    "totale": 1,
                    "numero": "99",
                },
            )
        assert "invoice ID 42" in prompt
        assert "number 10 (from database; model provided 99)" in prompt
        assert "client Acme S.r.l. (from database; model provided Evildoer S.p.A.)" in prompt
        assert "total 1220.0 (from database; model provided 1)" in prompt

    def test_prompt_labels_model_provided_values_when_lookup_empty(self) -> None:
        with patch(
            "openfatture.ai.tools.registry.policy._lookup_local_invoice_context",
            return_value={},
        ):
            prompt = build_confirmation_prompt(
                "send_invoice_to_sdi",
                {"fattura_id": 42, "cliente": "Acme S.r.l.", "totale": 1220.0, "numero": "10"},
            )
        assert "invoice ID 42" in prompt
        assert "number 10 (model provided)" in prompt
        assert "client Acme S.r.l. (model provided)" in prompt
        assert "total 1220.0 (model provided)" in prompt


class TestSendToolDefaultDisabled:
    def test_invoice_tool_definition_is_disabled(self) -> None:
        send = next(tool for tool in get_invoice_tools() if tool.name == "send_invoice_to_sdi")
        assert send.enabled is False
        assert send.requires_confirmation is True

    def test_send_hidden_from_default_list_tools(self) -> None:
        registry = ToolRegistry()
        for tool in get_invoice_tools():
            registry.register(tool)

        with patch(
            "openfatture.ai.tools.registry.core.get_settings",
            return_value=_settings(),
        ):
            names = [tool.name for tool in registry.list_tools()]
        assert "send_invoice_to_sdi" not in names
        assert "search_invoices" in names

    @pytest.mark.asyncio
    async def test_send_disabled_by_default_makes_no_transmit_call(self) -> None:
        transmit = MagicMock(return_value={"success": True})
        registry = _registry_with_send(transmit)

        with patch(
            "openfatture.ai.tools.registry.core.get_settings",
            return_value=_settings(),
        ):
            result = await registry.execute_tool("send_invoice_to_sdi", {"fattura_id": 1})

        assert result.success is False
        assert result.error_type == "tool_disabled"
        assert result.error is not None
        assert "ai_enabled_tools" in result.error
        transmit.assert_not_called()

    def test_chat_registry_hides_tools_outside_allowlist(self) -> None:
        registry = ToolRegistry(apply_ai_settings=True)
        for tool in get_invoice_tools():
            registry.register(tool)

        with patch(
            "openfatture.ai.tools.registry.core.get_settings",
            return_value=_settings(),
        ):
            names = [tool.name for tool in registry.list_tools()]

        assert "search_invoices" in names
        assert "send_invoice_to_sdi" not in names
        assert "create_invoice" not in names


class TestSendRefusalWithoutConfirmation:
    @pytest.mark.asyncio
    async def test_enabled_send_without_confirmation_refuses(self) -> None:
        transmit = MagicMock(return_value={"success": True})
        registry = _registry_with_send(transmit)

        with (
            patch(
                "openfatture.ai.tools.registry.core.get_settings",
                return_value=_settings(enabled_tools="send_invoice_to_sdi"),
            ),
            patch(
                "openfatture.ai.tools.registry.policy.is_interactive",
                return_value=False,
            ),
        ):
            result = await registry.execute_tool("send_invoice_to_sdi", {"fattura_id": 1})

        assert result.success is False
        assert result.error_type == "confirmation_required"
        assert result.error is not None
        assert "human confirmation" in result.error
        transmit.assert_not_called()

    @pytest.mark.asyncio
    async def test_ai_source_cannot_self_confirm(self) -> None:
        transmit = MagicMock(return_value={"success": True})
        registry = _registry_with_send(transmit)

        with (
            patch(
                "openfatture.ai.tools.registry.core.get_settings",
                return_value=_settings(enabled_tools="send_invoice_to_sdi"),
            ),
            patch(
                "openfatture.ai.tools.registry.policy.is_interactive",
                return_value=False,
            ),
        ):
            result = await registry.execute_tool(
                "send_invoice_to_sdi",
                {"fattura_id": 1, "confirmed": True, "confirm": True},
                confirmed=True,
                source="ai",
            )

        assert result.success is False
        assert result.error_type == "confirmation_required"
        transmit.assert_not_called()

    @pytest.mark.asyncio
    async def test_interactive_decline_refuses(self) -> None:
        transmit = MagicMock(return_value={"success": True})
        registry = _registry_with_send(transmit)

        with (
            patch(
                "openfatture.ai.tools.registry.core.get_settings",
                return_value=_settings(enabled_tools="send_invoice_to_sdi"),
            ),
            patch(
                "openfatture.ai.tools.registry.policy.is_interactive",
                return_value=True,
            ),
            patch(
                "openfatture.ai.tools.registry.policy.prompt_human_confirmation",
                new=AsyncMock(return_value=False),
            ) as prompt,
        ):
            result = await registry.execute_tool("send_invoice_to_sdi", {"fattura_id": 1})

        prompt.assert_awaited_once()
        assert prompt.await_args is not None
        assert prompt.await_args.args[0] == "send_invoice_to_sdi"
        assert prompt.await_args.args[1]["fattura_id"] == 1
        assert result.success is False
        assert result.error_type == "confirmation_required"
        transmit.assert_not_called()


class TestConfirmationEscapeHatch:
    @pytest.mark.asyncio
    async def test_escape_hatch_still_requires_enabled_tools_opt_in(self) -> None:
        transmit = MagicMock(return_value={"success": True})
        registry = _registry_with_send(transmit)

        with patch(
            "openfatture.ai.tools.registry.core.get_settings",
            return_value=_settings(require_confirmation=False),
        ):
            result = await registry.execute_tool("send_invoice_to_sdi", {"fattura_id": 1})

        assert result.success is False
        assert result.error_type == "tool_disabled"
        transmit.assert_not_called()

    @pytest.mark.asyncio
    async def test_escape_hatch_with_opt_in_calls_mocked_transmit(self) -> None:
        transmit = MagicMock(return_value={"success": True, "invoice_id": 1})
        registry = _registry_with_send(transmit)

        with patch(
            "openfatture.ai.tools.registry.core.get_settings",
            return_value=_settings(
                enabled_tools="send_invoice_to_sdi",
                require_confirmation=False,
            ),
        ):
            result = await registry.execute_tool("send_invoice_to_sdi", {"fattura_id": 1})

        assert result.success is True
        transmit.assert_called_once_with(fattura_id=1)

    @pytest.mark.asyncio
    async def test_cased_confirm_keys_do_not_reach_function(self) -> None:
        transmit = MagicMock(return_value={"success": True, "invoice_id": 5})
        registry = _registry_with_send(transmit)

        with patch(
            "openfatture.ai.tools.registry.core.get_settings",
            return_value=_settings(
                enabled_tools="send_invoice_to_sdi",
                require_confirmation=False,
            ),
        ):
            result = await registry.execute_tool(
                "send_invoice_to_sdi",
                {"fattura_id": 5, "Confirm": True, "CONFIRMED": True},
            )

        assert result.success is True
        transmit.assert_called_once_with(fattura_id=5)


class TestConfirmedHumanPath:
    @pytest.mark.asyncio
    async def test_human_confirmed_path_calls_mocked_transmit(self) -> None:
        transmit = MagicMock(return_value={"success": True, "invoice_id": 7})
        registry = _registry_with_send(transmit)

        with patch(
            "openfatture.ai.tools.registry.core.get_settings",
            return_value=_settings(enabled_tools="send_invoice_to_sdi"),
        ):
            result = await registry.execute_tool(
                "send_invoice_to_sdi",
                {"fattura_id": 7},
                confirmed=True,
                source="human",
            )

        assert result.success is True
        assert result.data == {"success": True, "invoice_id": 7}
        transmit.assert_called_once_with(fattura_id=7)

    @pytest.mark.asyncio
    async def test_interactive_yes_calls_mocked_transmit(self) -> None:
        transmit = MagicMock(return_value={"success": True})
        registry = _registry_with_send(transmit)

        with (
            patch(
                "openfatture.ai.tools.registry.core.get_settings",
                return_value=_settings(enabled_tools="send_invoice_to_sdi"),
            ),
            patch(
                "openfatture.ai.tools.registry.policy.is_interactive",
                return_value=True,
            ),
            patch(
                "openfatture.ai.tools.registry.policy.prompt_human_confirmation",
                new=AsyncMock(return_value=True),
            ),
        ):
            result = await registry.execute_tool("send_invoice_to_sdi", {"fattura_id": 3})

        assert result.success is True
        transmit.assert_called_once_with(fattura_id=3)


class TestInteractivePromptDoesNotBlock:
    @pytest.mark.asyncio
    async def test_interactive_prompt_runs_off_the_event_loop(self) -> None:
        transmit = MagicMock(return_value={"success": True})
        registry = _registry_with_send(transmit)
        loop_ident = threading.get_ident()
        ask_idents: list[int] = []
        loop_progressed = False

        def fake_ask(prompt: str, cancelled: threading.Event | None = None) -> bool:
            ask_idents.append(threading.get_ident())
            assert "42" in prompt
            time.sleep(0.15)
            return False

        async def marker() -> None:
            nonlocal loop_progressed
            await asyncio.sleep(0.05)
            loop_progressed = True

        with (
            patch(
                "openfatture.ai.tools.registry.core.get_settings",
                return_value=_settings(enabled_tools="send_invoice_to_sdi"),
            ),
            patch(
                "openfatture.ai.tools.registry.policy.is_interactive",
                return_value=True,
            ),
            patch(
                "openfatture.ai.tools.registry.policy._ask_tty_confirmation",
                side_effect=fake_ask,
            ),
        ):
            result, _ = await asyncio.gather(
                registry.execute_tool("send_invoice_to_sdi", {"fattura_id": 42}),
                marker(),
            )

        assert ask_idents
        assert ask_idents[0] != loop_ident
        assert loop_progressed is True
        assert result.success is False
        assert result.error_type == "confirmation_required"
        transmit.assert_not_called()

    @pytest.mark.asyncio
    async def test_running_loop_without_tty_refuses(self) -> None:
        transmit = MagicMock(return_value={"success": True})
        registry = _registry_with_send(transmit)

        with (
            patch(
                "openfatture.ai.tools.registry.core.get_settings",
                return_value=_settings(enabled_tools="send_invoice_to_sdi"),
            ),
            patch(
                "openfatture.ai.tools.registry.policy.is_interactive",
                return_value=False,
            ),
            patch(
                "openfatture.ai.tools.registry.policy._ask_tty_confirmation",
                side_effect=AssertionError("TTY ask must not run without a TTY"),
            ),
        ):
            result = await registry.execute_tool("send_invoice_to_sdi", {"fattura_id": 1})

        assert result.success is False
        assert result.error_type == "confirmation_required"
        transmit.assert_not_called()


class TestRegistryStatsReflectPolicy:
    def test_get_stats_reports_allowlist_and_tool_flag(self) -> None:
        registry = ToolRegistry(apply_ai_settings=True)
        for tool in get_invoice_tools():
            registry.register(tool)

        with patch(
            "openfatture.ai.tools.registry.core.get_settings",
            return_value=_settings(),
        ):
            stats = registry.get_stats()

        assert "send_invoice_to_sdi" not in stats["enabled_tool_names"]
        assert "search_invoices" in stats["enabled_tool_names"]
        assert stats["enabled_tools"] == len(stats["enabled_tool_names"])
        assert stats["enabled_tools"] < stats["total_tools"]
        assert stats["enabled_by_tool_flag"] == len(
            [tool for tool in registry._tools.values() if tool.enabled]
        )
        assert stats["enabled_by_tool_flag"] != stats["enabled_tools"]


class TestDefaultRegistryAllDoesNotEnableSend:
    @pytest.mark.asyncio
    async def test_real_default_registry_all_hides_and_disables_send(self) -> None:
        registry = ToolRegistry(apply_ai_settings=True)
        _register_default_tools(registry)

        send = registry.get_tool("send_invoice_to_sdi")
        assert send is not None
        transmit = MagicMock(return_value={"success": True})
        send.func = transmit

        with patch(
            "openfatture.ai.tools.registry.core.get_settings",
            return_value=_settings(enabled_tools="all"),
        ):
            names = [tool.name for tool in registry.list_tools()]
            result = await registry.execute_tool("send_invoice_to_sdi", {"fattura_id": 1})

        assert "send_invoice_to_sdi" not in names
        assert result.success is False
        assert result.error_type == "tool_disabled"
        transmit.assert_not_called()


class TestInvoiceLookupRunsOffEventLoop:
    @pytest.mark.asyncio
    async def test_invoice_lookup_runs_off_the_event_loop(self) -> None:
        loop_ident = threading.get_ident()
        lookup_idents: list[int] = []
        loop_progressed = False

        def fake_lookup(fattura_id: Any) -> dict[str, Any]:
            lookup_idents.append(threading.get_ident())
            assert fattura_id == 42
            time.sleep(0.15)
            return {"client": "Acme S.r.l.", "total": 1220.0, "numero": "10"}

        async def marker() -> None:
            nonlocal loop_progressed
            await asyncio.sleep(0.05)
            loop_progressed = True

        with (
            patch(
                "openfatture.ai.tools.registry.policy.is_interactive",
                return_value=True,
            ),
            patch(
                "openfatture.ai.tools.registry.policy._lookup_local_invoice_context",
                side_effect=fake_lookup,
            ),
            patch(
                "openfatture.ai.tools.registry.policy._ask_tty_confirmation",
                return_value=False,
            ),
        ):
            result, _ = await asyncio.gather(
                prompt_human_confirmation("send_invoice_to_sdi", {"fattura_id": 42}),
                marker(),
            )

        assert lookup_idents
        assert lookup_idents[0] != loop_ident
        assert loop_progressed is True
        assert result is False


class TestStalePromptDoesNotSwallowNextLine:
    async def _assert_line_survives(self, run: Any) -> None:
        read_fd, write_fd = os.pipe()
        stdin = os.fdopen(read_fd, "r", buffering=1)
        try:
            with (
                patch(
                    "openfatture.ai.tools.registry.policy.is_interactive",
                    return_value=True,
                ),
                patch("sys.stdin", stdin),
            ):
                await run()
                os.write(write_fd, b"yes\n")
                ready, _, _ = select.select([read_fd], [], [], 0.3)
                assert ready, "stale prompt swallowed the next line"
                assert stdin.readline() == "yes\n"
        finally:
            stdin.close()
            os.close(write_fd)

    @pytest.mark.asyncio
    async def test_cancelled_prompt_does_not_swallow_next_line(self) -> None:
        async def run() -> None:
            task = asyncio.create_task(
                prompt_human_confirmation("send_invoice_to_sdi", {"fattura_id": 1})
            )
            await asyncio.sleep(0.15)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

        await self._assert_line_survives(run)

    @pytest.mark.asyncio
    async def test_timed_out_prompt_does_not_swallow_next_line(self) -> None:
        async def run() -> None:
            with pytest.raises(TimeoutError):
                await asyncio.wait_for(
                    prompt_human_confirmation("send_invoice_to_sdi", {"fattura_id": 1}),
                    timeout=0.15,
                )

        await self._assert_line_survives(run)


class TestInteractivityBeyondTty:
    def test_tty_alone_is_not_interactive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "stdin", _Tty())
        monkeypatch.setattr(sys, "stdout", _Tty())
        monkeypatch.delenv("OPENFATTURE_INTERACTIVE", raising=False)
        set_interactive_session(False)
        assert is_interactive() is False

    def test_cli_session_and_tty_is_interactive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "stdin", _Tty())
        monkeypatch.setattr(sys, "stdout", _Tty())
        monkeypatch.delenv("OPENFATTURE_INTERACTIVE", raising=False)
        set_interactive_session(True)
        assert is_interactive() is True

    def test_cli_session_without_tty_is_not_interactive(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(sys, "stdin", SimpleNamespace(isatty=lambda: False))
        monkeypatch.setattr(sys, "stdout", _Tty())
        monkeypatch.delenv("OPENFATTURE_INTERACTIVE", raising=False)
        set_interactive_session(True)
        assert is_interactive() is False

    def test_env_opt_in_with_tty_is_interactive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "stdin", _Tty())
        monkeypatch.setattr(sys, "stdout", _Tty())
        monkeypatch.setenv("OPENFATTURE_INTERACTIVE", "1")
        set_interactive_session(False)
        assert is_interactive() is True

    def test_env_opt_out_overrides_cli_session(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "stdin", _Tty())
        monkeypatch.setattr(sys, "stdout", _Tty())
        monkeypatch.setenv("OPENFATTURE_INTERACTIVE", "0")
        set_interactive_session(True)
        assert is_interactive() is False

    def test_assistant_start_opts_in_for_the_run(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from openfatture.cli.commands import assistant

        seen: list[bool] = []

        def fake_run(_coro: Any) -> None:
            monkeypatch.setattr(sys, "stdin", _Tty())
            monkeypatch.setattr(sys, "stdout", _Tty())
            monkeypatch.delenv("OPENFATTURE_INTERACTIVE", raising=False)
            seen.append(is_interactive())
            _coro.close()

        monkeypatch.setattr(assistant, "_ensure_setup", lambda _fmt: None)
        monkeypatch.setattr(assistant, "run_sync_with_lifespan", fake_run)
        monkeypatch.setattr(
            "openfatture.cli.formatters.utils.get_format_from_context",
            lambda _ctx: "rich",
        )

        assistant.start(
            cast(typer.Context, SimpleNamespace()), message="hello", stream=False, session=None
        )

        assert seen == [True]
        assert is_interactive() is False

    def test_assistant_start_resets_opt_in_on_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from openfatture.cli.commands import assistant

        def fake_run(_coro: Any) -> None:
            _coro.close()
            raise typer.Exit(1)

        monkeypatch.setattr(assistant, "_ensure_setup", lambda _fmt: None)
        monkeypatch.setattr(assistant, "run_sync_with_lifespan", fake_run)
        monkeypatch.setattr(
            "openfatture.cli.formatters.utils.get_format_from_context",
            lambda _ctx: "rich",
        )
        monkeypatch.setattr(sys, "stdin", _Tty())
        monkeypatch.setattr(sys, "stdout", _Tty())
        monkeypatch.delenv("OPENFATTURE_INTERACTIVE", raising=False)

        with pytest.raises(typer.Exit):
            assistant.start(
                cast(typer.Context, SimpleNamespace()), message="hello", stream=False, session=None
            )

        assert is_interactive() is False
