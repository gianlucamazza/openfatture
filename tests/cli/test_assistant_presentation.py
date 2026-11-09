"""Presentation checks without network requests."""

from io import StringIO
from types import SimpleNamespace

import pytest
from rich.console import Console

from openfatture.cli.commands import assistant


@pytest.mark.asyncio
@pytest.mark.parametrize("terminal", [True, False])
async def test_stream_preserves_content_and_finishes(monkeypatch, terminal):
    output = StringIO()
    monkeypatch.setattr(
        assistant, "console", Console(file=output, force_terminal=terminal, width=60)
    )

    async def stream(message):
        yield "**Ciao"
        yield "**, mondo!"

    result = await assistant._render_stream(SimpleNamespace(stream=stream), "saluto")
    assert result == "**Ciao**, mondo!"
    assert "mondo!" in output.getvalue()
    if not terminal:
        assert output.getvalue() == "**Ciao**, mondo!\n"
        assert "\x1b" not in output.getvalue()


@pytest.mark.asyncio
async def test_stream_error_cleans_up_live_display(monkeypatch):
    output = StringIO()
    monkeypatch.setattr(assistant, "console", Console(file=output, force_terminal=True))

    async def stream(message):
        yield "Risposta parziale"
        raise RuntimeError("offline")

    with pytest.raises(RuntimeError, match="offline"):
        await assistant._render_stream(SimpleNamespace(stream=stream), "saluto")
    assert not assistant.console._live_stack


@pytest.mark.asyncio
@pytest.mark.parametrize("width", [40, 80, 120])
async def test_long_response_keeps_complete_final_text(monkeypatch, width):
    output = StringIO()
    monkeypatch.setattr(
        assistant, "console", Console(file=output, force_terminal=True, width=width, height=10)
    )

    async def stream(message):
        for number in range(50):
            yield f"Paragraph {number}.\n\n"

    runtime = SimpleNamespace(stream=stream)
    result = await assistant._render_stream(runtime, "long response")
    assert "Paragraph 49." in result
    assert "Paragraph 49." in output.getvalue()
    assert not assistant.console._live_stack
    assert not hasattr(runtime, "_presentation_live")


@pytest.mark.parametrize(
    "locale, expected", [("it", "Mostra questo aiuto"), ("en", "Show this help")]
)
def test_help_is_translated_without_warnings(monkeypatch, caplog, locale, expected):
    output = StringIO()
    monkeypatch.setattr(assistant, "console", Console(file=output))
    monkeypatch.setattr(assistant, "get_settings", lambda: SimpleNamespace(locale=locale))
    assert assistant._handle_slash_command("/help", runtime=object()) == "handled"
    assert expected in output.getvalue()
    assert "Translation not found" not in caplog.text
    assert "Failed to format" not in caplog.text


def test_configured_fallback_has_no_missing_translation_warning(monkeypatch, caplog):
    from openfatture.cli.assistant_ui import translate

    monkeypatch.setattr(
        "openfatture.platform.config.get_settings", lambda: SimpleNamespace(fallback_locale="it")
    )
    assert translate("assistant-help", "fr").startswith("Comandi")
    assert "Translation not found" not in caplog.text
    assert "Failed to format" not in caplog.text


@pytest.mark.asyncio
async def test_empty_response_releases_live_display():
    from openfatture.cli.assistant_ui import ChatPresentation

    output = StringIO()
    ui = ChatPresentation(Console(file=output, force_terminal=True), "it")

    async def empty():
        if False:
            yield ""

    assert await ui.render(empty()) == ""
    assert ui.live is None
    assert not ui.console._live_stack
