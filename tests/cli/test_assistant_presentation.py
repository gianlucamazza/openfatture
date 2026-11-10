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


# --- Incremental streaming -------------------------------------------------


def test_split_stable_markdown_keeps_open_blocks():
    from openfatture.cli.assistant_ui import split_stable_markdown

    assert split_stable_markdown("Uno.\n\nDue in corso") == ("Uno.\n\n", "Due in corso")
    assert split_stable_markdown("Nessuna riga vuota") == ("", "Nessuna riga vuota")
    assert split_stable_markdown("\n\nInizio") == ("", "\n\nInizio")
    fenced = "Testo.\n\n```python\nx = 1\n\ny = 2\n"
    assert split_stable_markdown(fenced) == ("Testo.\n\n", "```python\nx = 1\n\ny = 2\n")
    closed = "```\na\n\nb\n```\n\nDopo"
    assert split_stable_markdown(closed) == ("```\na\n\nb\n```\n\n", "Dopo")
    table = "| a | b |\n|---|---|\n| 1 | 2 |\n"
    assert split_stable_markdown(table) == ("", table)


def _terminal_ui(width: int = 80):
    from openfatture.cli.assistant_ui import ChatPresentation

    output = StringIO()
    console = Console(file=output, force_terminal=True, width=width, height=10)
    return ChatPresentation(console, "it"), output


@pytest.mark.asyncio
async def test_blocks_are_printed_once_without_final_reprint():
    ui, output = _terminal_ui()

    async def stream():
        for number in range(30):
            yield f"Blocco numero {number}.\n\n"

    await ui.render(stream())
    text = output.getvalue()
    for number in range(30):
        assert text.count(f"Blocco numero {number}.") == 1, number
    # No overflow ellipsis: the only "…" is the spinner label.
    assert "…" not in text.replace("Elaborazione…", "")


@pytest.mark.asyncio
async def test_text_before_a_tool_stays_visible():
    ui, output = _terminal_ui()

    async def stream():
        yield "Controllo le fatture"
        await ui.activity("search_invoices")
        await ui.finished("search_invoices", True)
        yield "Ci sono 2 fatture aperte."

    result = await ui.render(stream())
    text = output.getvalue()
    before, tool, after = (
        text.index("Controllo le fatture"),
        text.index("✓"),
        text.index("Ci sono 2 fatture aperte."),
    )
    assert before < tool < after
    assert result == "Controllo le fattureCi sono 2 fatture aperte."


@pytest.mark.asyncio
async def test_partial_stream_reports_incomplete_and_releases_live():
    ui, output = _terminal_ui()

    async def stream():
        yield "Primo blocco.\n\nSecondo"
        raise RuntimeError("offline")

    with pytest.raises(RuntimeError):
        await ui.render(stream())
    text = output.getvalue()
    assert "Primo blocco." in text and "Secondo" in text
    assert "Risposta incompleta." in text
    assert ui.live is None and not ui.console._live_stack


@pytest.mark.asyncio
@pytest.mark.parametrize("debug", [False, True])
async def test_console_logs_are_silenced_while_streaming(monkeypatch, debug):
    import logging

    from openfatture.platform import config

    settings = config.get_settings()
    monkeypatch.setattr(settings.debug_config, "enable_debug_logging", debug)
    import sys

    captured: list[str] = []

    class Recorder(logging.StreamHandler):
        def emit(self, record: logging.LogRecord) -> None:
            captured.append(record.getMessage())

    handler = Recorder(sys.stderr)
    root = logging.getLogger()
    root.addHandler(handler)
    try:
        ui, _output = _terminal_ui()

        async def stream():
            logging.getLogger("openfatture.test").warning("noisy_warning")
            yield "ok"

        await ui.render(stream())
    finally:
        root.removeHandler(handler)
    assert ("noisy_warning" in captured) is debug
