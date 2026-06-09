"""
数据库会话管理模块
提供异步 Session 工厂和依赖注入函数
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

# 统一从 Settings 读取数据库 URL，避免 API、迁移和任务连接到不同数据库。
DATABASE_URL = settings.DATABASE_URL

# 创建异步引擎
engine_options = {
    "echo": settings.DEBUG,
    "future": True,
    "pool_pre_ping": True,
}
if "sqlite" in DATABASE_URL:
    engine_options["poolclass"] = NullPool

engine = create_async_engine(DATABASE_URL, **engine_options)

# 创建异步 Session 工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI 依赖注入函数，用于获取数据库会话

    使用示例：
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
