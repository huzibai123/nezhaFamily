"""
媒体文件上传 API
"""

from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Iterable, List, Optional
from uuid import UUID
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import and_, delete, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db.session import get_db
from app.core.security import get_current_user, get_current_user_id
from app.core.media_utils import (
    MEDIA_URL_PREFIX,
    media_path_from_url,
    media_storage_path,
    signed_media_url,
    verify_media_token,
)
from app.models.user import User
from app.models.media import MediaFavorite, MediaFile
from app.models.album import Album, album_media
from app.schemas.media import (
    MediaResponse,
    MediaBulkRequest,
    MediaBulkResponse,
    MediaFavoriteResponse,
    MediaLibraryResponse,
    MediaMonthFacet,
    MediaSearchItem,
    MediaSearchResponse,
    MediaSearchUploader,
    MediaUpdateRequest,
    MediaUploadItem,
    MediaUploadResponse,
)
from app.tasks.media_processing import compress_image
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
ALLOWED_IMAGE_EXTENSIONS = _configured_extensions(settings.ALLOWED_IMAGE_EXTENSIONS)
MAX_FILE_SIZE = settings.MAX_UPLOAD_SIZE
MEDIA_SORT_TIME = func.coalesce(MediaFile.captured_at, MediaFile.created_at)

# 文件头 magic bytes 签名表（用于验证真实文件类型）
_MAGIC_SIGNATURES: list[tuple[bytes, str]] = [
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
    (b"\x1aE\xdf\xa3", "video/webm"),
]

# 扩展名到允许的 MIME 类型映射
_ALLOWED_MIME_BY_EXT: dict[str, list[str]] = {
    ".jpg": ["image/jpeg"],
    ".jpeg": ["image/jpeg"],
    ".png": ["image/png"],
    ".gif": ["image/gif"],
    ".webp": ["image/webp"],
    ".mp4": ["video/mp4"],
    ".mov": ["video/quicktime", "video/mp4"],
    ".avi": ["video/x-msvideo", "video/avi"],
}


def _detect_mime_from_bytes(content: bytes) -> str | None:
    """通过文件头 magic bytes 检测 MIME 类型"""
    if len(content) >= 12 and content[4:8] == b"ftyp":
        return "video/mp4"

    if content[:4] == b"RIFF":
        if content[8:12] == b"WEBP":
            return "image/webp"
        if content[8:12] == b"AVI ":
            return "video/x-msvideo"
        return "application/riff"

    for sig, mime in _MAGIC_SIGNATURES:
        if content[: len(sig)] == sig:
            return mime
    return None


def _normalize_page(page: int, page_size: int) -> tuple[int, int]:
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 24
    return page, page_size


def _media_base_filters(
    *,
    q: Optional[str] = None,
    media_type: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    include_deleted: bool = False,
    trash_only: bool = False,
) -> list:
    filters = []
    keyword = q.strip() if q else ""
    if keyword:
        like_keyword = f"%{keyword}%"
        filters.append(
            or_(
                MediaFile.original_name.ilike(like_keyword),
                MediaFile.file_path.ilike(like_keyword),
                MediaFile.caption.ilike(like_keyword),
            )
        )
    if media_type:
        filters.append(MediaFile.file_type == media_type)
    if date_from:
        filters.append(
            MEDIA_SORT_TIME
            >= datetime.combine(date_from, time.min, tzinfo=timezone.utc)
        )
    if date_to:
        filters.append(
            MEDIA_SORT_TIME
            <= datetime.combine(date_to, time.max, tzinfo=timezone.utc)
        )
    if trash_only:
        filters.append(MediaFile.deleted_at.is_not(None))
    elif not include_deleted:
        filters.append(MediaFile.deleted_at.is_(None))
    return filters


def _media_item_response(
    media: MediaFile,
    uploader: User,
    favorite_ids: set[UUID] | None = None,
) -> MediaSearchItem:
    favorite_ids = favorite_ids or set()
    return MediaSearchItem(
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
        caption=media.caption,
        captured_at=media.captured_at or media.created_at,
        deleted_at=media.deleted_at,
        is_favorite=media.id in favorite_ids,
        created_at=media.created_at,
        uploader=MediaSearchUploader(
            id=uploader.id,
            username=uploader.username,
            avatar_url=uploader.avatar_url,
            role_in_family=uploader.role_in_family,
        ),
    )


