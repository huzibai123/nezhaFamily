"""
通知中心 API 与通知生成 helper
"""
from typing import Iterable, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.ai import AIPersona
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationListResponse, NotificationResponse

router = APIRouter()


def _actor_name(actor: User) -> str:
    return actor.role_in_family or actor.username


async def _ai_personas_for_actors(db: AsyncSession, actor_ids: Iterable[UUID]) -> dict[UUID, AIPersona]:
    ids = list(set(actor_ids))
    if not ids:
        return {}
    result = await db.execute(select(AIPersona).where(AIPersona.user_id.in_(ids)))
    return {persona.user_id: persona for persona in result.scalars().all() if persona.user_id}


def _notification_actor_display(actor: User, persona: AIPersona | None = None) -> tuple[str, str | None]:
    if actor.is_system and actor.system_type == "ai_persona" and persona:
        return persona.name, persona.avatar_url
    return _actor_name(actor), actor.avatar_url


def _notification_response(
    notification: Notification,
    actor: User,
    *,
    persona: AIPersona | None = None,
) -> NotificationResponse:
    actor_username, actor_avatar_url = _notification_actor_display(actor, persona)
    return NotificationResponse(
        id=notification.id,
        recipient_id=notification.recipient_id,
        actor_id=notification.actor_id,
        actor_username=actor_username,
        actor_avatar_url=actor_avatar_url,
        type=notification.type,
        target_type=notification.target_type,
        target_id=notification.target_id,
        post_id=notification.post_id,
        message=notification.message,
        is_read=notification.is_read,
        created_at=notification.created_at,
    )


async def create_notification(
    db: AsyncSession,
    *,
    recipient_id: UUID,
    actor: User,
    notification_type: str,
    target_type: str,
    target_id: UUID,
    message: str,
    post_id: Optional[UUID] = None,
    dedupe: bool = False,
) -> Optional[Notification]:
    """创建单条通知；点赞等可用 dedupe 避免重复提醒。"""
    if recipient_id == actor.id:
        return None

    recipient = await db.get(User, recipient_id)
    if not recipient or recipient.is_system:
        return None

    if dedupe:
        existing_query = select(Notification.id).where(
            Notification.recipient_id == recipient_id,
            Notification.actor_id == actor.id,
            Notification.type == notification_type,
            Notification.target_type == target_type,
            Notification.target_id == target_id,
        )
        existing_result = await db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            return None

    notification = Notification(
        recipient_id=recipient_id,
        actor_id=actor.id,
        type=notification_type,
        target_type=target_type,
        target_id=target_id,
        post_id=post_id,
        message=message,
        is_read=False,
    )
    db.add(notification)
    return notification


async def create_notifications_for_recipients(
    db: AsyncSession,
    *,
    recipient_ids: Iterable[UUID],
    actor: User,
    notification_type: str,
    target_type: str,
    target_id: UUID,
    message: str,
    post_id: Optional[UUID] = None,
    dedupe: bool = False,
) -> None:
    """批量创建通知，自动去掉 actor 自己和重复 recipient。"""
    seen: set[UUID] = set()
    for recipient_id in recipient_ids:
        if recipient_id in seen:
            continue
        seen.add(recipient_id)
        await create_notification(
            db,
            recipient_id=recipient_id,
            actor=actor,
            notification_type=notification_type,
            target_type=target_type,
            target_id=target_id,
            message=message,
            post_id=post_id,
            dedupe=dedupe,
        )


@router.get("/notifications", response_model=NotificationListResponse)
async def get_notifications(
    unread_only: bool = False,
    notification_type: Optional[str] = Query(None, alias="type", max_length=30),
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户通知列表和未读数量"""
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20

    conditions = [Notification.recipient_id == current_user.id]
    if unread_only:
        conditions.append(Notification.is_read.is_(False))
    if notification_type:
        conditions.append(Notification.type == notification_type)

    count_query = select(func.count()).select_from(Notification).where(*conditions)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    unread_count_query = select(func.count()).select_from(Notification).where(
        Notification.recipient_id == current_user.id,
        Notification.is_read.is_(False),
    )
    unread_count_result = await db.execute(unread_count_query)
    unread_count = unread_count_result.scalar() or 0

    offset = (page - 1) * page_size
    query = (
        select(Notification, User)
        .join(User, User.id == Notification.actor_id)
        .where(*conditions)
        .order_by(desc(Notification.created_at))
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    rows = result.all()
    personas = await _ai_personas_for_actors(db, [actor.id for _notification, actor in rows])

    notifications = [
        _notification_response(notification, actor, persona=personas.get(actor.id))
        for notification, actor in rows
    ]

    return NotificationListResponse(
        notifications=notifications,
        unread_count=unread_count,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + len(notifications)) < total,
    )


@router.patch("/notifications/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """标记当前用户所有通知为已读"""
    result = await db.execute(
        update(Notification)
        .where(
            Notification.recipient_id == current_user.id,
            Notification.is_read.is_(False),
        )
        .values(is_read=True)
    )
    await db.commit()

    return {"success": True, "updated_count": result.rowcount or 0}


@router.patch("/notifications/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """标记单条通知为已读"""
    query = (
        select(Notification, User)
        .join(User, User.id == Notification.actor_id)
        .where(
            Notification.id == notification_id,
            Notification.recipient_id == current_user.id,
        )
    )
    result = await db.execute(query)
    row = result.one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="通知不存在")

    notification, actor = row
    notification.is_read = True
    await db.commit()
    await db.refresh(notification)

    personas = await _ai_personas_for_actors(db, [actor.id])
    return _notification_response(notification, actor, persona=personas.get(actor.id))


def build_comment_message(actor: User) -> str:
    return f"{_actor_name(actor)} 评论了你的帖子"


def build_reply_message(actor: User) -> str:
    return f"{_actor_name(actor)} 回复了你的评论"


def build_like_post_message(actor: User) -> str:
    return f"{_actor_name(actor)} 点赞了你的帖子"


def build_like_comment_message(actor: User) -> str:
    return f"{_actor_name(actor)} 点赞了你的评论"


def build_new_post_message(actor: User) -> str:
    return f"{_actor_name(actor)} 发布了新帖子"
