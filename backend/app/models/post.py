"""
帖子模型
包含内容、媒体 URLs、统计信息
"""
from sqlalchemy import Column, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.db.base import Base


class Post(Base):
    """帖子表"""
    __tablename__ = "posts"

    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 作者
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # 内容
    content = Column(Text, nullable=True)  # 文字内容，可为空（纯图片/视频帖子）

    # 媒体 URLs（存储为 JSON 数组）
    # 格式: [{"type": "image", "url": "/media/xxx.jpg", "thumbnail": "/media/xxx_thumb.jpg"}, ...]
    media_urls = Column(JSONB, nullable=True)

    # 统计信息（冗余字段，提升查询性能）
    comment_count = Column(Integer, default=0, nullable=False)

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)  # 时间线排序用
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # 关系定义
    author = relationship("User", back_populates="posts")  # 作者
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")  # 评论列表
    likes = relationship("PostLike", back_populates="post", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Post(id={self.id}, author_id={self.author_id}, created_at={self.created_at})>"