async def _favorite_media_ids(
    db: AsyncSession,
    *,
    user_id: UUID,
    media_ids: list[UUID],
) -> set[UUID]:
    if not media_ids:
        return set()
    result = await db.execute(
        select(MediaFavorite.media_id).where(
            MediaFavorite.user_id == user_id,
            MediaFavorite.media_id.in_(media_ids),
        )
    )
    return set(result.scalars().all())


async def _media_uploaders(
    db: AsyncSession,
    *,
    base_filters: list,
) -> list[MediaSearchUploader]:
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
    return [
        MediaSearchUploader(
            id=row.id,
            username=row.username,
            avatar_url=row.avatar_url,
            role_in_family=row.role_in_family,
        )
        for row in uploader_result
    ]


async def _media_months(
    db: AsyncSession,
    *,
    base_filters: list,
) -> list[MediaMonthFacet]:
    month_expr = func.to_char(MEDIA_SORT_TIME, "YYYY-MM")
    month_query = (
        select(month_expr.label("month"), func.count(MediaFile.id).label("count"))
        .select_from(MediaFile)
        .group_by(month_expr)
        .order_by(month_expr.desc())
    )
    if base_filters:
        month_query = month_query.where(*base_filters)
    month_result = await db.execute(month_query)
    return [
        MediaMonthFacet(month=row.month, count=row.count)
        for row in month_result
        if row.month
    ]


async def _favorite_count(db: AsyncSession, *, user_id: UUID) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(MediaFavorite)
        .join(MediaFile, MediaFile.id == MediaFavorite.media_id)
        .where(
            MediaFavorite.user_id == user_id,
            MediaFile.deleted_at.is_(None),
        )
    )
    return result.scalar() or 0


async def _trash_count(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count()).select_from(MediaFile).where(MediaFile.deleted_at.is_not(None))
    )
    return result.scalar() or 0


def _can_manage_media(user: User, media: MediaFile) -> bool:
    return user.role == "admin" or media.uploader_id == user.id


async def _save_upload_file_streaming(
    file: UploadFile, file_path: Path
) -> tuple[int, bytes]:
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


