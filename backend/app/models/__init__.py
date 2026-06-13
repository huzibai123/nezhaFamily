"""
数据库模型包
导出所有模型供其他模块使用。

不要在包初始化时直接导入所有模型。单个模型模块会导入 app.db.base.Base，
而 app.db.base 又需要导入模型来注册 metadata；如果这里 eager import 所有
模型，`import app.models.user` 这类直接导入路径会触发循环导入。
"""
from importlib import import_module
from typing import Any

_MODEL_EXPORTS = {
    "AIProviderConfig": "app.models.ai",
    "AIPersona": "app.models.ai",
    "AIJob": "app.models.ai",
    "AIContentInsight": "app.models.ai",
    "AIProfile": "app.models.ai",
    "AIAlbumSuggestion": "app.models.ai",
    "AIReportDraft": "app.models.ai",
    "User": "app.models.user",
    "Post": "app.models.post",
    "Comment": "app.models.comment",
    "Like": "app.models.like",
    "PostLike": "app.models.like",
    "CommentLike": "app.models.like",
    "MediaFile": "app.models.media",
    "MediaFavorite": "app.models.media",
    "Album": "app.models.album",
    "album_media": "app.models.album",
    "Event": "app.models.event",
    "EventType": "app.models.event",
    "FamilySettings": "app.models.family_settings",
    "Notification": "app.models.notification",
}

__all__ = list(_MODEL_EXPORTS)


def __getattr__(name: str) -> Any:
    """按需导出模型，保持 `from app.models import User` 兼容。"""
    module_name = _MODEL_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    value = getattr(import_module(module_name), name)
    globals()[name] = value
    return value
