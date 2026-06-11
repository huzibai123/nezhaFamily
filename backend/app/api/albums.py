"""
相册相关的 API 路由
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.db.session import get_db
from app.models.user import User
from app.models.album import Album, album_media
from app.models.media import MediaFile
from app.core.security import get_current_user
from app.core.media_utils import raw_media_url, signed_media_url
from app.schemas.album import (
    AlbumCreate,
    AlbumUpdate,
    AlbumResponse,
    AlbumDetailResponse,
    AlbumMediaItem,
)

router = APIRouter()


def _album_cover_url(album: Album, fallback_cover_url: str | None = None) -> str | None:
    return signed_media_url(album.cover_image_url or fallback_cover_url)


def _album_cover_type(
    album: Album,
    manual_cover_type: str | None = None,
    fallback_cover_type: str | None = None,
) -> str | None:
    if album.cover_image_url:
        return manual_cover_type or "image"
    return fallback_cover_type


async def _album_media_count(db: AsyncSession, album_id: UUID) -> int:
    media_count_query = (
        select(func.count())
        .select_from(album_media)
        .join(MediaFile, MediaFile.id == album_media.c.media_id)
        .where(album_media.c.album_id == album_id, MediaFile.deleted_at.is_(None))
    )
    media_count_result = await db.execute(media_count_query)
    return media_count_result.scalar() or 0


async def _latest_album_cover(db: AsyncSession, album_id: UUID) -> tuple[str | None, str | None]:
    result = await db.execute(
        select(MediaFile.file_path, MediaFile.file_type)
        .join(album_media, MediaFile.id == album_media.c.media_id)
        .where(
            album_media.c.album_id == album_id,
            MediaFile.deleted_at.is_(None),
        )
        .order_by(album_media.c.added_at.desc(), MediaFile.created_at.desc())
        .limit(1)
    )
    row = result.first()
    return (row.file_path, row.file_type) if row else (None, None)


async def _manual_album_cover_type(db: AsyncSession, cover_image_url: str | None) -> str | None:
    if not cover_image_url:
        return None
    result = await db.execute(
        select(MediaFile.file_type)
        .where(
            MediaFile.file_path == cover_image_url,
            MediaFile.deleted_at.is_(None),
        )
        .limit(1)
    )
    return result.scalar_one_or_none()


@router.post("/albums", response_model=AlbumResponse)
async def create_album(
    album_data: AlbumCreate = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建相册"""
    album = Album(
        name=album_data.name,
        description=album_data.description,
        cover_image_url=raw_media_url(album_data.cover_image_url),
        created_by=current_user.id
    )
    db.add(album)
    await db.commit()
    await db.refresh(album)
    manual_cover_type = await _manual_album_cover_type(db, album.cover_image_url)

    return AlbumResponse(
        id=album.id,
        name=album.name,
        description=album.description,
        cover_image_url=_album_cover_url(album),
        cover_media_type=_album_cover_type(album, manual_cover_type),
        created_by=album.created_by,
        created_at=album.created_at,
        media_count=0
    )

