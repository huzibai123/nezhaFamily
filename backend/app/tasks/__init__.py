"""
Celery 异步任务模块
用于处理耗时操作（图片压缩、视频转码等）
"""
import os

from celery import Celery
from app.core.config import settings
from app.db.base import import_all_models


import_all_models()


def _env_int(name: str, default: int) -> int:
    """Read integer Celery runtime knobs without involving app Settings ownership."""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


CELERY_TASK_TIME_LIMIT_SECONDS = _env_int(
    "CELERY_TASK_TIME_LIMIT", settings.CELERY_TASK_TIME_LIMIT
)
CELERY_TASK_SOFT_TIME_LIMIT_SECONDS = _env_int(
    "CELERY_TASK_SOFT_TIME_LIMIT", settings.CELERY_TASK_SOFT_TIME_LIMIT
)
CELERY_WORKER_PREFETCH_MULTIPLIER = _env_int("CELERY_WORKER_PREFETCH_MULTIPLIER", 1)

IMAGE_TASK_TIME_LIMIT_SECONDS = _env_int(
    "CELERY_IMAGE_TASK_TIME_LIMIT", CELERY_TASK_TIME_LIMIT_SECONDS
)
IMAGE_TASK_SOFT_TIME_LIMIT_SECONDS = _env_int(
    "CELERY_IMAGE_TASK_SOFT_TIME_LIMIT", CELERY_TASK_SOFT_TIME_LIMIT_SECONDS
)
AI_TASK_TIME_LIMIT_SECONDS = _env_int("CELERY_AI_TASK_TIME_LIMIT", 180)
AI_TASK_SOFT_TIME_LIMIT_SECONDS = _env_int("CELERY_AI_TASK_SOFT_TIME_LIMIT", 150)
MEDIA_CLEANUP_TASK_TIME_LIMIT_SECONDS = _env_int(
    "CELERY_MEDIA_CLEANUP_TASK_TIME_LIMIT", 3600
)
MEDIA_CLEANUP_TASK_SOFT_TIME_LIMIT_SECONDS = _env_int(
    "CELERY_MEDIA_CLEANUP_TASK_SOFT_TIME_LIMIT", 3300
)

IMAGE_TASK_OPTIONS = {
    "max_retries": 3,
    "time_limit": IMAGE_TASK_TIME_LIMIT_SECONDS,
    "soft_time_limit": IMAGE_TASK_SOFT_TIME_LIMIT_SECONDS,
}

AI_TASK_OPTIONS = {
    "max_retries": 0,
    "autoretry_for": (),
    "retry_backoff": False,
    "time_limit": AI_TASK_TIME_LIMIT_SECONDS,
    "soft_time_limit": AI_TASK_SOFT_TIME_LIMIT_SECONDS,
}

MEDIA_CLEANUP_TASK_OPTIONS = {
    "time_limit": MEDIA_CLEANUP_TASK_TIME_LIMIT_SECONDS,
    "soft_time_limit": MEDIA_CLEANUP_TASK_SOFT_TIME_LIMIT_SECONDS,
}

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
    task_time_limit=CELERY_TASK_TIME_LIMIT_SECONDS,
    task_soft_time_limit=CELERY_TASK_SOFT_TIME_LIMIT_SECONDS,
    worker_prefetch_multiplier=CELERY_WORKER_PREFETCH_MULTIPLIER,
)


def ai_task(*task_args, **task_kwargs):
    """Create AI tasks with timeouts and no automatic retry policy."""
    task_options = {**AI_TASK_OPTIONS, **task_kwargs}
    task_options["max_retries"] = 0
    task_options["autoretry_for"] = ()
    task_options["retry_backoff"] = False
    return celery_app.task(*task_args, **task_options)


# 导入具体的任务（必须导入，让 Celery worker 能发现这些任务）
from app.tasks.media_processing import compress_image, generate_thumbnail  # noqa: E402
from app.tasks.ai_housekeeper import (  # noqa: E402
    generate_ai_comment,
    run_ai_album_suggestions,
    run_ai_history_learning,
)

__all__ = [
    "AI_TASK_OPTIONS",
    "AI_TASK_SOFT_TIME_LIMIT_SECONDS",
    "AI_TASK_TIME_LIMIT_SECONDS",
    "CELERY_TASK_SOFT_TIME_LIMIT_SECONDS",
    "CELERY_TASK_TIME_LIMIT_SECONDS",
    "CELERY_WORKER_PREFETCH_MULTIPLIER",
    "IMAGE_TASK_OPTIONS",
    "IMAGE_TASK_SOFT_TIME_LIMIT_SECONDS",
    "IMAGE_TASK_TIME_LIMIT_SECONDS",
    "MEDIA_CLEANUP_TASK_OPTIONS",
    "MEDIA_CLEANUP_TASK_SOFT_TIME_LIMIT_SECONDS",
    "MEDIA_CLEANUP_TASK_TIME_LIMIT_SECONDS",
    "ai_task",
    "celery_app",
    "compress_image",
    "generate_thumbnail",
    "generate_ai_comment",
    "run_ai_album_suggestions",
    "run_ai_history_learning",
]
