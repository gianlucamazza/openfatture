"""Real pseudo-terminal coverage, using in-memory tools and no network."""

from __future__ import annotations

import os
import select
import signal
import struct
import sys
import time
from pathlib import Path

import pytest

from openfatture.platform.extras import available_extras

pytestmark = [
    pytest.mark.skipif(sys.platform != "linux", reason="Linux PTY integration"),
    pytest.mark.skipif(
        not available_extras().get("ai"), reason="AI extra required for assistant integration"
    ),
]

CHILD = r"""
import asyncio
from pathlib import Path
from openfatture.ai.domain.response import AgentResponse, ToolCall, UsageMetrics
from openfatture.ai.runtime.service import AssistantRuntime
from openfatture.ai.tools.registry import ToolRegistry
from openfatture.ai.tools.models import Tool
from openfatture.cli.main import app
import openfatture.ai.runtime as api
import openfatture.ai.runtime.service as service

registry = ToolRegistry()
def write():
    p = Path('effects.txt')
    p.write_text(p.read_text() + 'effect\n' if p.exists() else 'effect\n')
    return 'fake operation complete'
registry.register(Tool(name='write_test', description='Fake local test operation', func=write, requires_confirmation=True))
registry.register(Tool(name='read_test', description='Fake local read', func=lambda: 'READ_OK'))
service.get_tool_registry = lambda: registry
class Provider:
    model = 'fake-model'
    provider_name = 'openai'
    supports_tools = True
    waited = False
    async def generate(self, messages, **kwargs):
        if messages[-1].role.value == 'tool':
            return AgentResponse(content='TOOL_DONE', usage=UsageMetrics(total_tokens=1))
        text = messages[-1].content
        if text == 'wait' and self.waited:
            return AgentResponse(content='WAIT_DONE')
        if text == 'wait':
            self.waited = True
            print('WAIT_READY', flush=True)
            await asyncio.Event().wait()
        if text == 'long':
            return AgentResponse(content='\n\n'.join(f'Paragraph {n}.' for n in range(75)))
        if text in ('confirm', 'read'):
            name = 'write_test' if text == 'confirm' else 'read_test'
            return AgentResponse(content='', tool_calls=[ToolCall(id='call', name=name, arguments={})])
        return AgentResponse(content='HELLO_DONE', usage=UsageMetrics(total_tokens=1))
api.create_assistant_runtime = lambda **kwargs: AssistantRuntime(provider=Provider(), **kwargs)
app()
"""


class Terminal:
    def __init__(self, tmp_path, width, command=()):
        import fcntl
        import pty
        import termios

        root = Path(__file__).resolve().parents[2]
        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            os.chdir(tmp_path)
            env = dict(
                os.environ,
                PYTHONPATH=str(root),
                TERM="xterm-256color",
                PROMPT_TOOLKIT_NO_CPR="1",
                NO_COLOR="1",
                DATABASE_URL=f"sqlite:///{tmp_path}/test.db",
                DATA_DIR=str(tmp_path / "data"),
                ARCHIVIO_DIR=str(tmp_path / "archive"),
                CERTIFICATES_DIR=str(tmp_path / "certs"),
                AI_MODEL="fake-model",
                AI_API_KEY="fake-key",
                CEDENTE_PARTITA_IVA="12345678903",
                CEDENTE_DENOMINAZIONE="Test SRL",
                OPENFATTURE_CONFIG_DIR=str(tmp_path / "config"),
                OPENFATTURE_SECRET_BACKEND="file",
            )
            os.execve(sys.executable, [sys.executable, "-u", "-c", CHILD, *command], env)
        self.output = b""
        fcntl.ioctl(self.fd, termios.TIOCSWINSZ, struct.pack("HHHH", 12, width, 0, 0))

    def resize(self, width):
        import fcntl
        import termios

        fcntl.ioctl(self.fd, termios.TIOCSWINSZ, struct.pack("HHHH", 10, width, 0, 0))
        os.kill(self.pid, signal.SIGWINCH)

    def expect(self, text, timeout=15):
        wanted = text.encode()
        deadline = time.monotonic() + timeout
        while wanted not in self.output:
            if time.monotonic() > deadline:
                pytest.fail(f"PTY timed out waiting for {text!r}: {self.output[-2000:]!r}")
            if select.select([self.fd], [], [], 0.1)[0]:
                try:
                    chunk = os.read(self.fd, 65536)
                except OSError:
                    pytest.fail(f"PTY exited: {self.output[-2000:]!r}")
                self.output += chunk
        before, self.output = self.output.split(wanted, 1)
        return before

    def send(self, text):
        os.write(self.fd, text.encode())

    def close(self):
        try:
            os.kill(self.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        os.waitpid(self.pid, 0)
        os.close(self.fd)


@pytest.mark.parametrize("width", [40, 80, 120])
def test_real_terminal_long_response_confirmation_and_interrupt(tmp_path, width):
    terminal = Terminal(tmp_path, width)
    try:
        # A missing database is set up by `init` before the chat opens.
        terminal.expect("Configurazione mancante")
        terminal.expect("Inizializzazione del database")
        terminal.expect("Tu ›")
        assert (tmp_path / "test.db").exists()
        terminal.send("long\n")
        terminal.expect("Paragraph 74.")
        terminal.expect("Tu ›")
        terminal.send("confirm\n")
        terminal.expect("Confermi questa operazione?")
        assert not (tmp_path / "effects.txt").exists()
        terminal.send("n\n")
        terminal.expect("Tu ›")
        assert not (tmp_path / "effects.txt").exists()
        terminal.send("confirm\n")
        terminal.expect("Confermi questa operazione?")
        terminal.send("s\n")
        terminal.expect("Tu ›")
        assert (tmp_path / "effects.txt").read_text() == "effect\n"
        terminal.send("wait\n")
        terminal.expect("WAIT_READY")
        terminal.resize(max(30, width // 2))
        os.kill(terminal.pid, signal.SIGINT)
        terminal.expect("Tu ›")
        terminal.send("/resume\n")
        terminal.expect("WAIT_DONE")
        terminal.expect("Tu ›")
        terminal.send("hello\n")
        terminal.expect("HELLO_DONE")
        terminal.expect("Tu ›")
        terminal.send("confirm\n")
        terminal.expect("Confermi questa operazione?")
        terminal.send("\x04")
        terminal.expect("Tu ›")
        assert (tmp_path / "effects.txt").read_text() == "effect\n"
        terminal.send("/exit\n")
    finally:
        terminal.close()
