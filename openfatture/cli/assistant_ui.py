"""Terminal-only presentation, input and approval for the assistant."""

from __future__ import annotations

import re
import time
from collections.abc import AsyncIterator, Iterator
from contextlib import ExitStack, asynccontextmanager
from pathlib import Path
from typing import Any

from rich.console import Console, Group, RenderableType
from rich.live import Live
from rich.markdown import Markdown
from rich.spinner import Spinner
from rich.text import Text

from openfatture.i18n import _
from openfatture.platform.logging import redact_sensitive


def translate(key: str, locale: str, **values: Any) -> str:
    from openfatture.i18n.loader import SUPPORTED_LOCALES, get_bundle
    from openfatture.platform.config import get_settings

    for candidate in dict.fromkeys((locale, get_settings().fallback_locale, "en", "it")):
        if candidate in SUPPORTED_LOCALES and get_bundle(candidate).has_message(key):
            return _(key, locale=candidate, **values)
    return key


_FENCE = re.compile(r"^\s*(```|~~~)")


def split_stable_markdown(text: str) -> tuple[str, str]:
    """Split ``text`` into completed Markdown blocks and the block still being written.

    The split happens after the last blank line outside a fenced code block, so
    code, tables and contiguous lists are never cut. ``stable + tail == text``.
    """
    in_fence = False
    position = 0
    split = 0
    for line in text.splitlines(keepends=True):
        position += len(line)
        if _FENCE.match(line):
            in_fence = not in_fence
        elif not in_fence and not line.strip() and line.endswith("\n"):
            if text[:position].strip():
                split = position
    return text[:split], text[split:]


class _LiveView:
    """Live area: the block being written plus an animated status line."""

    def __init__(self, presentation: ChatPresentation) -> None:
        self.presentation = presentation
        self.spinner = Spinner("dots")

    def __rich__(self) -> RenderableType:
        ui = self.presentation
        parts: list[RenderableType] = []
        if ui.buffer.strip():
            parts.append(Markdown(ui.buffer))
        if ui.tool or not ui.buffer.strip():
            elapsed = int(time.monotonic() - ui.status_since)
            label = (
                ui.text("assistant-tool-running", name=ui.tool)
                if ui.tool
                else ui.text("assistant-thinking")
            )
            self.spinner.update(text=Text(f"{label} {elapsed}s" if elapsed else label, style="dim"))
            parts.append(self.spinner)
        return Group(*parts)


