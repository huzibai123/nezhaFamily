"""
评论模型
支持嵌套回复（parent_id）
"""
from sqlalchemy import Column, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.db.base import Base


class Comment(Base):
    """评论表"""
    __tablename__ = "comments"

    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 所属帖子
    post_id = Column(UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)

    # 作者
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # 父评论 ID（支持嵌套回复）
    parent_id = Column(UUID(as_uuid=True), ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True)

    # 内容
    content = Column(Text, nullable=False)

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # 关系定义
    post = relationship("Post", back_populates="comments")  # 所属帖子
    author = relationship("User", back_populates="comments")  # 作者
    parent = relationship("Comment", remote_side=[id], backref="replies")  # 父评论和子回复
    likes = relationship("Like", cascade="all, delete-orphan",
                        primaryjoin="and_(Comment.id==foreign(Like.target_id), Like.target_type=='comment')",
                        overlaps="likes")  # 消除与 Post.likes 的多态列冲突警告

    def __repr__(self):
        return f"<Comment(id={self.id}, post_id={self.post_id}, parent_id={self.parent_id})>"
