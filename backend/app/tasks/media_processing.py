"""
媒体处理 Celery 任务
处理图片压缩、缩略图生成等耗时操作
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID
from PIL import Image
from sqlalchemy import Column, DateTime, MetaData, String, Table, delete, select
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.core.media_utils import MEDIA_ROOT, media_path_from_url

try:
    from app.tasks import IMAGE_TASK_OPTIONS, MEDIA_CLEANUP_TASK_OPTIONS, celery_app
except ImportError:
    from app.tasks import celery_app

    IMAGE_TASK_OPTIONS = {"max_retries": 3}
    MEDIA_CLEANUP_TASK_OPTIONS = {"time_limit": 3600, "soft_time_limit": 3300}

logger = logging.getLogger(__name__)

# 与 API 和 Alembic 使用同一个 Settings 来源。
DATABASE_URL = settings.DATABASE_URL
DEFAULT_MEDIA_TRASH_RETENTION_DAYS = 30

_cleanup_metadata = MetaData()
_media_files_cleanup_table = Table(
    "media_files",
    _cleanup_metadata,
    Column("id", PG_UUID(as_uuid=True), primary_key=True),
    Column("file_path", String(500), nullable=False),
    Column("thumbnail_path", String(500), nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
)

# 为 Celery 任务创建独立的异步引擎和 session 工厂
task_engine = create_async_engine(DATABASE_URL, echo=False, future=True)
TaskAsyncSession = async_sessionmaker(
    task_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@dataclass(frozen=True)
class TrashMediaRecord:
    """待从媒体回收站物理清理的记录。"""

    id: UUID
    file_path: str
    thumbnail_path: str | None = None


class MediaTrashUnavailable(RuntimeError):
    """当前数据库尚不支持媒体回收站清理。"""


def get_media_trash_retention_days(retention_days: int | None = None) -> int:
    """读取媒体回收站保留天数，默认 30 天。"""
    if retention_days is not None:
        if retention_days < 1:
            raise ValueError("retention_days must be at least 1")
        return retention_days

    raw_value = os.getenv("MEDIA_TRASH_RETENTION_DAYS")
    if not raw_value:
        return DEFAULT_MEDIA_TRASH_RETENTION_DAYS

    try:
        parsed_value = int(raw_value)
    except ValueError:
        logger.warning(
            "MEDIA_TRASH_RETENTION_DAYS=%s 无效，回退到默认 %s 天",
            raw_value,
            DEFAULT_MEDIA_TRASH_RETENTION_DAYS,
        )
        return DEFAULT_MEDIA_TRASH_RETENTION_DAYS

    if parsed_value < 1:
        logger.warning(
            "MEDIA_TRASH_RETENTION_DAYS=%s 小于 1，回退到默认 %s 天",
            raw_value,
            DEFAULT_MEDIA_TRASH_RETENTION_DAYS,
        )
        return DEFAULT_MEDIA_TRASH_RETENTION_DAYS

    return parsed_value


def _is_missing_deleted_at_error(exc: SQLAlchemyError) -> bool:
    message = str(exc).lower()
    return "deleted_at" in message and (
        "undefinedcolumn" in message
        or "does not exist" in message
        or "no such column" in message
    )


def _media_disk_path(url_or_path: str) -> Path:
    """把媒体 URL/路径解析为任务内使用的安全磁盘路径。"""
    relative_path = Path(media_path_from_url(url_or_path))
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError("unsafe_media_path")

    media_root = MEDIA_ROOT.resolve()
    full_path = (media_root / relative_path).resolve()
    full_path.relative_to(media_root)
    return full_path


async def fetch_expired_trashed_media(cutoff: datetime) -> list[TrashMediaRecord]:
    """查询超过回收站保留期的软删除媒体记录。"""
    table = _media_files_cleanup_table

    async with TaskAsyncSession() as session:
        try:
            result = await session.execute(
                select(table.c.id, table.c.file_path, table.c.thumbnail_path).where(
                    table.c.deleted_at.is_not(None),
                    table.c.deleted_at < cutoff,
                )
            )
        except SQLAlchemyError as exc:
            await session.rollback()
            if _is_missing_deleted_at_error(exc):
                raise MediaTrashUnavailable(
                    "media_files.deleted_at column is not available"
                ) from exc
            raise

        return [
            TrashMediaRecord(
                id=row.id,
                file_path=row.file_path,
                thumbnail_path=row.thumbnail_path,
            )
            for row in result
        ]


async def delete_expired_trashed_media_records(media_ids: list[UUID]) -> int:
    """删除已完成磁盘清理的媒体数据库记录。"""
    if not media_ids:
        return 0

    table = _media_files_cleanup_table
    async with TaskAsyncSession() as session:
        try:
            result = await session.execute(
                delete(table).where(table.c.id.in_(media_ids))
            )
            await session.commit()
        except SQLAlchemyError as exc:
            await session.rollback()
            if _is_missing_deleted_at_error(exc):
                raise MediaTrashUnavailable(
                    "media_files.deleted_at column is not available"
                ) from exc
            raise

    return result.rowcount or 0


def _delete_media_record_disk_files(record: TrashMediaRecord) -> tuple[int, int]:
    """删除单条媒体记录对应的主文件和缩略图，返回删除/缺失数量。"""
    deleted_count = 0
    missing_count = 0
    paths: list[Path] = []
    seen_paths: set[Path] = set()

    for raw_path in (record.file_path, record.thumbnail_path):
        if not raw_path:
            continue
        disk_path = _media_disk_path(raw_path)
        if disk_path not in seen_paths:
            seen_paths.add(disk_path)
            paths.append(disk_path)

    for disk_path in paths:
        if disk_path.exists() and not disk_path.is_file():
            raise ValueError("unsafe_media_path")

    for disk_path in paths:
        if not disk_path.exists():
            missing_count += 1
            continue
        disk_path.unlink()
        deleted_count += 1

    return deleted_count, missing_count


def delete_expired_trashed_media_files(
    records: list[TrashMediaRecord],
) -> tuple[list[UUID], dict]:
    """删除过期软删除媒体的磁盘文件，返回可删除 DB 记录 ID 与统计信息。"""
    deleted_record_ids: list[UUID] = []
    unsafe_record_ids: list[str] = []
    deleted_files = 0
    missing_files = 0

    for record in records:
        try:
            record_deleted_files, record_missing_files = (
                _delete_media_record_disk_files(record)
            )
        except ValueError:
            logger.warning("媒体回收站清理跳过不安全路径记录：%s", record.id)
            unsafe_record_ids.append(str(record.id))
            continue

        deleted_files += record_deleted_files
        missing_files += record_missing_files
        deleted_record_ids.append(record.id)

    return deleted_record_ids, {
        "candidate_records": len(records),
        "deleted_files": deleted_files,
        "missing_files": missing_files,
        "skipped_records": len(unsafe_record_ids),
        "unsafe_record_ids": unsafe_record_ids,
    }


async def get_media_by_id(media_id: str):
    """
    通过 ID 获取媒体文件记录

    Args:
        media_id: 媒体文件 UUID 字符串

    Returns:
        MediaFile 对象或 None
    """
    from app.models.media import MediaFile

    async with TaskAsyncSession() as session:
        result = await session.execute(
            select(MediaFile).where(MediaFile.id == UUID(media_id))
        )
        return result.scalar_one_or_none()


async def update_media_thumbnail(media_id: str, thumbnail_path: str) -> None:
    """
    更新媒体文件的缩略图路径

    Args:
        media_id: 媒体文件 UUID 字符串
        thumbnail_path: 缩略图相对路径
    """
    from app.models.media import MediaFile

    async with TaskAsyncSession() as session:
        result = await session.execute(
            select(MediaFile).where(MediaFile.id == UUID(media_id))
        )
        media = result.scalar_one_or_none()
        if media:
            media.thumbnail_path = thumbnail_path
            await session.commit()


async def update_media_after_compression(
    media_id: str,
    *,
    file_path: str,
    file_size: int,
    mime_type: str,
    width: int,
    height: int,
) -> None:
    """更新压缩后的媒体主文件元数据。"""
    from app.models.media import MediaFile

    async with TaskAsyncSession() as session:
        result = await session.execute(
            select(MediaFile).where(MediaFile.id == UUID(media_id))
        )
        media = result.scalar_one_or_none()
        if media:
            media.file_path = file_path
            media.file_size = file_size
            media.mime_type = mime_type
            media.width = width
            media.height = height
            await session.commit()


@celery_app.task(bind=True, **IMAGE_TASK_OPTIONS)
def compress_image(self, media_id: str) -> dict:
    """
    压缩图片任务

    如果图片宽度超过 1920px，等比缩放到 1920px
    压缩质量设为 85%，覆盖原文件

    Args:
        media_id: 媒体文件 UUID 字符串

    Returns:
        任务执行结果字典
    """
    import asyncio

    try:
        # 在同步任务中运行异步查询
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            media = loop.run_until_complete(get_media_by_id(media_id))
        finally:
            loop.close()

        if not media:
            logger.warning(f"压缩任务：媒体文件 {media_id} 不存在")
            return {"status": "skipped", "reason": "media_not_found"}

        # 仅处理图片类型
        if media.file_type != "image":
            logger.info(f"压缩任务：{media_id} 不是图片类型，跳过")
            return {"status": "skipped", "reason": "not_image"}

        # 构建文件绝对路径（file_path 存储的是 /media/xxx.jpg）
        try:
            file_path = _media_disk_path(media.file_path)
        except ValueError:
            logger.warning("压缩任务：媒体文件 %s 路径不安全", media_id)
            return {"status": "error", "reason": "unsafe_media_path"}

        if not file_path.exists():
            logger.warning(f"压缩任务：文件 {file_path} 不存在")
            return {"status": "error", "reason": "file_not_found"}

        # 尝试打开图片。主文件路径必须保持稳定，避免上传响应中的 raw_url 失效。
        try:
            with Image.open(file_path) as img:
                original_size = img.size
                image_format = (img.format or "").upper()
                mime_type = Image.MIME.get(
                    image_format, media.mime_type or "image/jpeg"
                )

                preserve_original = image_format in {"GIF", "PNG", "WEBP"}
                next_size = original_size

                # 透明图、动图和 WebP 保留原文件，避免破坏透明度/动画。
                if preserve_original:
                    db_loop = asyncio.new_event_loop()
                    try:
                        asyncio.set_event_loop(db_loop)
                        db_loop.run_until_complete(
                            update_media_after_compression(
                                media_id,
                                file_path=media.file_path,
                                file_size=file_path.stat().st_size,
                                mime_type=mime_type,
                                width=img.width,
                                height=img.height,
                            )
                        )
                    finally:
                        db_loop.close()

                    generate_thumbnail.delay(media_id)
                    return {
                        "status": "success",
                        "original_size": original_size,
                        "file_path": media.file_path,
                        "file_size": file_path.stat().st_size,
                        "mime_type": mime_type,
                        "size": original_size,
                        "compressed": False,
                        "preserved": True,
                    }

                # JPEG 图片可在原路径上等比缩放/优化，但不改 URL。
                max_width = 1920
                if img.width > max_width:
                    ratio = max_width / img.width
                    next_size = (max_width, int(img.height * ratio))
                    img = img.resize(next_size, Image.Resampling.LANCZOS)
                    logger.info(
                        f"压缩任务：{media_id} 从 {original_size} 缩放到 {next_size}"
                    )

                # 转换 RGBA 为 RGB（JPEG 不支持透明度）
                if img.mode == "RGBA":
                    rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[3])
                    img = rgb_img
                elif img.mode not in {"RGB", "L"}:
                    img = img.convert("RGB")

                temp_path = file_path.with_name(
                    f".{file_path.stem}.optimized{file_path.suffix}"
                )
                img.save(temp_path, format="JPEG", quality=85, optimize=True)
                temp_path.replace(file_path)

                compressed_size = file_path.stat().st_size

                db_loop = asyncio.new_event_loop()
                try:
                    asyncio.set_event_loop(db_loop)
                    db_loop.run_until_complete(
                        update_media_after_compression(
                            media_id,
                            file_path=media.file_path,
                            file_size=compressed_size,
                            mime_type="image/jpeg",
                            width=img.width,
                            height=img.height,
                        )
                    )
                finally:
                    db_loop.close()

                generate_thumbnail.delay(media_id)

                logger.info(f"压缩任务：{media_id} 已原地更新主文件 {file_path}")
                return {
                    "status": "success",
                    "original_size": original_size,
                    "file_path": media.file_path,
                    "file_size": compressed_size,
                    "mime_type": "image/jpeg",
                    "size": (img.width, img.height),
                    "compressed": next_size != original_size,
                }

        except Exception as e:
            logger.error(f"压缩任务：处理图片 {media_id} 失败: {str(e)}")
            return {"status": "error", "reason": "pillow_error", "detail": str(e)}

    except Exception as e:
        logger.error(f"压缩任务：执行失败 {media_id}: {str(e)}")
        # 重试机制
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)
        return {"status": "error", "reason": "task_failed", "detail": str(e)}


@celery_app.task(bind=True, **IMAGE_TASK_OPTIONS)
def generate_thumbnail(self, media_id: str) -> dict:
    """
    生成缩略图任务

    生成宽度为 300px 的缩略图，保存到 media/thumbnails/ 目录
    更新数据库中的 thumbnail_path 字段

    Args:
        media_id: 媒体文件 UUID 字符串

    Returns:
        任务执行结果字典
    """
    import asyncio

    try:
        # 在同步任务中运行异步查询
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            media = loop.run_until_complete(get_media_by_id(media_id))
        finally:
            loop.close()

        if not media:
            logger.warning(f"缩略图任务：媒体文件 {media_id} 不存在")
            return {"status": "skipped", "reason": "media_not_found"}

        # 仅处理图片类型
        if media.file_type != "image":
            logger.info(f"缩略图任务：{media_id} 不是图片类型，跳过")
            return {"status": "skipped", "reason": "not_image"}

        # 构建文件路径
        thumbnails_dir = MEDIA_ROOT / "thumbnails"
        thumbnails_dir.mkdir(parents=True, exist_ok=True)

        try:
            file_path = _media_disk_path(media.file_path)
        except ValueError:
            logger.warning("缩略图任务：媒体文件 %s 路径不安全", media_id)
            return {"status": "error", "reason": "unsafe_media_path"}

        file_name = file_path.name

        if not file_path.exists():
            logger.warning(f"缩略图任务：文件 {file_path} 不存在")
            return {"status": "error", "reason": "file_not_found"}

        # 生成缩略图文件名
        thumbnail_name = f"thumb_{file_name}"
        thumbnail_path = thumbnails_dir / thumbnail_name

        # 生成缩略图
        try:
            with Image.open(file_path) as img:
                # 等比缩放到宽度 300px
                thumbnail_width = 300
                ratio = thumbnail_width / img.width
                thumbnail_height = int(img.height * ratio)
                thumbnail_size = (thumbnail_width, thumbnail_height)

                img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)

                # 转换 RGBA 为 RGB
                if img.mode == "RGBA":
                    rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[3])
                    img = rgb_img

                # 保存缩略图
                img.save(thumbnail_path, format="JPEG", quality=85, optimize=True)

                # 更新数据库（需要新建 event loop，之前的已关闭）
                thumbnail_relative_path = f"/media/thumbnails/{thumbnail_name}"
                db_loop = asyncio.new_event_loop()
                try:
                    asyncio.set_event_loop(db_loop)
                    db_loop.run_until_complete(
                        update_media_thumbnail(media_id, thumbnail_relative_path)
                    )
                finally:
                    db_loop.close()

                logger.info(f"缩略图任务：{media_id} 生成完成，尺寸 {thumbnail_size}")
                return {
                    "status": "success",
                    "thumbnail_path": thumbnail_relative_path,
                    "size": thumbnail_size,
                }

        except Exception as e:
            logger.error(f"缩略图任务：处理图片 {media_id} 失败: {str(e)}")
            return {"status": "error", "reason": "pillow_error", "detail": str(e)}

    except Exception as e:
        logger.error(f"缩略图任务：执行失败 {media_id}: {str(e)}")
        # 重试机制
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)
        return {"status": "error", "reason": "task_failed", "detail": str(e)}


@celery_app.task(**MEDIA_CLEANUP_TASK_OPTIONS)
def cleanup_expired_media_trash(retention_days: int | None = None) -> dict:
    """
    手动清理媒体回收站。

    删除 deleted_at 早于 MEDIA_TRASH_RETENTION_DAYS（默认 30 天）的媒体主文件、
    缩略图和数据库记录。此任务不会被 Celery Beat 默认调度。
    """
    import asyncio

    days = get_media_trash_retention_days(retention_days)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        records = loop.run_until_complete(fetch_expired_trashed_media(cutoff))
        record_ids, file_stats = delete_expired_trashed_media_files(records)
        deleted_db_records = loop.run_until_complete(
            delete_expired_trashed_media_records(record_ids)
        )
    except MediaTrashUnavailable as exc:
        logger.warning("媒体回收站清理跳过：%s", exc)
        return {
            "status": "skipped",
            "reason": "trash_column_unavailable",
            "retention_days": days,
            "cutoff": cutoff.isoformat(),
        }
    finally:
        loop.close()

    return {
        "status": "success",
        "retention_days": days,
        "cutoff": cutoff.isoformat(),
        "deleted_db_records": deleted_db_records,
        **file_stats,
    }
