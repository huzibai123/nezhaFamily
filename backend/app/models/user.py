"""
用户模型
包含用户认证、角色管理和邀请码机制
"""
from sqlalchemy import Boolean, Column, String, DateTime, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.db.base import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    # 主键：使用 UUID 代替自增 ID，更安全
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 基础信息
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # 角色权限：admin（管理员）或 member（普通成员）
    role = Column(String(20), nullable=False, default="member")
    is_system = Column(Boolean, nullable=False, default=False)
    system_type = Column(String(30), nullable=True)

    # 邀请码机制
    invite_code = Column(String(32), unique=True, nullable=True)  # 用户自己的邀请码
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # 被谁邀请

    # 头像
    avatar_url = Column(String(500), nullable=True)

    # 档案信息
    bio = Column(String(500), nullable=True)  # 个人简介
    birthday = Column(Date, nullable=True)  # 生日
    role_in_family = Column(String(50), nullable=True)  # 家庭角色（如：爸爸、妈妈、宝宝等）

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # 关系定义
    inviter = relationship("User", remote_side=[id], backref="invited_users")  # 邀请者
    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")  # 发布的帖子
    comments = relationship(
        "Comment",
        back_populates="author",
        cascade="all, delete-orphan",
        foreign_keys="Comment.author_id",
    )  # 发布的评论
    post_likes = relationship("PostLike", back_populates="user", cascade="all, delete-orphan")
    comment_likes = relationship("CommentLike", back_populates="user", cascade="all, delete-orphan")
    media_files = relationship(
        "MediaFile",
        back_populates="uploader",
        cascade="all, delete-orphan",
        foreign_keys="MediaFile.uploader_id",
    )  # 上传的媒体
    albums = relationship("Album", back_populates="creator", cascade="all, delete-orphan")  # 创建的相册
    events = relationship("Event", back_populates="creator", cascade="all, delete-orphan")  # 创建的事件

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
