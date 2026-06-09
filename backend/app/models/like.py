"""
点赞模型
支持对帖子和评论点赞，防止重复点赞
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.db.base import Base


class Like(Base):
    """点赞表"""
    __tablename__ = "likes"

    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 点赞用户
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # 点赞目标类型：post（帖子）或 comment（评论）
    target_type = Column(String(20), nullable=False)

    # 点赞目标 ID（可以是 post_id 或 comment_id）
    target_id = Column(UUID(as_uuid=True), nullable=False)

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # 唯一约束：同一用户不能对同一目标重复点赞
    __table_args__ = (
        UniqueConstraint("user_id", "target_type", "target_id", name="uq_user_target"),
    )

    # 关系定义
    user = relationship("User", back_populates="likes")  # 点赞用户

    def __repr__(self):
        return f"<Like(user_id={self.user_id}, target_type={self.target_type}, target_id={self.target_id})>"
