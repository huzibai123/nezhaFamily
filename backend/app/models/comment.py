"""
评论模型
支持嵌套回复（parent_id）
"""
from sqlalchemy import Boolean, Column, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID
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

    # AI 生成信息
    is_ai_generated = Column(Boolean, nullable=False, default=False)
    ai_persona_id = Column(UUID(as_uuid=True), ForeignKey("ai_personas.id", ondelete="SET NULL"), nullable=True)
    ai_generation_metadata = Column(JSONB, nullable=False, default=dict)
    edited_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    edited_at = Column(DateTime(timezone=True), nullable=True)

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # 关系定义
    post = relationship("Post", back_populates="comments")  # 所属帖子
    author = relationship("User", back_populates="comments", foreign_keys=[author_id])  # 作者
    parent = relationship("Comment", remote_side=[id], backref="replies")  # 父评论和子回复
    ai_persona = relationship("AIPersona")
    editor = relationship("User", foreign_keys=[edited_by])
    likes = relationship("CommentLike", back_populates="comment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Comment(id={self.id}, post_id={self.post_id}, parent_id={self.parent_id})>"


Index(
    "uq_comments_one_ai_generated_per_post",
    Comment.post_id,
    unique=True,
    postgresql_where=Comment.is_ai_generated.is_(True),
)
