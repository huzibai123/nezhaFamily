"""
媒体路径与私有访问签名工具。
"""

import base64
import hashlib
import hmac
import time
from pathlib import Path
from typing import Any, Optional

from app.core.config import settings

MEDIA_URL_PREFIX = "/media/"
MEDIA_ROOT = Path(settings.MEDIA_ROOT).expanduser().resolve()
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)


def strip_media_query(url: Optional[str]) -> Optional[str]:
    """去掉媒体 URL 上的签名查询参数，用于数据库持久化。"""
    if not url:
        return url
    path = url.split("?", 1)[0]
    return path


def is_local_media_url(url: Optional[str]) -> bool:
    """判断是否为本应用本地媒体 URL。"""
    if not url:
        return False
    return strip_media_query(url).startswith(MEDIA_URL_PREFIX)


def raw_media_url(url: Optional[str]) -> Optional[str]:
    """归一化为数据库中保存的原始媒体路径。"""
    if not is_local_media_url(url):
        return url
    return strip_media_query(url)


def _signature_payload(path: str, expires_at: int) -> bytes:
    return f"{path}:{expires_at}".encode("utf-8")


def _sign(path: str, expires_at: int) -> str:
    digest = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        _signature_payload(path, expires_at),
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def create_media_token(path: str, expires_at: Optional[int] = None) -> str:
    """生成包含过期时间的媒体访问 token。"""
    normalized_path = strip_media_query(path) or path
    expires = expires_at or int(time.time()) + settings.MEDIA_SIGNED_URL_EXPIRE_SECONDS
    return f"{expires}.{_sign(normalized_path, expires)}"


def verify_media_token(path: str, token: Optional[str]) -> bool:
    """校验媒体访问 token 是否有效且未过期。"""
    if not token or "." not in token:
        return False

    expires_text, supplied_signature = token.split(".", 1)
    try:
        expires_at = int(expires_text)
    except ValueError:
        return False

    if expires_at < int(time.time()):
        return False

    normalized_path = strip_media_query(path) or path
    expected_signature = _sign(normalized_path, expires_at)
    return hmac.compare_digest(expected_signature, supplied_signature)


def signed_media_url(url: Optional[str]) -> Optional[str]:
    """把本地媒体 URL 转为短期签名 URL；非本地 URL 原样返回。"""
    if not is_local_media_url(url):
        return url

    raw_url = raw_media_url(url)
    token = create_media_token(raw_url)
    return f"{raw_url}?token={token}"


MEDIA_URL_KEYS = {
    "url",
    "thumbnail",
    "thumbnail_url",
    "background_image_url",
    "logo_url",
}


def transform_media_urls(value: Any, transform) -> Any:
    """递归转换结构化数据中的媒体 URL 字段。"""
    if isinstance(value, list):
        return [transform_media_urls(item, transform) for item in value]
    if isinstance(value, dict):
        transformed: dict[str, Any] = {}
        for key, item in value.items():
            if key in MEDIA_URL_KEYS and isinstance(item, str):
                transformed[key] = transform(item)
            else:
                transformed[key] = transform_media_urls(item, transform)
        return transformed
    return value


def raw_media_value_urls(value: Any) -> Any:
    """递归清理结构化数据中的临时媒体签名。"""
    return transform_media_urls(value, raw_media_url)


def signed_media_value_urls(value: Any) -> Any:
    """递归签名结构化数据中的本地媒体 URL。"""
    return transform_media_urls(value, signed_media_url)


def normalize_media_item_for_storage(item: dict[str, Any]) -> dict[str, Any]:
    """清理媒体项中的临时签名，避免过期 URL 写入数据库。"""
    return raw_media_value_urls(item)


def sign_media_item_for_response(item: dict[str, Any]) -> dict[str, Any]:
    """给媒体项中的可访问 URL 添加短期签名。"""
    return signed_media_value_urls(item)


def media_storage_path(file_path: str) -> Path:
    """把相对媒体路径解析为安全的磁盘路径。"""
    relative_path = Path(file_path)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError("unsafe_media_path")

    full_path = (MEDIA_ROOT / relative_path).resolve()
    full_path.relative_to(MEDIA_ROOT.resolve())
    return full_path


def media_path_from_url(url_or_path: str) -> str:
    """把 /media/foo.jpg 或 foo.jpg 归一为相对磁盘路径。"""
    path = strip_media_query(url_or_path) or url_or_path
    if path.startswith(MEDIA_URL_PREFIX):
        return path[len(MEDIA_URL_PREFIX) :]
    return path.lstrip("/")
