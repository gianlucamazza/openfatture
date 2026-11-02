"""Refusal and confirmation gates for SDI/PEC transmit tools.

No test in this module talks to a network or uses real credentials.
The transmit function is always a MagicMock.
"""

from __future__ import annotations

import asyncio
import threading
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openfatture.ai.tools.invoice_tools import get_invoice_tools
from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
from openfatture.ai.tools.registry import ToolRegistry
from openfatture.ai.tools.registry.defaults import _register_default_tools
from openfatture.ai.tools.registry.policy import (
    build_confirmation_prompt,
    confirmation_required,
    is_tool_enabled_for_agent,
    parse_enabled_tools,
    strip_reserved_parameters,
)
from openfatture.platform.config import Settings

DEFAULT_READONLY_TOOLS = (
    "search_invoices,get_invoice_details,get_invoice_stats,"
    "search_clients,get_client_details,get_client_stats"
)


def _settings(
    *,
    enabled_tools: str = DEFAULT_READONLY_TOOLS,
    require_confirmation: bool = True,
) -> Settings:
    return Settings(
        ai_enabled_tools=enabled_tools,
        ai_tools_require_confirmation=require_confirmation,
    )


def _send_tool(func: MagicMock) -> Tool:
    return Tool(
        name="send_invoice_to_sdi",
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
    def test_default_list_excludes_send(self) -> None:
        names = parse_enabled_tools(DEFAULT_READONLY_TOOLS)
        assert names is not None
        assert "send_invoice_to_sdi" not in names
        assert "search_invoices" in names

    def test_all_means_non_transmit_allow_all(self) -> None:
        assert parse_enabled_tools("all") is None
        assert parse_enabled_tools("") is None

    def test_explicit_send_is_parsed(self) -> None:
        names = parse_enabled_tools("search_invoices,send_invoice_to_sdi")
        assert names is not None
        assert "send_invoice_to_sdi" in names


class TestPolicyHelpers:
    def test_transmit_requires_explicit_name_not_all(self) -> None:
        assert not is_tool_enabled_for_agent(
            "send_invoice_to_sdi",
            "all",
            apply_allowlist=True,
            tool_enabled=True,
        )
        assert is_tool_enabled_for_agent(
            "send_invoice_to_sdi",
            "send_invoice_to_sdi",
            apply_allowlist=True,
            tool_enabled=False,
        )

    def test_confirmation_honours_setting_for_transmit(self) -> None:
        assert confirmation_required(
            "send_invoice_to_sdi",
            tool_requires_confirmation=True,
            require_confirmation=True,
        )
        assert not confirmation_required(
            "send_invoice_to_sdi",
            tool_requires_confirmation=True,
            require_confirmation=False,
        )

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

        def fake_ask(prompt: str) -> bool:
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
