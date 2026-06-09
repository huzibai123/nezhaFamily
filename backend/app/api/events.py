"""
日历事件相关的 API 路由
"""
from typing import Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy import select, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.models.event import Event, EventType
from app.core.security import get_current_user
from app.schemas.event import EventCreate, EventUpdate, EventResponse

router = APIRouter()


@router.post("/events", response_model=EventResponse)
async def create_event(
    event_data: EventCreate = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建事件"""
    event = Event(
        title=event_data.title,
        description=event_data.description,
        start_time=event_data.start_time,
        end_time=event_data.end_time,
        is_all_day=event_data.is_all_day,
        event_type=event_data.event_type,
        location=event_data.location,
        reminder_minutes=event_data.reminder_minutes,
        recurrence_rule=event_data.recurrence_rule,
        created_by=current_user.id,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


@router.get("/events")
async def get_events(
    year: int = Query(..., description="年份"),
    month: int = Query(..., description="月份"),
    event_type: Optional[EventType] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取事件列表（按月份查询）"""
    query = select(Event).where(
        extract("year", Event.start_time) == year,
        extract("month", Event.start_time) == month,
    )

    if event_type:
        query = query.where(Event.event_type == event_type)

    query = query.order_by(Event.start_time)
    result = await db.execute(query)
    events = result.scalars().all()

    return {
        "events": [EventResponse.model_validate(e) for e in events],
        "total": len(events),
    }


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个事件详情"""
    event = await db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")
    return event


@router.put("/events/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: UUID,
    event_data: EventUpdate = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新事件（仅创建者或管理员）"""
    event = await db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")

    # 权限校验：仅创建者或管理员可更新
    if event.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限修改此事件")

    update_data = event_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)

    await db.commit()
    await db.refresh(event)
    return event


@router.delete("/events/{event_id}")
async def delete_event(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除事件（仅创建者或管理员）"""
    event = await db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")

    # 权限校验：仅创建者或管理员可删除
    if event.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限删除此事件")

    await db.delete(event)
    await db.commit()

    return {"message": "删除成功"}
