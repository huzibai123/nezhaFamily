"""
通知 API 测试
覆盖发布、评论、回复、点赞触发的真实通知流。
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.ai import AIPersona
from app.models.comment import Comment
from app.models.notification import Notification
from app.models.post import Post
from app.models.user import User


def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(data={"user_id": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_notifications_follow_family_interactions(
    client: AsyncClient,
    db: AsyncSession,
    test_admin: User,
    test_user: User,
):
    """测试帖子、评论、回复和点赞都会给对应成员生成通知。"""
    post_response = await client.post(
        "/api/v1/posts",
        json={"content": "今天的小记忆", "media": []},
        headers=auth_headers(test_user),
    )

    assert post_response.status_code == 201
    post_id = post_response.json()["id"]

    admin_notifications = await client.get(
        "/api/v1/notifications",
        headers=auth_headers(test_admin),
    )
    assert admin_notifications.status_code == 200
    assert admin_notifications.json()["unread_count"] == 1
    assert admin_notifications.json()["notifications"][0]["type"] == "new_post"

    comment_response = await client.post(
        f"/api/v1/posts/{post_id}/comments",
        json={"content": "看到了，很开心"},
        headers=auth_headers(test_admin),
    )

    assert comment_response.status_code == 201
    comment_id = comment_response.json()["id"]

    reply_response = await client.post(
        f"/api/v1/posts/{post_id}/comments",
        json={"content": "我也开心", "parent_id": comment_id},
        headers=auth_headers(test_user),
    )

    assert reply_response.status_code == 201

    like_response = await client.post(
        f"/api/v1/posts/{post_id}/like",
        headers=auth_headers(test_admin),
    )

    assert like_response.status_code == 200
    assert like_response.json()["liked"] is True

    user_notifications = await client.get(
        "/api/v1/notifications",
        headers=auth_headers(test_user),
    )
    user_payload = user_notifications.json()
    user_types = [item["type"] for item in user_payload["notifications"]]

    assert user_notifications.status_code == 200
    assert user_payload["unread_count"] == 2
    assert "comment" in user_types
    assert "like_post" in user_types

    refreshed_admin_notifications = await client.get(
        "/api/v1/notifications",
        headers=auth_headers(test_admin),
    )
    admin_types = [
        item["type"]
        for item in refreshed_admin_notifications.json()["notifications"]
    ]

    assert "new_post" in admin_types
    assert "reply" in admin_types

    read_all_response = await client.patch(
        "/api/v1/notifications/read-all",
        headers=auth_headers(test_user),
    )

    assert read_all_response.status_code == 200
    assert read_all_response.json()["updated_count"] == 2


@pytest.mark.asyncio
async def test_like_notification_dedupes_repeated_likes(
    client: AsyncClient,
    db: AsyncSession,
    test_admin: User,
    test_user: User,
):
    """测试同一成员重复点赞同一帖子不会重复制造提醒。"""
    post = Post(author_id=test_user.id, content="需要去重的帖子", media_urls=[])
    db.add(post)
    await db.commit()
    await db.refresh(post)

    for _ in range(3):
        response = await client.post(
            f"/api/v1/posts/{post.id}/like",
            headers=auth_headers(test_admin),
        )
        assert response.status_code == 200

        response = await client.post(
            f"/api/v1/posts/{post.id}/like",
            headers=auth_headers(test_admin),
        )
        assert response.status_code == 200

    result = await db.execute(
        select(Notification).where(
            Notification.recipient_id == test_user.id,
            Notification.type == "like_post",
            Notification.target_id == post.id,
        )
    )
    notifications = result.scalars().all()

    assert len(notifications) == 1


@pytest.mark.asyncio
async def test_notifications_filter_by_type(
    client: AsyncClient,
    db: AsyncSession,
    test_admin: User,
    test_user: User,
):
    """测试通知中心可按通知类型筛选。"""
    db.add_all(
        [
            Notification(
                recipient_id=test_user.id,
                actor_id=test_admin.id,
                type="comment",
                target_type="post",
                target_id=test_admin.id,
                post_id=None,
                message="评论提醒",
            ),
            Notification(
                recipient_id=test_user.id,
                actor_id=test_admin.id,
                type="reply",
                target_type="comment",
                target_id=test_admin.id,
                post_id=None,
                message="回复提醒",
            ),
        ]
    )
    await db.commit()

    response = await client.get(
        "/api/v1/notifications",
        params={"type": "reply"},
        headers=auth_headers(test_user),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["notifications"][0]["type"] == "reply"


@pytest.mark.asyncio
async def test_reply_notification_skips_actor_self(
    client: AsyncClient,
    db: AsyncSession,
    test_user: User,
):
    """测试回复自己的评论不会给自己生成通知。"""
    post = Post(author_id=test_user.id, content="自己的帖子", media_urls=[])
    db.add(post)
    await db.flush()

    comment = Comment(
        post_id=post.id,
        author_id=test_user.id,
        content="自己的评论",
    )
    db.add(comment)
    await db.commit()
    await db.refresh(post)
    await db.refresh(comment)

    response = await client.post(
        f"/api/v1/posts/{post.id}/comments",
        json={"content": "自己回复自己", "parent_id": str(comment.id)},
        headers=auth_headers(test_user),
    )

    assert response.status_code == 201

    result = await db.execute(
        select(Notification).where(Notification.recipient_id == test_user.id)
    )

    assert result.scalars().all() == []


@pytest.mark.asyncio
async def test_ai_notification_response_uses_persona_display_name(
    client: AsyncClient,
    db: AsyncSession,
    test_user: User,
):
    """AI 系统用户通知展示 persona 名称，而不是内部账号名。"""
    ai_user = User(
        username="ai_61855",
        email="ai_61855@ai.nezha.local",
        password_hash="!",
        role="member",
        is_system=True,
        system_type="ai_persona",
        role_in_family="内部角色",
    )
    db.add(ai_user)
    await db.flush()
    persona = AIPersona(
        user_id=ai_user.id,
        name="小金毛",
        persona_type="pet_dog",
        avatar_url="/media/ai-dog.png",
        enabled=True,
    )
    post = Post(author_id=test_user.id, content="一条有 AI 点赞的动态", media_urls=[])
    db.add_all([persona, post])
    await db.flush()
    notification = Notification(
        recipient_id=test_user.id,
        actor_id=ai_user.id,
        type="like_post",
        target_type="post",
        target_id=post.id,
        post_id=post.id,
        message="小金毛 点赞了你的帖子",
    )
    db.add(notification)
    await db.commit()

    response = await client.get(
        "/api/v1/notifications",
        headers=auth_headers(test_user),
    )

    assert response.status_code == 200
    payload = response.json()["notifications"][0]
    assert payload["actor_username"] == "小金毛"
    assert payload["actor_avatar_url"].startswith("/media/ai-dog.png?token=")
    assert payload["actor_username"] != "ai_61855"
