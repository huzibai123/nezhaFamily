"""
数据库模块
提供数据库连接、会话管理和基础配置
"""
from importlib import import_module
from typing import Any

_DB_EXPORTS = {
    "Base": "app.db.base",
    "import_all_models": "app.db.base",
    "get_db": "app.db.session",
    "AsyncSessionLocal": "app.db.session",
    "engine": "app.db.session",
}

__all__ = list(_DB_EXPORTS)


def __getattr__(name: str) -> Any:
    """按需导出数据库对象，避免导入 Base 时初始化 Session。"""
    module_name = _DB_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    value = getattr(import_module(module_name), name)
    globals()[name] = value
    return value
