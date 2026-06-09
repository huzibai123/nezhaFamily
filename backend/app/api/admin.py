"""
轻量管理员与家庭设置 API
"""
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import UUID
import json
import secrets
import shutil
import tarfile

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_active_admin
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.album import Album
from app.models.comment import Comment
from app.models.event import Event
from app.models.family_settings import FamilySettings
from app.models.like import Like
from app.models.media import MediaFile
from app.models.notification import Notification
from app.models.post import Post
from app.models.user import User
from app.core.media_utils import MEDIA_ROOT, raw_media_url, signed_media_url
from app.schemas.admin import (
    AdminBackupCheck,
    AdminBackupItem,
    AdminBackupStatus,
    AdminBackupVerification,
    AdminInviteCodeResponse,
    AdminMemberSummary,
    AdminOverviewResponse,
    AdminPostingMemberSummary,
    AdminRecentCommentSummary,
    AdminRecentMediaSummary,
    AdminStorageStatus,
    AdminUserResponse,
    AdminUserUpdate,
    FamilySettingsResponse,
    FamilySettingsUpdate,
)

router = APIRouter(prefix="/admin")
BACKUP_ROOT = Path(__file__).parent.parent.parent / "backups"
BACKUP_ROOT.mkdir(parents=True, exist_ok=True)


async def get_user_or_404(db: AsyncSession, user_id: UUID) -> User:
    """按 ID 获取用户，不存在则返回 404。"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    return user


async def count_rows(db: AsyncSession, model: type) -> int:
    """统计表行数。"""
    result = await db.execute(select(func.count()).select_from(model))
    return result.scalar() or 0


async def generate_unique_invite_code(db: AsyncSession) -> str:
    """生成唯一的邀请码。"""
    for _ in range(10):
        code = secrets.token_urlsafe(settings.INVITE_CODE_LENGTH)
        result = await db.execute(select(User.id).where(User.invite_code == code))
        if result.scalar_one_or_none() is None:
            return code

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="邀请码生成失败，请重试",
    )


async def get_family_settings_record(db: AsyncSession) -> Optional[FamilySettings]:
    """获取家庭设置记录。"""
    result = await db.execute(select(FamilySettings).where(FamilySettings.id == 1))
    return result.scalar_one_or_none()


def default_family_settings_response() -> FamilySettingsResponse:
    """未初始化时返回默认家庭设置。"""
    now = datetime.now(timezone.utc)
    return FamilySettingsResponse(
        family_name="哪吒家庭",
        tagline=None,
        theme_color=None,
        accent_color=None,
        background_image_url=None,
        updated_by=None,
        created_at=now,
        updated_at=now,
    )


def family_settings_response(settings_record: FamilySettings) -> FamilySettingsResponse:
    """家庭设置响应中的本地媒体背景图需要短期签名。"""
    response = FamilySettingsResponse.model_validate(settings_record)
    return response.model_copy(
        update={
            "background_image_url": signed_media_url(response.background_image_url),
        }
    )


def bytes_in_directory(root: Path) -> tuple[int, int]:
    """统计目录下真实文件数量和大小。"""
    if not root.exists():
        return 0, 0

    total_bytes = 0
    total_files = 0
    for path in root.rglob("*"):
        if path.is_file():
            total_files += 1
            total_bytes += path.stat().st_size
    return total_files, total_bytes


def format_backup_path(path: Path) -> str:
    """返回对管理员友好的相对路径。"""
    try:
        return str(path.relative_to(BACKUP_ROOT.parent))
    except ValueError:
        return str(path)


def load_backup_manifest(path: Path) -> Optional[AdminBackupItem]:
    """读取单个备份 manifest。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return AdminBackupItem(**data)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None


def get_backup_dir(backup_id: str) -> Path:
    """获取单个备份目录，并防止路径遍历。"""
    backup_dir = BACKUP_ROOT / backup_id
    try:
        backup_dir.resolve().relative_to(BACKUP_ROOT.resolve())
    except ValueError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="禁止访问该备份")

    if not backup_dir.exists() or not backup_dir.is_dir():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="备份不存在")
    return backup_dir


def get_backup_manifest_item(backup_id: str) -> AdminBackupItem:
    """读取指定备份 manifest。"""
    manifest_path = get_backup_dir(backup_id) / "manifest.json"
    item = load_backup_manifest(manifest_path)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="备份 manifest 不存在或无法读取",
        )
    return item


