"""
相册相关的 API 路由
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

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

    return AlbumResponse(
        id=album.id,
        name=album.name,
        description=album.description,
        cover_image_url=signed_media_url(album.cover_image_url),
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
    # 使用子查询统计每个相册的媒体数量
    media_count_subquery = (
        select(
            album_media.c.album_id,
            func.count(album_media.c.media_id).label("media_count")
        )
        .group_by(album_media.c.album_id)
        .subquery()
    )

    query = (
        select(Album, media_count_subquery.c.media_count)
        .outerjoin(media_count_subquery, Album.id == media_count_subquery.c.album_id)
        .order_by(Album.created_at.desc())
    )
    result = await db.execute(query)
    rows = result.all()

    albums = [
        AlbumResponse(
            id=album.id,
            name=album.name,
            description=album.description,
            cover_image_url=signed_media_url(album.cover_image_url),
            created_by=album.created_by,
            created_at=album.created_at,
            media_count=media_count or 0
        )
        for album, media_count in rows
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
        select(MediaFile)
        .join(album_media)
        .where(album_media.c.album_id == album_id)
    )
    media_result = await db.execute(media_query)
    media_files = media_result.scalars().all()

    return AlbumDetailResponse(
        id=album.id,
        name=album.name,
        description=album.description,
        cover_image_url=signed_media_url(album.cover_image_url),
        created_by=album.created_by,
        created_at=album.created_at,
        media=[
            AlbumMediaItem(
                id=media.id,
                url=signed_media_url(media.file_path) or media.file_path,
                type=media.file_type,
            )
            for media in media_files
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

    # 计算媒体数量（用子查询避免 lazy loading）
    media_count_query = select(func.count()).select_from(album_media).where(album_media.c.album_id == album.id)
    media_count_result = await db.execute(media_count_query)
    media_count = media_count_result.scalar() or 0

    return AlbumResponse(
        id=album.id,
        name=album.name,
        description=album.description,
        cover_image_url=signed_media_url(album.cover_image_url),
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
