"""
管理员与家庭设置相关的 Pydantic Schema
"""
from datetime import date, datetime
from typing import Optional
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


class FamilySettingsBase(BaseModel):
    """家庭设置基础字段"""
    family_name: str = Field(default="哪吒家庭", min_length=1, max_length=100)
    tagline: Optional[str] = Field(None, max_length=200)
    theme_color: Optional[str] = Field(None, max_length=20)
    accent_color: Optional[str] = Field(None, max_length=20)
    background_image_url: Optional[str] = Field(None, max_length=500)


class FamilySettingsUpdate(FamilySettingsBase):
    """家庭设置更新请求"""


class FamilySettingsResponse(FamilySettingsBase):
    """家庭设置响应"""
    updated_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