def resolve_backup_file(backup_id: str, file_kind: str) -> tuple[Path, str]:
    """按文件类型解析备份文件路径。"""
    backup_dir = get_backup_dir(backup_id)
    manifest = get_backup_manifest_item(backup_id)
    file_map = {
        "manifest": backup_dir / "manifest.json",
        "database": backup_dir / f"{backup_id}-database.json",
        "media": backup_dir / f"{backup_id}-media.tar.gz",
    }
    if file_kind not in file_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="下载类型仅支持 manifest、database、media",
        )

    path = file_map[file_kind]
    if file_kind == "media" and manifest.media_archive_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="该备份没有媒体归档")

    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="备份文件不存在")

    try:
        path.resolve().relative_to(backup_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="禁止访问该文件")

    return path, path.name


def get_backup_status() -> AdminBackupStatus:
    """读取最近备份状态。"""
    manifests = sorted(
        BACKUP_ROOT.glob("*/manifest.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    recent = [
        item
        for item in (load_backup_manifest(path) for path in manifests[:5])
        if item is not None
    ]
    return AdminBackupStatus(
        backup_root=format_backup_path(BACKUP_ROOT),
        latest=recent[0] if recent else None,
        recent=recent,
    )


def verify_backup_snapshot(backup_id: str) -> AdminBackupVerification:
    """校验备份 manifest、数据库快照和媒体归档是否可读。"""
    backup_dir = get_backup_dir(backup_id)
    checks: list[AdminBackupCheck] = []
    manifest_path = backup_dir / "manifest.json"
    manifest = load_backup_manifest(manifest_path)

    checks.append(
        AdminBackupCheck(
            label="manifest",
            ok=manifest is not None,
            detail="manifest.json 可读取" if manifest else "manifest.json 缺失或格式错误",
        )
    )

    snapshot_path = backup_dir / f"{backup_id}-database.json"
    snapshot_ok = False
    snapshot_detail = "数据库 JSON 快照缺失"
    if snapshot_path.exists():
        try:
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
            snapshot_ok = snapshot.get("format") == "nezha-family-json-snapshot-v1"
            snapshot_detail = (
                "数据库 JSON 快照可读取"
                if snapshot_ok
                else "数据库 JSON 快照格式标记不匹配"
            )
        except (OSError, json.JSONDecodeError):
            snapshot_detail = "数据库 JSON 快照无法解析"

    checks.append(
        AdminBackupCheck(label="database", ok=snapshot_ok, detail=snapshot_detail)
    )

    media_archive_path = backup_dir / f"{backup_id}-media.tar.gz"
    if manifest and manifest.media_archive_file is None:
        checks.append(
            AdminBackupCheck(
                label="media",
                ok=True,
                detail="该备份没有媒体文件，跳过媒体归档校验",
            )
        )
    else:
        media_ok = False
        media_detail = "媒体归档缺失"
        if media_archive_path.exists():
            try:
                with tarfile.open(media_archive_path, "r:gz") as archive:
                    archive.getmembers()
                media_ok = True
                media_detail = "媒体归档可读取"
            except (OSError, tarfile.TarError):
                media_detail = "媒体归档无法解析"
        checks.append(AdminBackupCheck(label="media", ok=media_ok, detail=media_detail))

    status_value = "valid" if all(check.ok for check in checks) else "invalid"
    return AdminBackupVerification(
        backup_id=backup_id,
        status=status_value,
        verified_at=datetime.now(timezone.utc),
        checks=checks,
        message="备份完整，可以下载用于恢复" if status_value == "valid" else "备份不完整，请检查文件",
        restore_hint="先下载 database 与 media 文件；恢复生产数据前请停机并保留当前数据副本。",
    )


async def get_storage_status(db: AsyncSession) -> AdminStorageStatus:
    """统计媒体目录、数据库媒体体积和磁盘剩余空间。"""
    media_file_count, media_directory_bytes = bytes_in_directory(MEDIA_ROOT)
    database_media_bytes = await db.scalar(
        select(func.coalesce(func.sum(MediaFile.file_size), 0))
    )
    disk_usage = shutil.disk_usage(MEDIA_ROOT)
    disk_free_percent = (
        round((disk_usage.free / disk_usage.total) * 100, 2)
        if disk_usage.total
        else 0.0
    )

    return AdminStorageStatus(
        media_root=str(MEDIA_ROOT),
        backup_root=format_backup_path(BACKUP_ROOT),
        media_file_count=media_file_count,
        media_directory_bytes=media_directory_bytes,
        database_media_bytes=database_media_bytes or 0,
        disk_total_bytes=disk_usage.total,
        disk_used_bytes=disk_usage.used,
        disk_free_bytes=disk_usage.free,
        disk_free_percent=disk_free_percent,
        last_scanned_at=datetime.now(timezone.utc),
    )


def serialize_value(value):
    """把 ORM 值转成 JSON 可存储格式。"""
    if isinstance(value, (date, datetime, UUID)):
        return str(value)
    return value


def serialize_model(instance) -> dict:
    """序列化 SQLAlchemy 模型列。"""
    return {
        column.name: serialize_value(getattr(instance, column.name))
        for column in instance.__table__.columns
    }


async def snapshot_table(db: AsyncSession, model: type) -> list[dict]:
    """导出一张表的全部记录。"""
    result = await db.execute(select(model))
    return [serialize_model(item) for item in result.scalars().all()]


async def build_backup_payload(db: AsyncSession) -> dict:
    """构建家庭数据 JSON 快照。"""
    tables = {
        "users": await snapshot_table(db, User),
        "posts": await snapshot_table(db, Post),
        "comments": await snapshot_table(db, Comment),
        "likes": await snapshot_table(db, Like),
    }
    tables["media_files"] = await snapshot_table(db, MediaFile)
    tables["albums"] = await snapshot_table(db, Album)
    tables["events"] = await snapshot_table(db, Event)
    tables["family_settings"] = await snapshot_table(db, FamilySettings)
    tables["notifications"] = await snapshot_table(db, Notification)

    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "format": "nezha-family-json-snapshot-v1",
        "tables": tables,
    }


