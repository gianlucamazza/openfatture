"""Every built-in tool declares its risk, and the default access is useful but safe."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from openfatture.ai.domain.context import ChatContext
from openfatture.ai.runtime.prompt import build_chat_system_prompt
from openfatture.ai.tools.models import ToolRisk
from openfatture.ai.tools.registry import ToolRegistry
from openfatture.ai.tools.registry.defaults import _register_default_tools
from openfatture.platform.config import Settings


def _registry(*, apply_ai_settings: bool = True) -> ToolRegistry:
    registry = ToolRegistry(apply_ai_settings=apply_ai_settings)
    _register_default_tools(registry)
    return registry


def _names(registry: ToolRegistry, settings: Settings) -> set[str]:
    with patch("openfatture.ai.tools.registry.core.get_settings", return_value=settings):
        return {tool.name for tool in registry.list_tools()}


def test_every_builtin_tool_declares_its_risk() -> None:
    undeclared = [
        tool.name
        for tool in _registry().list_tools(enabled_only=False)
        if "risk" not in tool.model_fields_set
    ]
    assert undeclared == []


def test_transmit_class_is_only_sdi_send() -> None:
    transmit = {
        tool.name
        for tool in _registry().list_tools(enabled_only=False)
        if tool.risk is ToolRisk.TRANSMIT
    }
    assert transmit == {"send_invoice_to_sdi"}


def test_mutating_and_transmit_tools_require_confirmation() -> None:
    unconfirmed = [
        tool.name
        for tool in _registry().list_tools(enabled_only=False)
        if tool.risk in (ToolRisk.MUTATE, ToolRisk.TRANSMIT) and not tool.requires_confirmation
    ]
    assert unconfirmed == []


def test_default_access_gates_changes_by_confirmation_not_by_hiding() -> None:
    registry = _registry()
    names = _names(registry, Settings())
    assert {
        "generate_invoice_pdf",
        "generate_invoice_summary_pdf",
        "generate_invoice_xml",
        "open_document",
        "search_invoices",
        "get_collections",
        "record_collection",
        "create_invoice",
    } <= names
    assert "send_invoice_to_sdi" not in names
    # Every change the default exposes still needs a human yes.
    for tool in registry.list_tools(enabled_only=False):
        if tool.name in names and tool.risk is ToolRisk.MUTATE:
            assert tool.requires_confirmation, tool.name


def test_standard_access_exposes_documents_but_no_mutation() -> None:
    names = _names(_registry(), Settings(ai_tool_access="standard"))
    assert {"generate_invoice_pdf", "open_document", "get_collections"} <= names
    assert "create_invoice" not in names
    assert "record_collection" not in names


def test_read_access_hides_pdf_and_full_shows_mutations() -> None:
    registry = _registry()
    read = _names(registry, Settings(ai_tool_access="read"))
    assert "generate_invoice_pdf" not in read
    assert "generate_invoice_summary_pdf" not in read
    assert "generate_invoice_xml" not in read  # it writes the archive file
    assert "open_document" not in read  # it starts another application
    full = _names(registry, Settings(ai_tool_access="full"))
    assert "create_invoice" in full
    assert "send_invoice_to_sdi" not in full


def test_disabled_capabilities_point_at_lowest_enabling_level() -> None:
    registry = _registry()
    with patch(
        "openfatture.ai.tools.registry.core.get_settings",
        return_value=Settings(ai_tool_access="read"),
    ):
        hidden = registry.disabled_capabilities()
    assert hidden["pdf"] == "openfatture config set ai_tool_access standard"
    assert hidden["clients"] == "openfatture config set ai_tool_access full"
    assert all("send_invoice_to_sdi" not in command for command in hidden.values())


def test_non_assistant_registry_reports_no_disabled_capabilities() -> None:
    assert _registry(apply_ai_settings=False).disabled_capabilities() == {}


@pytest.mark.parametrize("enable_tools", [True, False])
def test_prompt_states_disabled_capabilities_with_command(enable_tools: bool) -> None:
    context = ChatContext(
        user_input="genera pdf",
        available_tools=["search_invoices"],
        disabled_capabilities={"pdf": "openfatture config set ai_tool_access standard"},
    )
    prompt = build_chat_system_prompt(context, enable_tools=enable_tools)
    assert ("`openfatture config set ai_tool_access standard`" in prompt) is enable_tools
    assert "I tools includono" not in prompt
    assert "copia di cortesia" in prompt


def test_online_lookups_follow_access_and_the_offline_switch() -> None:
    registry = _registry()
    assert "check_vat_vies" in _names(registry, Settings(ai_tool_access="standard"))
    assert "check_vat_vies" in _names(registry, Settings())
    assert "check_vat_vies" not in _names(registry, Settings(ai_tool_access="read"))
    offline = Settings(ai_offline=True)
    assert "check_vat_vies" not in _names(registry, offline)
    with patch("openfatture.ai.tools.registry.core.get_settings", return_value=offline):
        assert registry.disabled_capabilities()["vat"] == "openfatture config set ai_offline false"
