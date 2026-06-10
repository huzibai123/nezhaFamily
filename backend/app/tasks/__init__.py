"""
Celery 异步任务模块
用于处理耗时操作（图片压缩、视频转码等）
"""
from celery import Celery
from app.core.config import settings

# 创建 Celery 实例
celery_app = Celery(
    "nezha_family",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
)


# 导入具体的任务（必须导入，让 Celery worker 能发现这些任务）
from app.tasks.media_processing import compress_image, generate_thumbnail  # noqa: E402
from app.tasks.ai_housekeeper import (  # noqa: E402
    generate_ai_comment,
    run_ai_album_suggestions,
    run_ai_history_learning,
)

__all__ = [
    "celery_app",
    "compress_image",
    "generate_thumbnail",
    "generate_ai_comment",
    "run_ai_album_suggestions",
    "run_ai_history_learning",
]
