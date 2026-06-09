"""
媒体文件上传 API
"""
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db.session import get_db
from app.core.security import get_current_user, get_current_user_id
from app.core.media_utils import (
    MEDIA_ROOT,
    MEDIA_URL_PREFIX,
    media_path_from_url,
    media_storage_path,
    raw_media_url,
    signed_media_url,
    verify_media_token,
)
from app.models.user import User
from app.models.media import MediaFile
from app.schemas.media import (
    MediaResponse,
    MediaSearchItem,
    MediaSearchResponse,
    MediaSearchUploader,
    MediaUploadItem,
    MediaUploadResponse,
)
from app.tasks.media_processing import compress_image, generate_thumbnail
import uuid

router = APIRouter()
public_router = APIRouter()

MAX_FILES_PER_UPLOAD = 20  # 单次最多上传文件数
UPLOAD_CHUNK_SIZE = 1024 * 1024


def _configured_extensions(*extension_groups: List[str] | str) -> set[str]:
    extensions: set[str] = set()
    for group in extension_groups:
        values = group.split(",") if isinstance(group, str) else group
        for ext in values:
            normalized = ext.strip().lower().lstrip(".")
            if normalized:
                extensions.add(f".{normalized}")
    return extensions


ALLOWED_EXTENSIONS = _configured_extensions(
    settings.ALLOWED_IMAGE_EXTENSIONS,
    settings.ALLOWED_VIDEO_EXTENSIONS,
)
MAX_FILE_SIZE = settings.MAX_UPLOAD_SIZE

# 文件头 magic bytes 签名表（用于验证真实文件类型）
_MAGIC_SIGNATURES: list[tuple[bytes, str]] = [
    (b'\xff\xd8\xff', 'image/jpeg'),
    (b'\x89PNG\r\n\x1a\n', 'image/png'),
    (b'GIF87a', 'image/gif'),
    (b'GIF89a', 'image/gif'),
    (b'\x1aE\xdf\xa3', 'video/webm'),
]

# 扩展名到允许的 MIME 类型映射
_ALLOWED_MIME_BY_EXT: dict[str, list[str]] = {
    '.jpg': ['image/jpeg'],
    '.jpeg': ['image/jpeg'],
    '.png': ['image/png'],
    '.gif': ['image/gif'],
    '.webp': ['image/webp'],
    '.mp4': ['video/mp4'],
    '.mov': ['video/quicktime', 'video/mp4'],
    '.avi': ['video/x-msvideo', 'video/avi'],
}


def _detect_mime_from_bytes(content: bytes) -> str | None:
    """通过文件头 magic bytes 检测 MIME 类型"""
    if len(content) >= 12 and content[4:8] == b'ftyp':
        return 'video/mp4'

    if content[:4] == b'RIFF':
        if content[8:12] == b'WEBP':
            return 'image/webp'
        if content[8:12] == b'AVI ':
            return 'video/x-msvideo'
        return 'application/riff'

    for sig, mime in _MAGIC_SIGNATURES:
        if content[:len(sig)] == sig:
            return mime
    return None


