"""
管理员与家庭设置相关的 Pydantic Schema
"""

from datetime import date, datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class AdminMemberSummary(BaseModel):
    """管理员概览中的成员摘要"""

    id: UUID
    username: str
    avatar_url: Optional[str] = None
    role_in_family: Optional[str] = None
    created_at: datetime


class AdminPostingMemberSummary(BaseModel):
    """最近发帖成员摘要"""

    id: UUID
    username: str
    avatar_url: Optional[str] = None
    role_in_family: Optional[str] = None
    post_count: int
    last_post_at: datetime


class AdminRecentCommentSummary(BaseModel):
    """最近评论摘要"""

    id: UUID
    post_id: UUID
    author_id: UUID
    author_username: str
    content: str
    created_at: datetime


class AdminRecentMediaSummary(BaseModel):
    """最近媒体与上传风险摘要"""

    id: UUID
    uploader_id: UUID
    uploader_username: str
    original_name: Optional[str] = None
    file_type: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    created_at: datetime
    warning: Optional[str] = None


class AdminStorageStatus(BaseModel):
    """媒体目录与磁盘状态"""

    media_root: str
    backup_root: str
    media_file_count: int
    media_directory_bytes: int
    database_media_bytes: int
    disk_total_bytes: int
    disk_used_bytes: int
    disk_free_bytes: int
    disk_free_percent: float
    last_scanned_at: datetime


class AdminRuntimeTaskTimeouts(BaseModel):
    """Celery 任务超时配置"""

    task_time_limit_seconds: int
    task_soft_time_limit_seconds: int
    image_task_time_limit_seconds: int
    image_task_soft_time_limit_seconds: int
    ai_task_time_limit_seconds: int
    ai_task_soft_time_limit_seconds: int
    media_cleanup_task_time_limit_seconds: int
    media_cleanup_task_soft_time_limit_seconds: int


class AdminRuntimeStatus(BaseModel):
    """运行时只读状态"""

    database_available: bool
    redis_available: bool
    celery_broker_url: str
    celery_result_backend: str
    celery_broker_configured: bool
    celery_result_backend_configured: bool
    task_timeouts: AdminRuntimeTaskTimeouts
    media_trash_retention_days: int
    checked_at: datetime


class AdminBackupItem(BaseModel):
    """一次备份快照摘要"""

    backup_id: str
    status: str
    created_at: datetime
    snapshot_file: str
    media_archive_file: Optional[str] = None
    size_bytes: int
    database_record_count: int
    media_file_count: int
    message: Optional[str] = None


class AdminBackupStatus(BaseModel):
    """备份目录状态"""

    backup_root: str
    latest: Optional[AdminBackupItem] = None
    recent: list[AdminBackupItem] = []


class AdminBackupCheck(BaseModel):
    """备份完整性校验项"""

    label: str
    ok: bool
    detail: str


class AdminBackupVerification(BaseModel):
    """备份完整性校验结果"""

    backup_id: str
    status: str
    verified_at: datetime
    checks: list[AdminBackupCheck]
    message: str
    restore_hint: str


class AdminOverviewResponse(BaseModel):
    """管理员概览响应"""

    user_count: int
    post_count: int
    comment_count: int
    media_count: int
    album_count: int
    event_count: int
    recent_members: list[AdminMemberSummary]
    recent_posting_members: list[AdminPostingMemberSummary]
    recent_comments: list[AdminRecentCommentSummary] = Field(default_factory=list)
    recent_media: list[AdminRecentMediaSummary] = Field(default_factory=list)
    upload_warnings: list[AdminRecentMediaSummary] = Field(default_factory=list)
    storage: AdminStorageStatus
    runtime: AdminRuntimeStatus
    backups: AdminBackupStatus


class AdminUserResponse(BaseModel):
    """管理员成员列表响应项"""

    id: UUID
    username: str
    email: str
    role: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    birthday: Optional[date] = None
    role_in_family: Optional[str] = None
    invite_code: Optional[str] = None
    invited_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    post_count: int
    comment_count: int
    media_count: int


class AdminUserUpdate(BaseModel):
    """管理员更新成员资料请求"""

    role: Optional[str] = Field(None, max_length=20)
    role_in_family: Optional[str] = Field(None, max_length=50)
    bio: Optional[str] = Field(None, max_length=500)

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in {"admin", "member"}:
            raise ValueError("role 只能是 admin 或 member")
        return value


class AdminInviteCodeResponse(BaseModel):
    """重新生成邀请码响应"""

    user_id: UUID
    invite_code: str


THEME_ASSET_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def validate_local_media_asset_url(value: Optional[str]) -> Optional[str]:
    """主题视觉资产只能引用本地私有媒体路径。"""
    if value in (None, ""):
        return value
    if not value.startswith("/media/"):
        raise ValueError("主题资产只能使用本地 /media/ 路径")
    path = value.split("?", 1)[0].lower()
    if not any(path.endswith(extension) for extension in THEME_ASSET_EXTENSIONS):
        raise ValueError("主题资产仅支持 jpg、jpeg、png、gif、webp")
    return value


class ThemeBackgroundAsset(BaseModel):
    """家庭背景图资产"""

    id: str = Field(..., min_length=1, max_length=80)
    url: str = Field(..., max_length=500)
    label: Optional[str] = Field(None, max_length=80)
    enabled: bool = True

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        return validate_local_media_asset_url(value) or value


class ThemeCursorAsset(BaseModel):
    """鼠标跟随装饰资产"""

    url: Optional[str] = Field(None, max_length=500)
    enabled: bool = False
    size: int = Field(76, ge=24, le=160)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: Optional[str]) -> Optional[str]:
        return validate_local_media_asset_url(value)


class ThemeOrnamentAsset(BaseModel):
    """页面角落挂饰资产"""

    id: str = Field(..., min_length=1, max_length=80)
    url: str = Field(..., max_length=500)
    position: Literal["top-left", "top-right", "bottom-left", "bottom-right"]
    enabled: bool = True
    size: int = Field(96, ge=24, le=220)
    opacity: float = Field(0.72, ge=0.1, le=1.0)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        return validate_local_media_asset_url(value) or value


class FamilyThemeAssets(BaseModel):
    """全局家庭主题资产集合"""

    backgrounds: list[ThemeBackgroundAsset] = Field(default_factory=list, max_length=12)
    cursor: Optional[ThemeCursorAsset] = None
    ornaments: list[ThemeOrnamentAsset] = Field(default_factory=list, max_length=8)


class FamilySettingsBase(BaseModel):
    """家庭设置基础字段"""

    family_name: str = Field(default="哪吒家庭", min_length=1, max_length=100)
    tagline: Optional[str] = Field(None, max_length=200)
    theme_color: Optional[str] = Field(None, max_length=20)
    accent_color: Optional[str] = Field(None, max_length=20)
    background_image_url: Optional[str] = Field(None, max_length=500)
    logo_url: Optional[str] = Field(None, max_length=500)
    theme_assets: FamilyThemeAssets = Field(default_factory=FamilyThemeAssets)

    @field_validator("background_image_url", "logo_url")
    @classmethod
    def validate_asset_url(cls, value: Optional[str]) -> Optional[str]:
        return validate_local_media_asset_url(value)


class FamilySettingsUpdate(FamilySettingsBase):
    """家庭设置更新请求"""


class FamilySettingsResponse(FamilySettingsBase):
    """家庭设置响应"""

    updated_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
