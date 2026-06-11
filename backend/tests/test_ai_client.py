"""
OpenAI-compatible AI 客户端测试
"""

import pytest

from app.services import ai_client
from app.services.ai_client import AIProviderError, OpenAICompatibleClient


async def test_client_wraps_success_response_invalid_json(monkeypatch):
    class FakeResponse:
        status_code = 200

        def json(self):
            raise ValueError("invalid json")

    class FakeAsyncClient:
        def __init__(self, *, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr(ai_client.httpx, "AsyncClient", FakeAsyncClient)
    client = OpenAICompatibleClient(
        base_url="https://api.example.com/v1",
        api_key="secret",
        model="gpt-compatible",
        timeout_seconds=30,
    )

    with pytest.raises(AIProviderError, match="有效 JSON"):
        await client.chat([{"role": "user", "content": "ping"}])


async def test_client_does_not_duplicate_chat_completions_path(monkeypatch):
    posted_urls = []

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"choices": [{"message": {"content": "OK"}}]}

    class FakeAsyncClient:
        def __init__(self, *, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, *args, **kwargs):
            posted_urls.append(url)
            return FakeResponse()

    monkeypatch.setattr(ai_client.httpx, "AsyncClient", FakeAsyncClient)
    client = OpenAICompatibleClient(
        base_url="https://api.example.com/v1/chat/completions",
        api_key="secret",
        model="gpt-compatible",
        timeout_seconds=30,
    )

    result = await client.chat([{"role": "user", "content": "ping"}])

    assert result.content == "OK"
    assert posted_urls == ["https://api.example.com/v1/chat/completions"]
