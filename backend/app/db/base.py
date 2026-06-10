"""
数据库基础配置模块
提供 SQLAlchemy Base 类和通用的数据库配置
"""
from sqlalchemy.ext.declarative import declarative_base

# 创建 SQLAlchemy 基类
Base = declarative_base()


def import_all_models() -> None:
    """注册所有模型到 Base.metadata，供 Alembic 和测试建表使用。"""
    import app.models.ai  # noqa: F401
    import app.models.album  # noqa: F401
    import app.models.comment  # noqa: F401
    import app.models.event  # noqa: F401
    import app.models.family_settings  # noqa: F401
    import app.models.like  # noqa: F401
    import app.models.media  # noqa: F401
    import app.models.notification  # noqa: F401
    import app.models.post  # noqa: F401
    import app.models.user  # noqa: F401
