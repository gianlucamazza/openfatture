"""Ollama works with the lifespan's shared HTTP client, which has no base URL."""

import httpx
import pytest

from openfatture.ai.domain.message import Message, Role
from openfatture.ai.providers.ollama import OllamaProvider


@pytest.mark.asyncio
async def test_generate_uses_absolute_url_with_shared_client() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(200, json={"response": "ciao", "done": True})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as shared:
        provider = OllamaProvider(
            base_url="http://127.0.0.1:11434/", model="qwen3:8b", http_client=shared
        )
        response = await provider.generate([Message(role=Role.USER, content="ciao")])

    assert seen == ["http://127.0.0.1:11434/api/generate"]
    assert response.content == "ciao"
