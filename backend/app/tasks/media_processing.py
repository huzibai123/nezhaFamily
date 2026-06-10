"""
媒体处理 Celery 任务
处理图片压缩、缩略图生成等耗时操作
"""

import logging
from pathlib import Path
from uuid import UUID
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.tasks import celery_app
from app.core.media_utils import MEDIA_ROOT, media_path_from_url

logger = logging.getLogger(__name__)

# 与 API 和 Alembic 使用同一个 Settings 来源。
DATABASE_URL = settings.DATABASE_URL

# 为 Celery 任务创建独立的异步引擎和 session 工厂
task_engine = create_async_engine(DATABASE_URL, echo=False, future=True)
TaskAsyncSession = async_sessionmaker(
    task_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


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


@celery_app.task(bind=True, max_retries=3)
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
        relative_path = media_path_from_url(media.file_path)
        file_path = MEDIA_ROOT / relative_path

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


@celery_app.task(bind=True, max_retries=3)
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

        file_name = Path(media.file_path).name
        relative_path = media_path_from_url(media.file_path)
        file_path = MEDIA_ROOT / relative_path

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
