"""
Pytest 配置文件
提供测试所需的 fixtures（测试数据库、测试客户端、测试用户等）
"""

import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.db.base import Base, import_all_models
from app.db.session import get_db
from app.models.user import User
from app.core.security import get_password_hash
from app.tasks import ai_housekeeper as ai_tasks
from app.api import media as media_api

import_all_models()


# 测试数据库 URL（使用独立的测试数据库，避免污染开发数据）
# 根据环境自动选择主机名（容器内用 postgres，本地用 localhost）
DB_HOST = os.getenv(
    "TEST_DB_HOST", "postgres" if os.path.exists("/.dockerenv") else "localhost"
)
TEST_DATABASE_URL = f"postgresql+asyncpg://nezha_user:nezha_dev_password@{DB_HOST}:5432/nezha_family_test"


class _ImmediateTaskStub:
    """Small stand-in for Celery AsyncResult used by API tests."""

    id = "test-task"


def _task_delay_stub(*args, **kwargs):
    return _ImmediateTaskStub()


@pytest.fixture(autouse=True)
def disable_celery_tasks(monkeypatch):
    """Keep API tests focused on request behavior instead of Redis/Celery availability."""
    monkeypatch.setattr(media_api.compress_image, "delay", _task_delay_stub)
    monkeypatch.setattr(ai_tasks.generate_ai_comment, "delay", _task_delay_stub)
    monkeypatch.setattr(ai_tasks.run_ai_album_suggestions, "delay", _task_delay_stub)
    monkeypatch.setattr(ai_tasks.run_ai_history_learning, "delay", _task_delay_stub)


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """创建测试数据库引擎（每个测试函数独立）"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,  # 测试时关闭 SQL 日志
        future=True,
    )

    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # 清空旧数据
        await conn.run_sync(Base.metadata.create_all)  # 创建表结构

    yield engine

    # 测试结束后清理
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    数据库会话 fixture
    每个测试函数获得独立的数据库会话，测试结束后回滚
    """
    AsyncTestSession = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with AsyncTestSession() as session:
        yield session
        await session.rollback()  # 测试结束回滚，保持数据库干净


@pytest_asyncio.fixture(scope="function")
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    测试客户端 fixture
    提供 httpx.AsyncClient，自动注入测试数据库会话
    """

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_admin(db: AsyncSession) -> User:
    """
    创建测试管理员用户
    用于注册时需要邀请码的场景
    """
    admin = User(
        username="testadmin",
        email="admin@test.com",
        password_hash=get_password_hash("admin123456"),
        role="admin",
        invite_code="TEST_ADMIN_INVITE",
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> User:
    """
    创建普通测试用户
    用于需要已登录用户的测试场景
    """
    user = User(
        username="testuser",
        email="user@test.com",
        password_hash=get_password_hash("user123456"),
        role="member",
        invite_code=None,
        invited_by=None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
