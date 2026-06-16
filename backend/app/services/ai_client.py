"""
OpenAI-compatible AI 客户端
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Optional
from urllib.parse import urlparse, urlunparse

import httpx

AIWireAPI = Literal["chat_completions", "responses"]


class AIProviderError(Exception):
    """模型供应商调用失败。

    message 为对外可暴露/落库的提示，只含状态码 + 通用中文，不含上游响应正文。
    detail 为仅供内部判断的细节（如上游错误片段），不会进入 str(exc)，
    用于诸如 responses fallback 的判定，避免半盲 SSRF 数据外泄。
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        detail: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


@dataclass
class AIChatResult:
    content: str
    raw: dict[str, Any]


class OpenAICompatibleClient:
    """最小 OpenAI-compatible 客户端。"""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: int,
        wire_api: AIWireAPI = "chat_completions",
        reasoning_effort: Optional[str] = None,
        disable_response_storage: bool = False,
    ) -> None:
        self.base_url = _normalize_base_url(base_url)
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.wire_api: AIWireAPI = wire_api if wire_api in {"chat_completions", "responses"} else "chat_completions"
        self.reasoning_effort = reasoning_effort.strip() if isinstance(reasoning_effort, str) else None
        self.disable_response_storage = disable_response_storage

    async def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.6,
        max_tokens: int = 300,
    ) -> AIChatResult:
        if self.wire_api == "responses":
            return await self._responses(messages, max_tokens=max_tokens)
        return await self._chat_completions(messages, temperature=temperature, max_tokens=max_tokens)

    async def _chat_completions(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float,
        max_tokens: int,
    ) -> AIChatResult:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        data = await self._post_json(url, payload)

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIProviderError("模型响应格式不兼容") from exc

        return _result_from_content(content, data)

    async def _responses(
        self,
        messages: list[dict[str, Any]],
        *,
        max_tokens: int,
    ) -> AIChatResult:
        url = f"{self.base_url}/responses"
        instructions, input_items = _messages_to_responses_payload(messages)
        payload: dict[str, Any] = {
            "model": self.model,
            "input": input_items,
            "max_output_tokens": max_tokens,
        }
        if instructions:
            payload["instructions"] = instructions
        if self.reasoning_effort:
            payload["reasoning"] = {"effort": self.reasoning_effort}
        if self.disable_response_storage:
            payload["store"] = False

        data = await self._post_json_with_responses_fallback(url, payload)
        content = _extract_responses_content(data)
        return _result_from_content(content, data)

    async def _post_json_with_responses_fallback(
        self,
        url: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            return await self._post_json(url, payload)
        except AIProviderError as exc:
            # 用不对外的 detail 字段判断是否触发 fallback，避免把上游正文回显给用户
            if exc.status_code != 400 or "max_output_tokens" not in (exc.detail or ""):
                raise
            fallback_payload = dict(payload)
            fallback_payload.pop("max_output_tokens", None)
            return await self._post_json(url, fallback_payload)

    async def _post_json(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(url, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            raise AIProviderError("模型请求超时") from exc
        except httpx.HTTPError as exc:
            raise AIProviderError(f"模型请求失败: {exc}") from exc

        if response.status_code >= 400:
            message = _generic_http_error_message(response.status_code)
            raise AIProviderError(
                message,
                status_code=response.status_code,
                detail=_extract_error_detail(response),
            )

        try:
            return response.json()
        except ValueError as exc:
            raise AIProviderError(
                _non_json_message(response),
                status_code=response.status_code,
                detail=_extract_error_detail(response),
            ) from exc


def _result_from_content(content: Any, raw: dict[str, Any]) -> AIChatResult:
    if isinstance(content, list):
        content = "\n".join(str(item) for item in content if item)
    if not isinstance(content, str) or not content.strip():
        raise AIProviderError("模型返回了空内容")
    return AIChatResult(content=content.strip(), raw=raw)


def _messages_to_responses_payload(messages: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    instructions: list[str] = []
    input_items: list[dict[str, Any]] = []
    for message in messages:
        role = str(message.get("role") or "user")
        content = message.get("content", "")
        text = _text_from_content(content)
        response_content = _responses_content(content)
        if not text.strip() and not (
            isinstance(response_content, list) and len(response_content) > 0
        ):
            continue
        if role in {"system", "developer"}:
            instructions.append(text)
            continue
        input_role = role if role in {"user", "assistant"} else "user"
        input_items.append({"role": input_role, "content": response_content})
    return "\n\n".join(instructions), input_items


def _text_from_content(content: Any) -> str:
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if not isinstance(part, dict):
                parts.append(str(part))
                continue
            text = part.get("text")
            if isinstance(text, str):
                parts.append(text)
        return "\n".join(part for part in parts if part.strip())
    return str(content)


def _responses_content(content: Any) -> str | list[dict[str, Any]]:
    if not isinstance(content, list):
        return str(content)

    response_parts: list[dict[str, Any]] = []
    for part in content:
        if not isinstance(part, dict):
            text = str(part)
            if text.strip():
                response_parts.append({"type": "input_text", "text": text})
            continue

        part_type = part.get("type")
        if part_type in {"text", "input_text"}:
            text = str(part.get("text") or "")
            if text.strip():
                response_parts.append({"type": "input_text", "text": text})
            continue

        if part_type == "image_url":
            image_url = part.get("image_url")
            if isinstance(image_url, dict):
                image_url = image_url.get("url")
            if isinstance(image_url, str) and image_url.strip():
                response_parts.append({"type": "input_image", "image_url": image_url})
            continue

        if part_type == "input_image":
            image_part: dict[str, Any] = {"type": "input_image"}
            for key in ("image_url", "file_id"):
                value = part.get(key)
                if isinstance(value, str) and value.strip():
                    image_part[key] = value
            if len(image_part) > 1:
                response_parts.append(image_part)

    return response_parts or _text_from_content(content)


def _extract_responses_content(data: dict[str, Any]) -> str:
    output_text = data.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    parts: list[str] = []
    output_items = data.get("output")
    if isinstance(output_items, list):
        for output_item in output_items:
            if not isinstance(output_item, dict):
                continue
            content_items = output_item.get("content")
            if isinstance(content_items, list):
                for content_item in content_items:
                    if not isinstance(content_item, dict):
                        continue
                    text = content_item.get("text")
                    if isinstance(text, str) and text.strip():
                        parts.append(text)
            text = output_item.get("text")
            if isinstance(text, str) and text.strip():
                parts.append(text)

    if parts:
        return "\n".join(parts)
    raise AIProviderError("模型响应格式不兼容")


def _generic_http_error_message(status_code: int) -> str:
    """对外/落库的错误提示：只含状态码 + 通用中文，不回显上游响应正文。"""
    if 400 <= status_code < 500:
        category = "请求被拒绝（4xx）"
    elif 500 <= status_code < 600:
        category = "上游服务异常（5xx）"
    else:
        category = "上游返回异常"
    return f"模型服务返回 HTTP {status_code}：{category}"


def _extract_error_detail(response: httpx.Response) -> Optional[str]:
    """提取仅供内部判断的上游错误片段（如 max_output_tokens），不对外暴露。"""
    try:
        data = response.json()
        error = data.get("error")
        if isinstance(error, dict):
            message = error.get("message") or error.get("code")
            if message:
                return str(message)
        for key in ("message", "detail"):
            if isinstance(data.get(key), str):
                return data[key]
    except ValueError:
        pass
    text = getattr(response, "text", "")
    if isinstance(text, str) and text.strip():
        return " ".join(text.split())[:200]
    return None


def _non_json_message(response: httpx.Response) -> str:
    content_type = _response_content_type(response) or "unknown content-type"
    message = f"模型响应不是有效 JSON（HTTP {response.status_code}，{content_type}）"
    text = getattr(response, "text", "")
    if isinstance(text, str) and "<html" in text.lower():
        message += "。请检查 Base URL 是否缺少 /v1"
    return message


def _response_content_type(response: httpx.Response) -> str:
    headers = getattr(response, "headers", {}) or {}
    if hasattr(headers, "get"):
        return str(headers.get("content-type") or headers.get("Content-Type") or "")
    return ""


def _normalize_base_url(value: str) -> str:
    cleaned = value.strip().rstrip("/")
    parsed = urlparse(cleaned)
    path = parsed.path.rstrip("/")
    for suffix in ("/chat/completions", "/responses"):
        if path.endswith(suffix):
            path = path.removesuffix(suffix).rstrip("/")
            break
    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))
