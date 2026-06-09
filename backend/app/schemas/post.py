"""
帖子相关的 Pydantic Schema
用于请求验证和响应序列化
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator
from uuid import UUID


EMPTY_POST_MESSAGE = "帖子内容和媒体不能同时为空"


def has_post_text(content: Optional[str]) -> bool:
    """判断帖子是否有有效文字内容。"""
    return bool(content and content.strip())


def has_post_media(media: Optional[List["MediaItem"]]) -> bool:
    """判断帖子是否有媒体内容。"""
    return bool(media)


class MediaItem(BaseModel):
    """媒体项（图片或视频）"""
    type: str = Field(..., description="媒体类型：image 或 video")
    url: str = Field(..., description="媒体 URL")
    thumbnail_url: Optional[str] = Field(None, description="缩略图 URL（视频）")
    width: Optional[int] = Field(None, description="宽度")
    height: Optional[int] = Field(None, description="高度")

    @model_validator(mode="before")
    @classmethod
    def normalize_thumbnail(cls, data):
        """兼容旧格式：存储用 thumbnail，Schema 用 thumbnail_url"""
        if isinstance(data, dict) and "thumbnail" in data and "thumbnail_url" not in data:
            data["thumbnail_url"] = data["thumbnail"]
        return data


class PostCreate(BaseModel):
    """创建帖子请求"""
    content: Optional[str] = Field(None, max_length=5000, description="帖子内容")
    media: Optional[List[MediaItem]] = Field(default=None, description="媒体列表")

    @model_validator(mode="after")
    def validate_not_empty(self):
        """帖子至少需要文字或媒体之一。"""
        if not has_post_text(self.content) and not has_post_media(self.media):
            raise ValueError(EMPTY_POST_MESSAGE)
        return self


class PostUpdate(BaseModel):
    """更新帖子请求"""
    content: Optional[str] = Field(None, max_length=5000, description="帖子内容")
    media: Optional[List[MediaItem]] = Field(None, description="媒体列表")


class PostResponse(BaseModel):
    """帖子响应"""
    id: UUID
    author_id: UUID
    author_username: str
    author_avatar_url: Optional[str]
    content: str
    media_urls: List[MediaItem]
    like_count: int
    comment_count: int
    is_liked: bool  # 当前用户是否已点赞
    created_at: datetime
    updated_at: datetime

    @field_validator("content", mode="before")
    @classmethod
    def normalize_content(cls, value):
        """数据库中纯媒体帖 content 可能为 None，响应统一为空字符串。"""
        return "" if value is None else value

    model_config = {"from_attributes": True}


class PostListResponse(BaseModel):
    """帖子列表响应"""
    posts: List[PostResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