class ChatPresentation:
    def __init__(self, console: Console, locale: str, *, interactive: bool = True):
        self.console = console
        self.locale = locale
        self.interactive = interactive
        self.live: Live | None = None
        self.prompt_session: Any = None
        self.buffer = ""
        self.tool: str | None = None
        self.status_since = time.monotonic()
        # Documents the tools produced in this chat, oldest first (for /open).
        self.documents: list[Path] = []

    def _set_status(self, tool: str | None) -> None:
        self.tool = tool
        self.status_since = time.monotonic()

    def _commit(self, *, everything: bool = False) -> None:
        """Print completed Markdown blocks permanently above the live area."""
        stable, self.buffer = (
            (self.buffer, "") if everything else split_stable_markdown(self.buffer)
        )
        if stable.strip():
            self.console.print(Markdown(stable))

    def text(self, key: str, **values: Any) -> str:
        return translate(key, self.locale, **values)

    async def read(self) -> str:
        if not self.interactive:
            return self.console.input(self.text("assistant-input") + " ")
        if self.prompt_session is None:
            from prompt_toolkit import PromptSession
            from prompt_toolkit.completion import CompleteEvent, Completer, Completion
            from prompt_toolkit.document import Document

            class SlashCompleter(Completer):
                def get_completions(
                    self, document: Document, complete_event: CompleteEvent
                ) -> Iterator[Completion]:
                    text = document.text_before_cursor
                    if text.startswith("/") and " " not in text and "\n" not in text:
                        for command in ("/help", "/open", "/exit", "/session", "/clear"):
                            if command.startswith(text):
                                yield Completion(command, start_position=-len(text))

            self.prompt_session = PromptSession(completer=SlashCompleter())
        value: str = await self.prompt_session.prompt_async(self.text("assistant-input") + " ")
        return value

    async def confirm(self, name: str, parameters: dict[str, Any]) -> bool:
        if not self.interactive:
            return False
        if self.live:
            self._commit(everything=True)
            self.live.stop()
        try:
            from prompt_toolkit import PromptSession

            self.console.print(Text(self.text("assistant-operation", name=name)))
            for key, value in redact_sensitive(parameters).items():
                self.console.print(Text(f"  {key}: {value}"))
            answer: str = await PromptSession().prompt_async(
                self.text("assistant-confirm-operation") + " "
            )
            return answer.strip().casefold() in {"s", "si", "sì", "y", "yes"}
        except (EOFError, KeyboardInterrupt):
            return False
        finally:
            if self.live:
                self.live.start()

    async def activity(self, name: str) -> None:
        if self.live:
            # Text written before a tool call is a complete thought: keep it.
            self._commit(everything=True)
            self._set_status(name)

    async def finished(self, name: str, success: bool, data: Any = None) -> None:
        from openfatture.platform.opener import documents_in

        documents = documents_in(data) if success else []
        for document in documents:
            if document in self.documents:
                self.documents.remove(document)
            self.documents.append(document)
        if self.live:
            mark, style = ("✓", "green") if success else ("✗", "red")
            label = self.text(
                "assistant-tool-completed" if success else "assistant-tool-failed", name=name
            )
            self.console.print(Text.assemble((f"{mark} ", style), (label, "dim")))
            for document in documents:
                self.console.print(self.document_line(document))
            self._set_status(None)

    def document_line(self, document: Path) -> Text:
        """The path of ``document`` as a terminal link (Ctrl+click opens it)."""
        return Text.assemble(
            ("  ↳ ", "dim"),
            (str(document), f"link {document.as_uri()}"),
            ("  " + self.text("assistant-document-open-hint"), "dim"),
        )

    async def render(self, iterator: AsyncIterator[Any]) -> str:
        from openfatture.platform.config import get_settings
        from openfatture.platform.logging import suppress_stdout_logging

        parts: list[str] = []
        complete = False
        self.buffer = ""
        self._set_status(None)
        with ExitStack() as stack:
            try:
                if self.console.is_terminal:
                    if not get_settings().debug_config.enable_debug_logging:
                        # Console log lines would tear through the live area.
                        stack.enter_context(suppress_stdout_logging())
                    self.live = Live(
                        _LiveView(self),
                        console=self.console,
                        transient=True,
                        vertical_overflow="visible",
                        refresh_per_second=12,
                    )
                    self.live.start()
                async for event in iterator:
                    content = (
                        event
                        if isinstance(event, str)
                        else event.get_text()
                        if event.is_content()
                        else ""
                    )
                    if content:
                        content = redact_sensitive(content)
                        parts.append(content)
                        if self.live:
                            self.buffer += content
                            self._commit()
                        else:
                            self.console.print(content, end="", markup=False, highlight=False)
                complete = True
            finally:
                # Explicitly close the runtime generator before restoring the input prompt.
                try:
                    close = getattr(iterator, "aclose", None)
                    if close:
                        await close()
                finally:
                    if self.live:
                        self.live.stop()
                        self.live = None
                        self._commit(everything=True)
                        self.tool = None
                    elif parts:
                        self.console.print()
                    if parts and not complete:
                        self.console.print(Text(self.text("assistant-incomplete")))
        return "".join(parts)


@asynccontextmanager
async def interruptible_turn() -> AsyncIterator[None]:
    """SIGINT cancels the active async turn and waits for its cleanup."""
    import asyncio
    import signal

    loop = asyncio.get_running_loop()
    task = asyncio.current_task()
    assert task is not None
    previous = signal.getsignal(signal.SIGINT)
    installed = False
    try:
        try:
            loop.add_signal_handler(signal.SIGINT, task.cancel)
            installed = True
        except (NotImplementedError, RuntimeError, ValueError):
            pass
        yield
    finally:
        if installed:
            loop.remove_signal_handler(signal.SIGINT)
            signal.signal(signal.SIGINT, previous)
