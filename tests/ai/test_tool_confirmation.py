"""Refusal and confirmation gates for SDI/PEC transmit tools.

No test in this module talks to a network or uses real credentials.
The transmit function is always a MagicMock.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from openfatture.ai.tools.invoice_tools import get_invoice_tools
from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
from openfatture.ai.tools.registry import ToolRegistry
from openfatture.ai.tools.registry.policy import (
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
        assert cleaned == {"fattura_id": 1}


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
                return_value=False,
            ) as prompt,
        ):
            result = await registry.execute_tool("send_invoice_to_sdi", {"fattura_id": 1})

        prompt.assert_called_once_with("send_invoice_to_sdi")
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
                return_value=True,
            ),
        ):
            result = await registry.execute_tool("send_invoice_to_sdi", {"fattura_id": 3})

        assert result.success is True
        transmit.assert_called_once_with(fattura_id=3)
