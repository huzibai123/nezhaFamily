"""
日历事件相关的 Pydantic Schema
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID

from app.models.event import EventType


class EventCreate(BaseModel):
    """创建事件请求"""
    title: str = Field(
        ..., min_length=1, max_length=200, description="事件标题"
    )
    description: Optional[str] = Field(None, description="事件描述")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    is_all_day: bool = Field(False, description="是否全天事件")
    event_type: EventType = Field(..., description="事件类型")
    location: Optional[str] = Field(
        None, max_length=200, description="事件地点"
    )
    reminder_minutes: Optional[int] = Field(None, description="提前提醒分钟数")
    recurrence_rule: Optional[str] = Field(None, description="重复规则")


class EventUpdate(BaseModel):
    """更新事件请求"""
    title: Optional[str] = Field(
        None, min_length=1, max_length=200, description="事件标题"
    )
    description: Optional[str] = Field(None, description="事件描述")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    is_all_day: Optional[bool] = Field(None, description="是否全天事件")
    event_type: Optional[EventType] = Field(None, description="事件类型")
    location: Optional[str] = Field(
        None, max_length=200, description="事件地点"
    )
    reminder_minutes: Optional[int] = Field(None, description="提前提醒分钟数")
    recurrence_rule: Optional[str] = Field(None, description="重复规则")


class EventResponse(BaseModel):
    """事件响应"""
    id: UUID
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: Optional[datetime]
    is_all_day: bool
    event_type: EventType
    location: Optional[str]
    reminder_minutes: Optional[int]
    recurrence_rule: Optional[str]
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
