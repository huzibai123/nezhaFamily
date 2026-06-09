"""
相册相关的 Pydantic Schema
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class AlbumCreate(BaseModel):
    """创建相册请求"""
    name: str = Field(..., min_length=1, max_length=100, description="相册名称")
    description: Optional[str] = Field(None, description="相册描述")
    cover_image_url: Optional[str] = Field(None, description="封面图 URL")


class AlbumUpdate(BaseModel):
    """更新相册请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="相册名称")
    description: Optional[str] = Field(None, description="相册描述")
    cover_image_url: Optional[str] = Field(None, description="封面图 URL")


class AlbumMediaItem(BaseModel):
    """相册中的媒体项"""
    id: UUID
    url: str = Field(..., description="媒体文件 URL")
    type: str = Field(..., description="媒体类型：image 或 video")


class AlbumResponse(BaseModel):
    """相册响应"""
    id: UUID
    name: str
    description: Optional[str]
    cover_image_url: Optional[str]
    created_by: UUID
    created_at: datetime
    media_count: int = Field(..., description="媒体文件数量")

    model_config = {"from_attributes": True}


class AlbumDetailResponse(BaseModel):
    """相册详情响应（含媒体列表）"""
    id: UUID
    name: str
    description: Optional[str]
    cover_image_url: Optional[str]
    created_by: UUID
    created_at: datetime
    media: list[AlbumMediaItem] = Field(..., description="相册中的媒体列表")

    model_config = {"from_attributes": True}
