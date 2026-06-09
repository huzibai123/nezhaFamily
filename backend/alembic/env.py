"""
Alembic 环境配置文件
负责数据库连接和迁移执行
"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# 将项目根目录添加到 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入 Base 并显式注册所有模型
from app.db.base import Base, import_all_models
from app.core.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# 从 Settings 读取数据库 URL，覆盖 alembic.ini 中的配置。
database_url = settings.DATABASE_URL
# 转换为同步 URL（Alembic 不支持异步）
if "asyncpg" in database_url:
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
import_all_models()
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    在离线模式下运行迁移
    不需要数据库连接，直接生成 SQL 语句
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    在在线模式下运行迁移
    需要创建数据库引擎并建立连接
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
