"""
相册模型
"""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.db.base import Base

# 相册-媒体文件关联表
album_media = Table(
    'album_media',
    Base.metadata,
    Column('album_id', UUID(as_uuid=True), ForeignKey('albums.id', ondelete='CASCADE'), primary_key=True),
    Column('media_id', UUID(as_uuid=True), ForeignKey('media_files.id', ondelete='CASCADE'), primary_key=True),
    Column('added_at', DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False),
)

class Album(Base):
    """相册表"""
    __tablename__ = "albums"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    cover_image_url = Column(String(500), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # 关系
    creator = relationship("User", back_populates="albums")
    media_files = relationship("MediaFile", secondary=album_media, back_populates="albums")
