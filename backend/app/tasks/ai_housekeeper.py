"""
AI 家庭管家异步任务
"""
from collections.abc import Awaitable, Callable
from typing import TypeVar
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.tasks import ai_task
from app.services.ai_housekeeper import (
    generate_ai_comment_for_post,
    mark_ai_job_failed,
    run_album_suggestions,
    run_history_learning,
)

TaskResult = TypeVar("TaskResult")


def _create_ai_task_session_factory() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    # Celery tasks use asyncio.run() per invocation; do not reuse asyncpg pooled
    # connections across those short-lived event loops.
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        future=True,
        pool_pre_ping=True,
        poolclass=NullPool,
    )
    return engine, async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def _with_ai_task_session(
    handler: Callable[[AsyncSession], Awaitable[TaskResult]],
) -> TaskResult:
    engine, session_factory = _create_ai_task_session_factory()
    try:
        async with session_factory() as db:
            return await handler(db)
    finally:
        await engine.dispose()


@ai_task(bind=True)
def generate_ai_comment(self, post_id: str) -> dict:
    """为新帖子生成 AI 自动评论。"""
    import asyncio

    async def _run() -> dict:
        async def _handle(db: AsyncSession) -> dict:
            try:
                comment = await generate_ai_comment_for_post(db, UUID(post_id))
                await db.commit()
                return {"created": bool(comment), "comment_id": str(comment.id) if comment else None}
            except Exception:
                await db.rollback()
                raise

        return await _with_ai_task_session(_handle)

    return asyncio.run(_run())


@ai_task(bind=True)
def run_ai_history_learning(self, job_id: str) -> dict:
    """执行历史学习任务。"""
    import asyncio

    async def _run() -> dict:
        parsed_job_id = UUID(job_id)

        async def _handle(db: AsyncSession) -> dict:
            try:
                await run_history_learning(db, parsed_job_id)
                await db.commit()
                return {"job_id": job_id}
            except Exception as exc:
                await db.rollback()
                await mark_ai_job_failed(db, parsed_job_id, exc)
                await db.commit()
                raise

        return await _with_ai_task_session(_handle)

    return asyncio.run(_run())


@ai_task(bind=True)
def run_ai_album_suggestions(self, job_id: str) -> dict:
    """生成待管理员确认的 AI 相册整理建议。"""
    import asyncio

    async def _run() -> dict:
        parsed_job_id = UUID(job_id)

        async def _handle(db: AsyncSession) -> dict:
            try:
                await run_album_suggestions(db, parsed_job_id)
                await db.commit()
                return {"job_id": job_id}
            except Exception as exc:
                await db.rollback()
                await mark_ai_job_failed(db, parsed_job_id, exc)
                await db.commit()
                raise

        return await _with_ai_task_session(_handle)

    return asyncio.run(_run())