@router.get("/albums")
async def get_albums(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取相册列表"""
    # 使用子查询统计每个相册的媒体数量，并取最新有效媒体作为自动封面。
    media_count_subquery = (
        select(
            album_media.c.album_id,
            func.count(album_media.c.media_id).label("media_count")
        )
        .join(MediaFile, MediaFile.id == album_media.c.media_id)
        .where(MediaFile.deleted_at.is_(None))
        .group_by(album_media.c.album_id)
        .subquery()
    )
    latest_media_subquery = (
        select(
            album_media.c.album_id,
            MediaFile.file_path.label("fallback_cover_url"),
            MediaFile.file_type.label("fallback_cover_type"),
            func.row_number()
            .over(
                partition_by=album_media.c.album_id,
                order_by=(album_media.c.added_at.desc(), MediaFile.created_at.desc()),
            )
            .label("row_number"),
        )
        .join(MediaFile, MediaFile.id == album_media.c.media_id)
        .where(MediaFile.deleted_at.is_(None))
        .subquery()
    )
    manual_cover_media = aliased(MediaFile)

    query = (
        select(
            Album,
            media_count_subquery.c.media_count,
            latest_media_subquery.c.fallback_cover_url,
            latest_media_subquery.c.fallback_cover_type,
            manual_cover_media.file_type.label("manual_cover_type"),
        )
        .outerjoin(media_count_subquery, Album.id == media_count_subquery.c.album_id)
        .outerjoin(
            latest_media_subquery,
            and_(
                Album.id == latest_media_subquery.c.album_id,
                latest_media_subquery.c.row_number == 1,
            ),
        )
        .outerjoin(
            manual_cover_media,
            and_(
                manual_cover_media.file_path == Album.cover_image_url,
                manual_cover_media.deleted_at.is_(None),
            ),
        )
        .order_by(Album.created_at.desc())
    )
    result = await db.execute(query)
    rows = result.all()

    albums = [
        AlbumResponse(
            id=album.id,
            name=album.name,
            description=album.description,
            cover_image_url=_album_cover_url(album, fallback_cover_url),
            cover_media_type=_album_cover_type(album, manual_cover_type, fallback_cover_type),
            created_by=album.created_by,
            created_at=album.created_at,
            media_count=media_count or 0
        )
        for album, media_count, fallback_cover_url, fallback_cover_type, manual_cover_type in rows
    ]

    return {"albums": albums}

@router.get("/albums/{album_id}", response_model=AlbumDetailResponse)
async def get_album_detail(
    album_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取相册详情（含照片）"""
    query = select(Album).where(Album.id == album_id)
    result = await db.execute(query)
    album = result.scalar_one_or_none()

    if not album:
        raise HTTPException(status_code=404, detail="相册不存在")

    # 显式查询相册的媒体文件（避免 lazy loading）
    media_query = (
        select(MediaFile, album_media.c.added_at)
        .join(album_media)
        .where(
            album_media.c.album_id == album_id,
            MediaFile.deleted_at.is_(None),
        )
        .order_by(album_media.c.added_at.desc())
    )
    media_result = await db.execute(media_query)
    media_rows = media_result.all()
    fallback_cover_url = media_rows[0][0].file_path if media_rows else None
    fallback_cover_type = media_rows[0][0].file_type if media_rows else None
    manual_cover_type = next(
        (
            media.file_type
            for media, _added_at in media_rows
            if media.file_path == album.cover_image_url
        ),
        None,
    )
    if album.cover_image_url and manual_cover_type is None:
        manual_cover_type = await _manual_album_cover_type(db, album.cover_image_url)

    return AlbumDetailResponse(
        id=album.id,
        name=album.name,
        description=album.description,
        cover_image_url=_album_cover_url(album, fallback_cover_url),
        cover_media_type=_album_cover_type(album, manual_cover_type, fallback_cover_type),
        created_by=album.created_by,
        created_at=album.created_at,
        media=[
            AlbumMediaItem(
                id=media.id,
                url=signed_media_url(media.file_path) or media.file_path,
                type=media.file_type,
                added_at=added_at,
            )
            for media, added_at in media_rows
        ]
    )


@router.put("/albums/{album_id}", response_model=AlbumResponse)
async def update_album(
    album_id: UUID,
    album_data: AlbumUpdate = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新相册（仅创建者或管理员）"""
    album = await db.get(Album, album_id)
    if not album:
        raise HTTPException(status_code=404, detail="相册不存在")

    # 权限校验：仅创建者或管理员可更新
    if album.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限修改此相册")

    # 更新字段
    if album_data.name is not None:
        album.name = album_data.name
    if album_data.description is not None:
        album.description = album_data.description
    if album_data.cover_image_url is not None:
        album.cover_image_url = raw_media_url(album_data.cover_image_url)

    await db.commit()
    await db.refresh(album)

    media_count = await _album_media_count(db, album.id)
    fallback_cover_url, fallback_cover_type = await _latest_album_cover(db, album.id)
    manual_cover_type = await _manual_album_cover_type(db, album.cover_image_url)

    return AlbumResponse(
        id=album.id,
        name=album.name,
        description=album.description,
        cover_image_url=_album_cover_url(album, fallback_cover_url),
        cover_media_type=_album_cover_type(album, manual_cover_type, fallback_cover_type),
        created_by=album.created_by,
        created_at=album.created_at,
        media_count=media_count
    )


@router.delete("/albums/{album_id}")
async def delete_album(
    album_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除相册（仅创建者或管理员）"""
    album = await db.get(Album, album_id)
    if not album:
        raise HTTPException(status_code=404, detail="相册不存在")

    # 权限校验：仅创建者或管理员可删除
    if album.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限删除此相册")

    await db.delete(album)
    await db.commit()

    return {"message": "删除成功"}

@router.post("/albums/{album_id}/media/{media_id}")
async def add_media_to_album(
    album_id: UUID,
    media_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """添加照片到相册（仅创建者或管理员）"""
    album = await db.get(Album, album_id)
    if not album:
        raise HTTPException(status_code=404, detail="相册不存在")

    # 权限校验：仅创建者或管理员可添加
    if album.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限修改此相册")

    media = await db.get(MediaFile, media_id)
    if not media or media.deleted_at is not None:
        raise HTTPException(status_code=404, detail="媒体文件不存在")

    # 显式查询关联是否存在（避免 async session 中触发 lazy loading）
    exists_query = select(album_media).where(
        and_(
            album_media.c.album_id == album_id,
            album_media.c.media_id == media_id,
        )
    )
    result = await db.execute(exists_query)
    if result.first():
        raise HTTPException(status_code=400, detail="媒体已在相册中")

    # 插入关联记录
    insert_stmt = album_media.insert().values(
        album_id=album_id, media_id=media_id
    )
    await db.execute(insert_stmt)
    await db.commit()

    return {"message": "添加成功"}


@router.delete("/albums/{album_id}/media/{media_id}")
async def remove_media_from_album(
    album_id: UUID,
    media_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """从相册移除照片（仅创建者或管理员）"""
    album = await db.get(Album, album_id)
    if not album:
        raise HTTPException(status_code=404, detail="相册不存在")

    # 权限校验：仅创建者或管理员可移除
    if album.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限修改此相册")

    media = await db.get(MediaFile, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="媒体文件不存在")

    # 显式查询关联是否存在（避免 async session 中触发 lazy loading）
    exists_query = select(album_media).where(
        and_(
            album_media.c.album_id == album_id,
            album_media.c.media_id == media_id,
        )
    )
    result = await db.execute(exists_query)
    if not result.first():
        raise HTTPException(status_code=400, detail="媒体不在相册中")

    # 删除关联记录
    delete_stmt = album_media.delete().where(
        and_(
            album_media.c.album_id == album_id,
            album_media.c.media_id == media_id,
        )
    )
    await db.execute(delete_stmt)
    await db.commit()

    return {"message": "移除成功"}