async def _save_upload_file_streaming(file: UploadFile, file_path: Path) -> tuple[int, bytes]:
    """分块写入上传文件，避免大文件整体读入内存。"""
    total_size = 0
    header = b""
    try:
        with open(file_path, "wb") as output:
            while True:
                chunk = await file.read(UPLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                total_size += len(chunk)
                if len(header) < 32:
                    header += chunk[: 32 - len(header)]
                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(status_code=400, detail="文件大小超过限制")
                output.write(chunk)
    except Exception:
        file_path.unlink(missing_ok=True)
        raise

    return total_size, header


@router.post("/upload", response_model=MediaUploadResponse)
async def upload_media(
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传媒体文件"""
    # 限制单次上传文件数量
    if len(files) > MAX_FILES_PER_UPLOAD:
        raise HTTPException(
            status_code=400,
            detail=f"单次最多上传 {MAX_FILES_PER_UPLOAD} 个文件",
        )

    uploaded_files: list[MediaUploadItem] = []
    saved_paths: list[Path] = []

    try:
        for file in files:
            # 验证文件扩展名
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_ext}")

            # 生成唯一文件名
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = media_storage_path(unique_filename)

            # 验证真实文件类型（magic bytes 检查）
            file_size, file_header = await _save_upload_file_streaming(file, file_path)
            saved_paths.append(file_path)
            detected_mime = _detect_mime_from_bytes(file_header)
            allowed_mimes = _ALLOWED_MIME_BY_EXT.get(file_ext, [])
            if allowed_mimes and not detected_mime:
                raise HTTPException(status_code=400, detail="无法识别文件类型")
            if allowed_mimes and detected_mime not in allowed_mimes:
                raise HTTPException(
                    status_code=400,
                    detail=f"文件内容与扩展名不匹配: 检测到 {detected_mime}",
                )

            # 保存到数据库
            media_type = "video" if file_ext in {'.mp4', '.mov', '.avi'} else "image"
            original_url = f"{MEDIA_URL_PREFIX}{unique_filename}"
            media = MediaFile(
                file_path=original_url,
                file_type=media_type,
                original_name=file.filename,
                mime_type=file.content_type,
                file_size=file_size,
                uploader_id=current_user.id,
            )
            db.add(media)
            await db.flush()

            uploaded_files.append(
                MediaUploadItem(
                    id=media.id,
                    url=signed_media_url(media.file_path) or media.file_path,
                    raw_url=media.file_path,
                    type=media.file_type,
                )
            )

        await db.commit()
    except Exception:
        await db.rollback()
        for path in saved_paths:
            path.unlink(missing_ok=True)
        raise

    # 异步触发 Celery 任务处理媒体文件（压缩 + 缩略图）
    for item in uploaded_files:
        media_id_str = str(item.id)
        # 仅对图片类型触发处理任务；缩略图由压缩任务在更新主文件后继续触发。
        if item.type == "image":
            compress_image.delay(media_id_str)

    return MediaUploadResponse(files=uploaded_files)


@public_router.get("/media/{file_path:path}")
async def serve_signed_media_file(file_path: str, token: Optional[str] = None):
    """通过短期签名 URL 访问私有媒体文件。"""
    signed_path = f"{MEDIA_URL_PREFIX}{file_path}"
    if not verify_media_token(signed_path, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="媒体链接无效或已过期",
        )

    try:
        full_path = media_storage_path(file_path)
    except ValueError:
        raise HTTPException(status_code=403, detail="禁止访问")

    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(str(full_path))


@router.get("/media/search", response_model=MediaSearchResponse)
async def search_media(
    q: Optional[str] = Query(None, max_length=100),
    uploader_id: Optional[UUID] = None,
    media_type: Optional[str] = Query(None, alias="type", pattern="^(image|video)$"),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    page: int = 1,
    page_size: int = 24,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """搜索家庭媒体库。"""
    del current_user

    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 24

    base_filters = []
    keyword = q.strip() if q else ""
    if keyword:
        like_keyword = f"%{keyword}%"
        base_filters.append(
            or_(
                MediaFile.original_name.ilike(like_keyword),
                MediaFile.file_path.ilike(like_keyword),
            )
        )
    if media_type:
        base_filters.append(MediaFile.file_type == media_type)
    if date_from:
        base_filters.append(
            MediaFile.created_at >= datetime.combine(date_from, time.min, tzinfo=timezone.utc)
        )
    if date_to:
        base_filters.append(
            MediaFile.created_at <= datetime.combine(date_to, time.max, tzinfo=timezone.utc)
        )

    filters = list(base_filters)
    if uploader_id:
        filters.append(MediaFile.uploader_id == uploader_id)

    count_query = select(func.count()).select_from(MediaFile)
    query = (
        select(MediaFile, User)
        .join(User, User.id == MediaFile.uploader_id)
        .order_by(desc(MediaFile.created_at))
    )
    if filters:
        count_query = count_query.where(*filters)
        query = query.where(*filters)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    uploader_query = (
        select(
            User.id,
            User.username,
            User.avatar_url,
            User.role_in_family,
        )
        .join(MediaFile, MediaFile.uploader_id == User.id)
        .group_by(User.id, User.username, User.avatar_url, User.role_in_family)
        .order_by(User.username)
    )
    if base_filters:
        uploader_query = uploader_query.where(*base_filters)
    uploader_result = await db.execute(uploader_query)
    uploaders = [
        MediaSearchUploader(
            id=row.id,
            username=row.username,
            avatar_url=row.avatar_url,
            role_in_family=row.role_in_family,
        )
        for row in uploader_result
    ]

    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    rows = result.all()

    items = [
        MediaSearchItem(
            id=media.id,
            url=signed_media_url(media.file_path) or media.file_path,
            thumbnail_url=signed_media_url(media.thumbnail_path),
            type=media.file_type,
            original_name=media.original_name,
            file_size=media.file_size,
            mime_type=media.mime_type,
            width=media.width,
            height=media.height,
            duration=media.duration,
            created_at=media.created_at,
            uploader=MediaSearchUploader(
                id=uploader.id,
                username=uploader.username,
                avatar_url=uploader.avatar_url,
                role_in_family=uploader.role_in_family,
            ),
        )
        for media, uploader in rows
    ]

    return MediaSearchResponse(
        media=items,
        uploaders=uploaders,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + len(items)) < total,
    )


@router.get("/media/{media_id}", response_model=MediaResponse)
async def get_media(
    media_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取单个媒体文件详情（仅限上传者本人）"""
    query = select(MediaFile).where(
        MediaFile.id == media_id,
        MediaFile.uploader_id == current_user_id,
    )
    result = await db.execute(query)
    media = result.scalar_one_or_none()
    if not media:
        raise HTTPException(status_code=404, detail="媒体文件不存在")

    return MediaResponse(
        id=media.id,
        url=signed_media_url(media.file_path) or media.file_path,
        type=media.file_type,
        original_name=media.original_name,
        file_size=media.file_size,
        mime_type=media.mime_type,
        width=media.width,
        height=media.height,
        duration=media.duration,
        created_at=media.created_at,
    )


@router.get("/files/{file_path:path}")
async def serve_media_file(
    file_path: str,
    current_user_id: UUID = Depends(get_current_user_id),
):
    """提供媒体文件下载（需要认证，防止未授权访问）"""
    try:
        full_path = media_storage_path(media_path_from_url(file_path))
    except ValueError:
        raise HTTPException(status_code=403, detail="禁止访问")

    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(str(full_path))


@router.get("/media")
async def get_user_media(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户上传的媒体列表（分页）"""
    query = (
        select(MediaFile)
        .where(MediaFile.uploader_id == current_user.id)
        .order_by(MediaFile.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    media_files = result.scalars().all()

    return {
        "media": [
            {
                "id": media.id,
                "url": signed_media_url(media.file_path),
                "type": media.file_type,
                "created_at": media.created_at,
            }
            for media in media_files
        ],
        "skip": skip,
        "limit": limit,
    }
