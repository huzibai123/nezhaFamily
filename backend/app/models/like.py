"""
点赞模型
支持对帖子和评论点赞，使用真实外键防止孤儿记录
"""
from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.db.base import Base


class PostLike(Base):
    """帖子点赞表"""
    __tablename__ = "post_likes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    post_id = Column(UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="uq_user_post_like"),
    )

    user = relationship("User", back_populates="post_likes")
    post = relationship("Post", back_populates="likes")

    def __repr__(self):
        return f"<PostLike(user_id={self.user_id}, post_id={self.post_id})>"


class CommentLike(Base):
    """评论点赞表"""
    __tablename__ = "comment_likes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    comment_id = Column(UUID(as_uuid=True), ForeignKey("comments.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "comment_id", name="uq_user_comment_like"),
    )

    user = relationship("User", back_populates="comment_likes")
    comment = relationship("Comment", back_populates="likes")

    def __repr__(self):
        return f"<CommentLike(user_id={self.user_id}, comment_id={self.comment_id})>"


Like = PostLike
