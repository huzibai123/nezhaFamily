"""
通知模型
记录家庭成员之间的评论、回复、点赞和新帖子提醒
"""
from datetime import datetime, timezone
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Notification(Base):
    """通知表"""
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type = Column(String(30), nullable=False)
    target_type = Column(String(30), nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=False)
    post_id = Column(
        UUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    target_deleted = Column(Boolean, nullable=False, default=False, index=True)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    recipient = relationship(
        "User",
        foreign_keys=[recipient_id],
    )
    actor = relationship(
        "User",
        foreign_keys=[actor_id],
    )
    post = relationship("Post")

    __table_args__ = (
        Index(
            "idx_notifications_recipient_read_created",
            "recipient_id",
            "is_read",
            "created_at",
        ),
        Index(
            "idx_notifications_dedupe",
            "recipient_id",
            "actor_id",
            "type",
            "target_type",
            "target_id",
        ),
    )

    def __repr__(self):
        return f"<Notification(id={self.id}, recipient_id={self.recipient_id}, type={self.type})>"
