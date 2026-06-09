"""
媒体文件相关的 Pydantic Schema
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class MediaUploadItem(BaseModel):
    """上传媒体项"""
    id: UUID
    url: str = Field(..., description="签名后的媒体文件 URL")
    raw_url: str = Field(..., description="原始媒体文件 URL，用于持久化")
    type: str = Field(..., description="媒体类型：image 或 video")


class MediaUploadResponse(BaseModel):
    """媒体上传响应"""
    files: list[MediaUploadItem]


class MediaResponse(BaseModel):
    """单个媒体文件详情响应"""
    id: UUID
    url: str = Field(..., description="媒体文件 URL")
    type: str = Field(..., description="媒体类型：image 或 video")
    original_name: Optional[str] = Field(None, description="原始文件名")
    file_size: Optional[int] = Field(None, description="文件大小（字节）")
    mime_type: Optional[str] = Field(None, description="MIME 类型")
    width: Optional[int] = Field(None, description="宽度（像素）")
    height: Optional[int] = Field(None, description="高度（像素）")
    duration: Optional[int] = Field(None, description="视频时长（秒）")
    created_at: datetime = Field(..., description="创建时间")

    model_config = {"from_attributes": True}


class MediaSearchUploader(BaseModel):
    """媒体搜索结果中的上传者摘要"""
    id: UUID
    username: str
    avatar_url: Optional[str] = None
    role_in_family: Optional[str] = None


class MediaSearchItem(BaseModel):
    """媒体搜索结果项"""
    id: UUID
    url: str = Field(..., description="签名后的媒体文件 URL")
    thumbnail_url: Optional[str] = Field(None, description="签名后的缩略图 URL")
    type: str = Field(..., description="媒体类型：image 或 video")
    original_name: Optional[str] = Field(None, description="原始文件名")
    file_size: Optional[int] = Field(None, description="文件大小（字节）")
    mime_type: Optional[str] = Field(None, description="MIME 类型")
    width: Optional[int] = Field(None, description="宽度（像素）")
    height: Optional[int] = Field(None, description="高度（像素）")
    duration: Optional[int] = Field(None, description="视频时长（秒）")
    created_at: datetime = Field(..., description="创建时间")
    uploader: MediaSearchUploader


class MediaSearchResponse(BaseModel):
    """媒体搜索响应"""
    media: list[MediaSearchItem]
    uploaders: list[MediaSearchUploader] = Field(
        default_factory=list,
        description="当前搜索条件下可选的上传者列表，不受分页和 uploader_id 限制",
    )
    total: int
    page: int
    page_size: int
    has_more: bool
