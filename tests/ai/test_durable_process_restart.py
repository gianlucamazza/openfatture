"""Recovery after abrupt process exit, without provider/network dependencies."""

import subprocess
import sys
from pathlib import Path

SCRIPT = r"""
import asyncio
import os
import sys
from pathlib import Path
from openfatture.ai.domain.response import AgentResponse, ToolCall
from openfatture.ai.runtime.durability import DurableToolExecutor
from openfatture.ai.tools.models import ToolResult

root = Path(sys.argv[1])
phase = sys.argv[2]
class Provider:
    provider_name = 'openai'
    supports_tools = True
    async def generate(self, messages, **kwargs):
        if messages[-1].role.value == 'user':
            return AgentResponse(content='', tool_calls=[ToolCall(id='c1', name='write', arguments={})])
        if phase == 'crash':
            os._exit(23)
        return AgentResponse(content='recovered')
class Registry:
    confirmation_callback = None
    def get_openai_functions(self):
        return []
    def get_tool(self, name):
        return None
    async def execute_tool(self, **kwargs):
        with (root / 'effects').open('a') as f:
            f.write('effect\n')
        return ToolResult(tool_name='write', success=True, data={'id': 1})
async def main():
    result = await DurableToolExecutor(root).run(
        session_id='session', turn_id='turn', provider=Provider(), registry=Registry(),
        initial={'user_input': 'write'} if phase == 'crash' else None,
    )
    (root / 'answer').write_text(result['content'])
asyncio.run(main())
"""


def test_abrupt_process_restart_does_not_repeat_effect(tmp_path: Path) -> None:
    crashed = subprocess.run(
        [sys.executable, "-c", SCRIPT, str(tmp_path), "crash"], capture_output=True, timeout=30
    )
    assert crashed.returncode == 23, crashed.stderr.decode()
    recovered = subprocess.run(
        [sys.executable, "-c", SCRIPT, str(tmp_path), "resume"], capture_output=True, timeout=30
    )
    assert recovered.returncode == 0, recovered.stderr.decode()
    assert (tmp_path / "effects").read_text() == "effect\n"
    assert (tmp_path / "answer").read_text() == "recovered"