def count_snapshot_records(payload: dict) -> int:
    """统计快照中的记录数。"""
    return sum(len(records) for records in payload.get("tables", {}).values())


def create_media_archive(backup_dir: Path, backup_id: str) -> tuple[Optional[Path], int, int]:
    """归档媒体目录，返回归档路径、文件数和大小。"""
    media_file_count, _ = bytes_in_directory(MEDIA_ROOT)
    if media_file_count == 0:
        return None, 0, 0

    archive_path = backup_dir / f"{backup_id}-media.tar.gz"
    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(MEDIA_ROOT, arcname="media")

    return archive_path, media_file_count, archive_path.stat().st_size


async def create_backup_snapshot(db: AsyncSession) -> AdminBackupItem:
    """创建一次真实备份快照。"""
    created_at = datetime.now(timezone.utc)
    backup_id = created_at.strftime("%Y%m%d%H%M%S%f")
    backup_dir = BACKUP_ROOT / backup_id
    backup_dir.mkdir(parents=True, exist_ok=False)

    snapshot_path = backup_dir / f"{backup_id}-database.json"
    payload = await build_backup_payload(db)
    snapshot_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    media_archive_path, media_count, media_archive_size = create_media_archive(
        backup_dir,
        backup_id,
    )
    snapshot_size = snapshot_path.stat().st_size
    total_size = snapshot_size + media_archive_size

    backup = AdminBackupItem(
        backup_id=backup_id,
        status="success",
        created_at=created_at,
        snapshot_file=format_backup_path(snapshot_path),
        media_archive_file=(
            format_backup_path(media_archive_path) if media_archive_path else None
        ),
        size_bytes=total_size,
        database_record_count=count_snapshot_records(payload),
        media_file_count=media_count,
        message="已生成数据库 JSON 快照和媒体归档",
    )
    manifest_path = backup_dir / "manifest.json"
    manifest_path.write_text(
        backup.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return backup


@router.get("/overview", response_model=AdminOverviewResponse)
async def get_admin_overview(
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取管理员概览数据。"""
    del current_user

    recent_members_result = await db.execute(
        select(User).order_by(desc(User.created_at)).limit(5)
    )
    recent_members = [
        AdminMemberSummary(
            id=user.id,
            username=user.username,
            avatar_url=user.avatar_url,
            role_in_family=user.role_in_family,
            created_at=user.created_at,
        )
        for user in recent_members_result.scalars().all()
    ]

    last_post_at = func.max(Post.created_at).label("last_post_at")
    recent_posting_result = await db.execute(
        select(
            User.id,
            User.username,
            User.avatar_url,
            User.role_in_family,
            func.count(Post.id).label("post_count"),
            last_post_at,
        )
        .join(Post, Post.author_id == User.id)
        .group_by(User.id, User.username, User.avatar_url, User.role_in_family)
        .order_by(desc(last_post_at))
        .limit(5)
    )
    recent_posting_members = [
        AdminPostingMemberSummary(
            id=row.id,
            username=row.username,
            avatar_url=row.avatar_url,
            role_in_family=row.role_in_family,
            post_count=row.post_count,
            last_post_at=row.last_post_at,
        )
        for row in recent_posting_result
    ]

    recent_comments_result = await db.execute(
        select(Comment, User)
        .join(User, User.id == Comment.author_id)
        .order_by(desc(Comment.created_at))
        .limit(6)
    )
    recent_comments = [
        AdminRecentCommentSummary(
            id=comment.id,
            post_id=comment.post_id,
            author_id=user.id,
            author_username=user.username,
            content=comment.content,
            created_at=comment.created_at,
        )
        for comment, user in recent_comments_result.all()
    ]

    recent_media_result = await db.execute(
        select(MediaFile, User)
        .join(User, User.id == MediaFile.uploader_id)
        .order_by(desc(MediaFile.created_at))
        .limit(6)
    )
    recent_media = [
        AdminRecentMediaSummary(
            id=media.id,
            uploader_id=user.id,
            uploader_username=user.username,
            original_name=media.original_name,
            file_type=media.file_type,
            file_size=media.file_size,
            mime_type=media.mime_type,
            created_at=media.created_at,
            warning=None,
        )
        for media, user in recent_media_result.all()
    ]

    upload_warning_result = await db.execute(
        select(MediaFile, User)
        .join(User, User.id == MediaFile.uploader_id)
        .where(
            (MediaFile.mime_type.is_(None))
            | (MediaFile.file_size.is_(None))
            | (MediaFile.file_size <= 0)
        )
        .order_by(desc(MediaFile.created_at))
        .limit(6)
    )
    upload_warnings = [
        AdminRecentMediaSummary(
            id=media.id,
            uploader_id=user.id,
            uploader_username=user.username,
            original_name=media.original_name,
            file_type=media.file_type,
            file_size=media.file_size,
            mime_type=media.mime_type,
            created_at=media.created_at,
            warning="缺少 MIME 或文件大小异常",
        )
        for media, user in upload_warning_result.all()
    ]

    return AdminOverviewResponse(
        user_count=await count_rows(db, User),
        post_count=await count_rows(db, Post),
        comment_count=await count_rows(db, Comment),
        media_count=await count_rows(db, MediaFile),
        album_count=await count_rows(db, Album),
        event_count=await count_rows(db, Event),
        recent_members=recent_members,
        recent_posting_members=recent_posting_members,
        recent_comments=recent_comments,
        recent_media=recent_media,
        upload_warnings=upload_warnings,
        storage=await get_storage_status(db),
        backups=get_backup_status(),
    )


@router.post("/backups", response_model=AdminBackupItem)
async def create_admin_backup(
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理员手动创建一次家庭数据备份。"""
    del current_user
    return await create_backup_snapshot(db)


@router.get("/backups", response_model=AdminBackupStatus)
async def get_admin_backups(
    current_user: User = Depends(get_current_active_admin),
):
    """查看最近备份状态。"""
    del current_user
    return get_backup_status()


@router.get("/backups/{backup_id}", response_model=AdminBackupItem)
async def get_admin_backup_detail(
    backup_id: str,
    current_user: User = Depends(get_current_active_admin),
):
    """查看单个备份 manifest。"""
    del current_user
    return get_backup_manifest_item(backup_id)


@router.post("/backups/{backup_id}/verify", response_model=AdminBackupVerification)
async def verify_admin_backup(
    backup_id: str,
    current_user: User = Depends(get_current_active_admin),
):
    """校验备份是否具备恢复前的基本完整性。"""
    del current_user
    return verify_backup_snapshot(backup_id)


@router.get("/backups/{backup_id}/download/{file_kind}")
async def download_admin_backup_file(
    backup_id: str,
    file_kind: str,
    current_user: User = Depends(get_current_active_admin),
):
    """下载备份文件：manifest、database 或 media。"""
    del current_user
    path, filename = resolve_backup_file(backup_id, file_kind)
    return FileResponse(path=path, filename=filename)


@router.get("/users", response_model=list[AdminUserResponse])
async def get_admin_users(
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取成员列表与基础统计。"""
    del current_user

    post_counts = (
        select(Post.author_id.label("user_id"), func.count(Post.id).label("post_count"))
        .group_by(Post.author_id)
        .subquery()
    )
    comment_counts = (
        select(
            Comment.author_id.label("user_id"),
            func.count(Comment.id).label("comment_count"),
        )
        .group_by(Comment.author_id)
        .subquery()
    )
    media_counts = (
        select(
            MediaFile.uploader_id.label("user_id"),
            func.count(MediaFile.id).label("media_count"),
        )
        .group_by(MediaFile.uploader_id)
        .subquery()
    )

    result = await db.execute(
        select(
            User,
            func.coalesce(post_counts.c.post_count, 0).label("post_count"),
            func.coalesce(comment_counts.c.comment_count, 0).label("comment_count"),
            func.coalesce(media_counts.c.media_count, 0).label("media_count"),
        )
        .outerjoin(post_counts, post_counts.c.user_id == User.id)
        .outerjoin(comment_counts, comment_counts.c.user_id == User.id)
        .outerjoin(media_counts, media_counts.c.user_id == User.id)
        .order_by(desc(User.created_at))
    )

    return [
        AdminUserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            avatar_url=user.avatar_url,
            bio=user.bio,
            birthday=user.birthday,
            role_in_family=user.role_in_family,
            invite_code=user.invite_code,
            invited_by=user.invited_by,
            created_at=user.created_at,
            updated_at=user.updated_at,
            post_count=post_count,
            comment_count=comment_count,
            media_count=media_count,
        )
        for user, post_count, comment_count, media_count in result.all()
    ]


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
async def update_admin_user(
    user_id: UUID,
    user_data: AdminUserUpdate,
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    """管理员更新成员角色、家庭角色和简介。"""
    del current_user

    user = await get_user_or_404(db, user_id)
    update_data = user_data.model_dump(exclude_unset=True)

    new_role = update_data.get("role")
    if user.role == "admin" and new_role is not None and new_role != "admin":
        admin_count_result = await db.execute(
            select(func.count()).select_from(User).where(User.role == "admin")
        )
        if (admin_count_result.scalar() or 0) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能降级最后一个管理员",
            )

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    post_count = await db.scalar(
        select(func.count()).select_from(Post).where(Post.author_id == user.id)
    )
    comment_count = await db.scalar(
        select(func.count()).select_from(Comment).where(Comment.author_id == user.id)
    )
    media_count = await db.scalar(
        select(func.count()).select_from(MediaFile).where(MediaFile.uploader_id == user.id)
    )

    return AdminUserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        avatar_url=user.avatar_url,
        bio=user.bio,
        birthday=user.birthday,
        role_in_family=user.role_in_family,
        invite_code=user.invite_code,
        invited_by=user.invited_by,
        created_at=user.created_at,
        updated_at=user.updated_at,
        post_count=post_count or 0,
        comment_count=comment_count or 0,
        media_count=media_count or 0,
    )


@router.post("/users/{user_id}/invite-code", response_model=AdminInviteCodeResponse)
async def regenerate_user_invite_code(
    user_id: UUID,
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    """重新生成用户邀请码。"""
    del current_user

    user = await get_user_or_404(db, user_id)
    user.invite_code = await generate_unique_invite_code(db)

    await db.commit()
    await db.refresh(user)

    return AdminInviteCodeResponse(user_id=user.id, invite_code=user.invite_code)


@router.get("/family-settings", response_model=FamilySettingsResponse)
async def get_family_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取家庭设置，任意登录用户可访问。"""
    del current_user

    settings_record = await get_family_settings_record(db)
    if not settings_record:
        return default_family_settings_response()

    return family_settings_response(settings_record)


@router.put("/family-settings", response_model=FamilySettingsResponse)
async def update_family_settings(
    settings_data: FamilySettingsUpdate,
    current_user: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    """更新家庭设置，仅管理员可访问。"""
    settings_record = await get_family_settings_record(db)
    if not settings_record:
        settings_record = FamilySettings(id=1)
        db.add(settings_record)

    update_data = settings_data.model_dump()
    for field, value in update_data.items():
        if field == "background_image_url":
            value = raw_media_url(value)
        setattr(settings_record, field, value)
    settings_record.updated_by = current_user.id

    await db.commit()
    await db.refresh(settings_record)

    return family_settings_response(settings_record)
