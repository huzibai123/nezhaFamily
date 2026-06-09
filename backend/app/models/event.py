"""
日历事件模型
"""
from sqlalchemy import (
    Column, String, DateTime, Text, Boolean,
    Integer, Enum, ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum

from app.db.base import Base


class EventType(str, enum.Enum):
    """事件类型枚举"""
    BIRTHDAY = "birthday"
    ANNIVERSARY = "anniversary"
    ACTIVITY = "activity"
    APPOINTMENT = "appointment"
    HOLIDAY = "holiday"
    OTHER = "other"


class Event(Base):
    """事件表"""
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    is_all_day = Column(Boolean, default=False, nullable=False)
    event_type = Column(
        Enum(EventType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=EventType.ACTIVITY,
    )
    location = Column(String(200), nullable=True)
    reminder_minutes = Column(Integer, nullable=True)
    recurrence_rule = Column(String(200), nullable=True)
    created_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # 关系
    creator = relationship("User", back_populates="events")
