"""Terminal-only presentation, input and approval for the assistant."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
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


class ChatPresentation:
    def __init__(self, console: Console, locale: str, *, interactive: bool = True):
        self.console = console
        self.locale = locale
        self.interactive = interactive
        self.live: Live | None = None
        self.prompt_session: Any = None

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
                        for command in ("/help", "/exit", "/session", "/clear"):
                            if command.startswith(text):
                                yield Completion(command, start_position=-len(text))

            self.prompt_session = PromptSession(completer=SlashCompleter())
        return await self.prompt_session.prompt_async(self.text("assistant-input") + " ")

    async def confirm(self, name: str, parameters: dict[str, Any]) -> bool:
        if not self.interactive:
            return False
        if self.live:
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
            self.live.update(Text(self.text("assistant-tool-running", name=name)))

    async def finished(self, name: str, success: bool) -> None:
        if self.live:
            self.live.update(
                Text(
                    self.text(
                        "assistant-tool-completed" if success else "assistant-tool-failed",
                        name=name,
                    )
                )
            )

    async def render(self, iterator: AsyncIterator[Any]) -> str:
        parts: list[str] = []
        complete = False
        try:
            if self.console.is_terminal:
                self.live = Live(
                    Text(self.text("assistant-thinking")),
                    console=self.console,
                    transient=True,
                    vertical_overflow="ellipsis",
                    refresh_per_second=8,
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
                        self.live.update(Markdown("".join(parts)))
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
                    if parts:
                        self.console.print(Markdown("".join(parts)))
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
