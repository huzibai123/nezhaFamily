"""
OpenAI-compatible AI 客户端测试
"""

import pytest

from app.services import ai_client
from app.services.ai_client import AIProviderError, OpenAICompatibleClient


async def test_client_wraps_success_response_invalid_json(monkeypatch):
    class FakeResponse:
        status_code = 200
        headers = {"content-type": "text/plain"}
        text = "not-json"

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


async def test_client_non_json_html_response_hints_missing_v1(monkeypatch):
    class FakeResponse:
        status_code = 200
        headers = {"content-type": "text/html; charset=utf-8"}
        text = "<!doctype html><html><body>site shell</body></html>"

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
        base_url="https://api.example.com",
        api_key="secret",
        model="gpt-compatible",
        timeout_seconds=30,
    )

    with pytest.raises(AIProviderError, match="缺少 /v1"):
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


async def test_client_supports_responses_api(monkeypatch):
    requests = []

    class FakeResponse:
        status_code = 200
        headers = {"content-type": "application/json"}

        def json(self):
            return {
                "id": "resp_123",
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": "OK from responses"}],
                    }
                ],
            }

    class FakeAsyncClient:
        def __init__(self, *, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, *args, **kwargs):
            requests.append({"url": url, "kwargs": kwargs})
            return FakeResponse()

    monkeypatch.setattr(ai_client.httpx, "AsyncClient", FakeAsyncClient)
    client = OpenAICompatibleClient(
        base_url="https://api.example.com/v1/responses",
        api_key="secret",
        model="gpt-compatible",
        timeout_seconds=30,
        wire_api="responses",
        reasoning_effort="low",
        disable_response_storage=True,
    )

    result = await client.chat(
        [
            {"role": "system", "content": "Only say OK"},
            {"role": "user", "content": "ping"},
        ],
        temperature=0,
        max_tokens=20,
    )

    assert result.content == "OK from responses"
    assert requests[0]["url"] == "https://api.example.com/v1/responses"
    payload = requests[0]["kwargs"]["json"]
    assert payload["model"] == "gpt-compatible"
    assert payload["max_output_tokens"] == 20
    assert payload["store"] is False
    assert payload["reasoning"] == {"effort": "low"}
    assert payload["instructions"] == "Only say OK"
    assert payload["input"] == [{"role": "user", "content": "ping"}]


async def test_client_retries_responses_without_unsupported_max_output_tokens(monkeypatch):
    requests = []

    class FakeErrorResponse:
        status_code = 400
        headers = {"content-type": "application/json"}

        def json(self):
            return {"detail": "Unsupported parameter: max_output_tokens"}

    class FakeSuccessResponse:
        status_code = 200
        headers = {"content-type": "application/json"}

        def json(self):
            return {"output_text": "OK after fallback"}

    class FakeAsyncClient:
        def __init__(self, *, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, *args, **kwargs):
            requests.append({"url": url, "kwargs": kwargs})
            return FakeErrorResponse() if len(requests) == 1 else FakeSuccessResponse()

    monkeypatch.setattr(ai_client.httpx, "AsyncClient", FakeAsyncClient)
    client = OpenAICompatibleClient(
        base_url="https://api.example.com/v1",
        api_key="secret",
        model="gpt-compatible",
        timeout_seconds=30,
        wire_api="responses",
    )

    result = await client.chat([{"role": "user", "content": "ping"}], max_tokens=20)

    assert result.content == "OK after fallback"
    assert len(requests) == 2
    assert requests[0]["kwargs"]["json"]["max_output_tokens"] == 20
    assert "max_output_tokens" not in requests[1]["kwargs"]["json"]
