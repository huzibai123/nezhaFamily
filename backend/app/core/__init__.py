"""
核心模块初始化
"""
from importlib import import_module
from typing import Any

_CORE_EXPORTS = {
    "settings": "app.core.config",
    "get_password_hash": "app.core.security",
    "verify_password": "app.core.security",
    "create_access_token": "app.core.security",
    "decode_access_token": "app.core.security",
    "get_current_user_id": "app.core.security",
}

__all__ = list(_CORE_EXPORTS)


def __getattr__(name: str) -> Any:
    """按需导出核心对象，避免包初始化时触发循环导入。"""
    module_name = _CORE_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    value = getattr(import_module(module_name), name)
    globals()[name] = value
    return value
