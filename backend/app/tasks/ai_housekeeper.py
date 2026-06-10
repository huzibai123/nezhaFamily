"""
AI 家庭管家异步任务
"""
from uuid import UUID

from app.db.session import AsyncSessionLocal
from app.tasks import celery_app
from app.services.ai_housekeeper import (
    generate_ai_comment_for_post,
    mark_ai_job_failed,
    run_album_suggestions,
    run_history_learning,
)


@celery_app.task(bind=True, max_retries=0)
def generate_ai_comment(self, post_id: str) -> dict:
    """为新帖子生成 AI 自动评论。"""
    import asyncio

    async def _run() -> dict:
        async with AsyncSessionLocal() as db:
            try:
                comment = await generate_ai_comment_for_post(db, UUID(post_id))
                await db.commit()
                return {"created": bool(comment), "comment_id": str(comment.id) if comment else None}
            except Exception:
                await db.rollback()
                raise

    return asyncio.run(_run())


@celery_app.task(bind=True, max_retries=0)
def run_ai_history_learning(self, job_id: str) -> dict:
    """执行历史学习任务。"""
    import asyncio

    async def _run() -> dict:
        parsed_job_id = UUID(job_id)
        async with AsyncSessionLocal() as db:
            try:
                await run_history_learning(db, parsed_job_id)
                await db.commit()
                return {"job_id": job_id}
            except Exception as exc:
                await db.rollback()
                await mark_ai_job_failed(db, parsed_job_id, exc)
                await db.commit()
                raise

    return asyncio.run(_run())


@celery_app.task(bind=True, max_retries=0)
def run_ai_album_suggestions(self, job_id: str) -> dict:
    """生成待管理员确认的 AI 相册整理建议。"""
    import asyncio

    async def _run() -> dict:
        parsed_job_id = UUID(job_id)
        async with AsyncSessionLocal() as db:
            try:
                await run_album_suggestions(db, parsed_job_id)
                await db.commit()
                return {"job_id": job_id}
            except Exception as exc:
                await db.rollback()
                await mark_ai_job_failed(db, parsed_job_id, exc)
                await db.commit()
                raise

    return asyncio.run(_run())
