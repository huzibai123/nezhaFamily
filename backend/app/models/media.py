"""
媒体文件模型
存储图片和视频的元数据
"""
from sqlalchemy import Column, String, Integer, BigInteger, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.db.base import Base


class MediaFile(Base):
    """媒体文件表"""
    __tablename__ = "media_files"
    __table_args__ = (
        Index("idx_media_files_created_at", "created_at"),
        Index("idx_media_files_file_type", "file_type"),
    )

    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 上传者
    uploader_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # 文件类型：image（图片）或 video（视频）
    file_type = Column(String(20), nullable=False)

    # 文件信息
    original_name = Column(String(255), nullable=True)  # 原始文件名
    file_path = Column(String(500), nullable=False)  # 存储路径
    thumbnail_path = Column(String(500), nullable=True)  # 缩略图路径（仅图片）

    # 文件属性
    file_size = Column(BigInteger, nullable=True)  # 文件大小（字节）
    mime_type = Column(String(100), nullable=True)  # MIME 类型

    # 媒体属性
    width = Column(Integer, nullable=True)  # 宽度（像素）
    height = Column(Integer, nullable=True)  # 高度（像素）
    duration = Column(Integer, nullable=True)  # 视频时长（秒）

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # 关系定义
    uploader = relationship("User", back_populates="media_files")  # 上传者
    # 所属相册（多对多，通过 album_media 关联表，与 Album.media_files 对称）
    albums = relationship(
        "Album", secondary="album_media", back_populates="media_files"
    )

    def __repr__(self):
        return f"<MediaFile(id={self.id}, file_type={self.file_type}, file_path={self.file_path})>"
