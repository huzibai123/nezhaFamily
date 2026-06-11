"""
OpenAI-compatible AI 客户端
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import urlparse, urlunparse

import httpx


class AIProviderError(Exception):
    """模型供应商调用失败。"""

    def __init__(self, message: str, *, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class AIChatResult:
    content: str
    raw: dict[str, Any]


class OpenAICompatibleClient:
    """最小 OpenAI-compatible chat completions 客户端。"""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: int,
    ) -> None:
        self.base_url = _normalize_base_url(base_url)
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.6,
        max_tokens: int = 300,
    ) -> AIChatResult:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(url, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            raise AIProviderError("模型请求超时") from exc
        except httpx.HTTPError as exc:
            raise AIProviderError(f"模型请求失败: {exc}") from exc

        if response.status_code >= 400:
            message = _extract_error_message(response)
            raise AIProviderError(message, status_code=response.status_code)

        try:
            data = response.json()
        except ValueError as exc:
            raise AIProviderError("模型响应不是有效 JSON") from exc

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIProviderError("模型响应格式不兼容") from exc

        if not isinstance(content, str) or not content.strip():
            raise AIProviderError("模型返回了空内容")

        return AIChatResult(content=content.strip(), raw=data)


def _extract_error_message(response: httpx.Response) -> str:
    try:
        data = response.json()
        error = data.get("error")
        if isinstance(error, dict):
            message = error.get("message") or error.get("code")
            if message:
                return str(message)
        if isinstance(data.get("message"), str):
            return data["message"]
    except ValueError:
        pass
    return f"模型服务返回 HTTP {response.status_code}"


def _normalize_base_url(value: str) -> str:
    cleaned = value.strip().rstrip("/")
    parsed = urlparse(cleaned)
    path = parsed.path.rstrip("/")
    if path.endswith("/chat/completions"):
        path = path.removesuffix("/chat/completions").rstrip("/")
    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))
