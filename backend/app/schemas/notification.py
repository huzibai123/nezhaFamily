"""
通知相关的 Pydantic Schema
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    """通知响应"""

    id: UUID
    recipient_id: UUID
    actor_id: UUID
    actor_username: Optional[str] = None
    actor_avatar_url: Optional[str] = None
    type: str
    target_type: str
    target_id: UUID
    post_id: Optional[UUID]
    message: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    """通知列表响应"""

    notifications: List[NotificationResponse]
    unread_count: int
    total: int
    page: int
    page_size: int
    has_more: bool
