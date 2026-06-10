"""
评论相关的 Pydantic Schema
用于请求验证和响应序列化
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class CommentCreate(BaseModel):
    """创建评论请求"""
    content: str = Field(..., min_length=1, max_length=1000, description="评论内容")
    parent_id: Optional[UUID] = Field(None, description="父评论 ID（回复评论时使用）")


class CommentUpdate(BaseModel):
    """评论更新请求（管理员可用于修正 AI 评论）"""
    content: str = Field(..., min_length=1, max_length=1000, description="评论内容")


class CommentResponse(BaseModel):
    """评论响应"""
    id: UUID
    post_id: UUID
    author_id: UUID
    author_username: str
    author_avatar_url: Optional[str]
    content: str
    parent_id: Optional[UUID]
    like_count: int
    is_liked: bool  # 当前用户是否已点赞
    created_at: datetime
    updated_at: datetime
    is_ai_generated: bool = False
    ai_persona_id: Optional[UUID] = None
    edited_by: Optional[UUID] = None
    edited_at: Optional[datetime] = None

    # 嵌套回复（只展示一层）
    replies: Optional[List['CommentResponse']] = None

    model_config = {"from_attributes": True}


class CommentListResponse(BaseModel):
    """评论列表响应"""
    comments: List[CommentResponse]
    total: int