async def store_uploaded_media_files(
    *,
    files: List[UploadFile],
    db: AsyncSession,
    current_user: User,
    allowed_extensions: Optional[Iterable[str]] = None,
    max_files: int = MAX_FILES_PER_UPLOAD,
    process_images: bool = True,
) -> MediaUploadResponse:
    """保存上传文件并可选触发图片处理任务。"""
    if len(files) > max_files:
        raise HTTPException(
            status_code=400,
            detail=f"单次最多上传 {max_files} 个文件",
        )

    allowed_exts = set(allowed_extensions or ALLOWED_EXTENSIONS)
    uploaded_files: list[MediaUploadItem] = []
    saved_paths: list[Path] = []

    try:
        for file in files:
            file_ext = Path(file.filename or "").suffix.lower()
            if file_ext not in allowed_exts:
                raise HTTPException(
                    status_code=400, detail=f"不支持的文件类型: {file_ext}"
                )

            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = media_storage_path(unique_filename)

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

            media_type = "video" if file_ext in {".mp4", ".mov", ".avi"} else "image"
            original_url = f"{MEDIA_URL_PREFIX}{unique_filename}"
            media = MediaFile(
                file_path=original_url,
                file_type=media_type,
                original_name=file.filename,
                mime_type=detected_mime or file.content_type,
                file_size=file_size,
                uploader_id=current_user.id,
                captured_at=datetime.now(timezone.utc),
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

    if process_images:
        for item in uploaded_files:
            if item.type == "image":
                compress_image.delay(str(item.id))

    return MediaUploadResponse(files=uploaded_files)


@router.post("/upload", response_model=MediaUploadResponse)
async def upload_media(
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传媒体文件"""
    return await store_uploaded_media_files(
        files=files,
        db=db,
        current_user=current_user,
    )


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
    page, page_size = _normalize_page(page, page_size)
    base_filters = _media_base_filters(
        q=q,
        media_type=media_type,
        date_from=date_from,
        date_to=date_to,
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

    uploaders = await _media_uploaders(db, base_filters=base_filters)

    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    rows = result.all()
    favorite_ids = await _favorite_media_ids(
        db,
        user_id=current_user.id,
        media_ids=[media.id for media, _uploader in rows],
    )

    items = [
        _media_item_response(media, uploader, favorite_ids)
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


@router.get("/media/library", response_model=MediaLibraryResponse)
async def get_media_library(
    q: Optional[str] = Query(None, max_length=100),
    uploader_id: Optional[UUID] = None,
    media_type: Optional[str] = Query(None, alias="type", pattern="^(image|video)$"),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    favorite_only: bool = False,
    trash_only: bool = False,
    page: int = 1,
    page_size: int = 48,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """家庭媒体库：全家共享浏览，支持收藏和回收站视图。"""
    page, page_size = _normalize_page(page, page_size)
    base_filters = _media_base_filters(
        q=q,
        media_type=media_type,
        date_from=date_from,
        date_to=date_to,
        trash_only=trash_only,
    )
    filters = list(base_filters)
    if uploader_id:
        filters.append(MediaFile.uploader_id == uploader_id)

    query = (
        select(MediaFile, User)
        .join(User, User.id == MediaFile.uploader_id)
        .order_by(desc(MEDIA_SORT_TIME), desc(MediaFile.created_at))
    )
    count_query = select(func.count()).select_from(MediaFile)

    if favorite_only:
        query = query.join(
            MediaFavorite,
            and_(
                MediaFavorite.media_id == MediaFile.id,
                MediaFavorite.user_id == current_user.id,
            ),
        )
        count_query = count_query.join(
            MediaFavorite,
            and_(
                MediaFavorite.media_id == MediaFile.id,
                MediaFavorite.user_id == current_user.id,
            ),
        )

    if filters:
        query = query.where(*filters)
        count_query = count_query.where(*filters)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    rows = (await db.execute(query.offset(offset).limit(page_size))).all()
    favorite_ids = await _favorite_media_ids(
        db,
        user_id=current_user.id,
        media_ids=[media.id for media, _uploader in rows],
    )

    return MediaLibraryResponse(
        media=[
            _media_item_response(media, uploader, favorite_ids)
            for media, uploader in rows
        ],
        uploaders=await _media_uploaders(db, base_filters=base_filters),
        months=await _media_months(db, base_filters=base_filters),
        trash_count=await _trash_count(db),
        favorite_count=await _favorite_count(db, user_id=current_user.id),
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + len(rows)) < total,
    )


@router.post("/media/bulk", response_model=MediaBulkResponse)
async def bulk_media_action(
    payload: MediaBulkRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """媒体库批量操作。"""
    unique_ids = list(dict.fromkeys(payload.media_ids))
    result = await db.execute(select(MediaFile).where(MediaFile.id.in_(unique_ids)))
    media_files = {media.id: media for media in result.scalars().all()}
    affected = 0
    skipped = len(unique_ids) - len(media_files)

    if payload.action == "add_to_album":
        album = await db.get(Album, payload.album_id)
        if not album:
            raise HTTPException(status_code=404, detail="相册不存在")
        if album.created_by != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="无权限修改此相册")

        active_media = [
            media
            for media in media_files.values()
            if media.deleted_at is None
        ]
        skipped += len(media_files) - len(active_media)
        if active_media:
            existing_result = await db.execute(
                select(album_media.c.media_id).where(
                    album_media.c.album_id == payload.album_id,
                    album_media.c.media_id.in_([media.id for media in active_media]),
                )
            )
            existing_ids = set(existing_result.scalars().all())
            for media in active_media:
                if media.id in existing_ids:
                    skipped += 1
                    continue
                await db.execute(
                    album_media.insert().values(
                        album_id=payload.album_id,
                        media_id=media.id,
                    )
                )
                affected += 1

    elif payload.action in {"favorite", "unfavorite"}:
        active_ids = [
            media.id
            for media in media_files.values()
            if media.deleted_at is None
        ]
        skipped += len(media_files) - len(active_ids)
        if payload.action == "favorite" and active_ids:
            existing_result = await db.execute(
                select(MediaFavorite.media_id).where(
                    MediaFavorite.user_id == current_user.id,
                    MediaFavorite.media_id.in_(active_ids),
                )
            )
            existing_ids = set(existing_result.scalars().all())
            for media_id in active_ids:
                if media_id in existing_ids:
                    skipped += 1
                    continue
                db.add(MediaFavorite(media_id=media_id, user_id=current_user.id))
                affected += 1
        elif active_ids:
            delete_result = await db.execute(
                delete(MediaFavorite).where(
                    MediaFavorite.user_id == current_user.id,
                    MediaFavorite.media_id.in_(active_ids),
                )
            )
            affected = delete_result.rowcount or 0
            skipped += len(active_ids) - affected

    elif payload.action in {"trash", "restore"}:
        now = datetime.now(timezone.utc)
        for media in media_files.values():
            if not _can_manage_media(current_user, media):
                skipped += 1
                continue
            if payload.action == "trash":
                if media.deleted_at is not None:
                    skipped += 1
                    continue
                media.deleted_at = now
                media.deleted_by = current_user.id
            else:
                if media.deleted_at is None:
                    skipped += 1
                    continue
                media.deleted_at = None
                media.deleted_by = None
            affected += 1

    await db.commit()
    return MediaBulkResponse(
        action=payload.action,
        requested=len(payload.media_ids),
        affected=affected,
        skipped=skipped,
    )


@router.get("/media/{media_id}", response_model=MediaResponse)
async def get_media(
    media_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个媒体文件详情。"""
    query = select(MediaFile).where(MediaFile.id == media_id)
    result = await db.execute(query)
    media = result.scalar_one_or_none()
    if not media:
        raise HTTPException(status_code=404, detail="媒体文件不存在")
    favorite_ids = await _favorite_media_ids(
        db,
        user_id=current_user.id,
        media_ids=[media.id],
    )

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
        caption=media.caption,
        captured_at=media.captured_at or media.created_at,
        deleted_at=media.deleted_at,
        is_favorite=media.id in favorite_ids,
        created_at=media.created_at,
    )


@router.patch("/media/{media_id}", response_model=MediaResponse)
async def update_media(
    media_id: UUID,
    payload: MediaUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新媒体说明和拍摄时间。"""
    media = await db.get(MediaFile, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="媒体文件不存在")
    if not _can_manage_media(current_user, media):
        raise HTTPException(status_code=403, detail="无权限修改此媒体")

    if "caption" in payload.model_fields_set:
        media.caption = payload.caption
    if "captured_at" in payload.model_fields_set:
        media.captured_at = payload.captured_at

    await db.commit()
    await db.refresh(media)
    favorite_ids = await _favorite_media_ids(
        db,
        user_id=current_user.id,
        media_ids=[media.id],
    )

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
        caption=media.caption,
        captured_at=media.captured_at or media.created_at,
        deleted_at=media.deleted_at,
        is_favorite=media.id in favorite_ids,
        created_at=media.created_at,
    )


@router.post("/media/{media_id}/favorite", response_model=MediaFavoriteResponse)
async def toggle_media_favorite(
    media_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """收藏/取消收藏媒体。"""
    media = await db.get(MediaFile, media_id)
    if not media or media.deleted_at is not None:
        raise HTTPException(status_code=404, detail="媒体文件不存在")

    result = await db.execute(
        select(MediaFavorite).where(
            MediaFavorite.media_id == media_id,
            MediaFavorite.user_id == current_user.id,
        )
    )
    favorite = result.scalar_one_or_none()
    if favorite:
        await db.delete(favorite)
        is_favorite = False
    else:
        db.add(MediaFavorite(media_id=media_id, user_id=current_user.id))
        is_favorite = True
    await db.commit()
    return MediaFavoriteResponse(is_favorite=is_favorite)


@router.delete("/media/{media_id}", response_model=MediaBulkResponse)
async def trash_media(
    media_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """把媒体移入回收站。"""
    response = await bulk_media_action(
        MediaBulkRequest(action="trash", media_ids=[media_id]),
        current_user=current_user,
        db=db,
    )
    return response


@router.post("/media/{media_id}/restore", response_model=MediaBulkResponse)
async def restore_media(
    media_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """从回收站恢复媒体。"""
    response = await bulk_media_action(
        MediaBulkRequest(action="restore", media_ids=[media_id]),
        current_user=current_user,
        db=db,
    )
    return response


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
        .where(
            MediaFile.uploader_id == current_user.id,
            MediaFile.deleted_at.is_(None),
        )
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
