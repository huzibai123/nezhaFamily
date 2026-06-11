"""
Celery 任务运行时配置测试。
"""

from app.tasks import (
    AI_TASK_OPTIONS,
    AI_TASK_SOFT_TIME_LIMIT_SECONDS,
    AI_TASK_TIME_LIMIT_SECONDS,
    CELERY_TASK_SOFT_TIME_LIMIT_SECONDS,
    CELERY_TASK_TIME_LIMIT_SECONDS,
    CELERY_WORKER_PREFETCH_MULTIPLIER,
    IMAGE_TASK_OPTIONS,
    IMAGE_TASK_SOFT_TIME_LIMIT_SECONDS,
    IMAGE_TASK_TIME_LIMIT_SECONDS,
    celery_app,
)
from app.tasks import media_processing


def test_celery_global_runtime_limits_are_configured():
    assert celery_app.conf.task_time_limit == CELERY_TASK_TIME_LIMIT_SECONDS
    assert celery_app.conf.task_soft_time_limit == CELERY_TASK_SOFT_TIME_LIMIT_SECONDS
    assert celery_app.conf.worker_prefetch_multiplier == CELERY_WORKER_PREFETCH_MULTIPLIER
    assert CELERY_WORKER_PREFETCH_MULTIPLIER == 1


def test_image_tasks_keep_retries_and_have_timeouts():
    for task in (media_processing.compress_image, media_processing.generate_thumbnail):
        assert task.max_retries == IMAGE_TASK_OPTIONS["max_retries"]
        assert task.max_retries == 3
        assert task.time_limit == IMAGE_TASK_TIME_LIMIT_SECONDS
        assert task.soft_time_limit == IMAGE_TASK_SOFT_TIME_LIMIT_SECONDS


def test_ai_task_defaults_disable_auto_retry_but_keep_timeouts():
    assert AI_TASK_OPTIONS["max_retries"] == 0
    assert AI_TASK_OPTIONS["autoretry_for"] == ()
    assert AI_TASK_OPTIONS["retry_backoff"] is False
    assert AI_TASK_OPTIONS["time_limit"] == AI_TASK_TIME_LIMIT_SECONDS
    assert AI_TASK_OPTIONS["soft_time_limit"] == AI_TASK_SOFT_TIME_LIMIT_SECONDS
