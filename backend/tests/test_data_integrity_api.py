"""
数据一致性与并发行为测试
"""
import asyncio
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.security import create_access_token
from app.db.session import get_db
from app.main import app
from app.models.ai import AIPersona
from app.models.comment import Comment
from app.models.event import Event
from app.models.like import CommentLike, PostLike
from app.models.media import MediaFile
from app.models.post import Post
from app.models.user import User
from app.services.ai_housekeeper import ensure_default_personas


async def run_with_isolated_request_sessions(test_engine, callback):
    """让每个 ASGI 请求独立创建 AsyncSession，便于并发测试。"""
    TestingSession = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_db():
        async with TestingSession() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as isolated_client:
            return await callback(isolated_client)
    finally:
        app.dependency_overrides.clear()


def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(data={"user_id": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_concurrent_like_toggle_does_not_raise_500(
    test_engine,
    db: AsyncSession,
    test_user: User,
    test_admin: User,
):
    """并发点赞同一目标不应触发唯一约束 500。"""
    post = Post(author_id=test_admin.id, content="需要被点赞的动态", media_urls=[])
    db.add(post)
    await db.commit()
    await db.refresh(post)

    async def scenario(isolated_client: AsyncClient):
        return await asyncio.gather(
            isolated_client.post(
                f"/api/v1/posts/{post.id}/like",
                headers=auth_headers(test_user),
            ),
            isolated_client.post(
                f"/api/v1/posts/{post.id}/like",
                headers=auth_headers(test_user),
            ),
        )

    responses = await run_with_isolated_request_sessions(test_engine, scenario)
    assert [response.status_code for response in responses] == [200, 200]

    result = await db.execute(
        select(PostLike).where(
            PostLike.user_id == test_user.id,
            PostLike.post_id == post.id,
        )
    )
    assert len(result.scalars().all()) <= 1


@pytest.mark.asyncio
async def test_concurrent_comments_keep_post_comment_count(
    test_engine,
    db: AsyncSession,
    test_user: User,
):
    """并发评论后 Post.comment_count 与实际评论数一致。"""
    post = Post(author_id=test_user.id, content="可评论动态", media_urls=[])
    db.add(post)
    await db.commit()
    await db.refresh(post)

    async def scenario(isolated_client: AsyncClient):
        return await asyncio.gather(
            isolated_client.post(
                f"/api/v1/posts/{post.id}/comments",
                headers=auth_headers(test_user),
                json={"content": "第一条评论"},
            ),
            isolated_client.post(
                f"/api/v1/posts/{post.id}/comments",
                headers=auth_headers(test_user),
                json={"content": "第二条评论"},
            ),
        )

    responses = await run_with_isolated_request_sessions(test_engine, scenario)
    assert [response.status_code for response in responses] == [201, 201]

    await db.refresh(post)
    comment_count = await db.scalar(
        select(func.count()).select_from(Comment).where(Comment.post_id == post.id)
    )
    assert post.comment_count == 2
    assert comment_count == 2


@pytest.mark.asyncio
async def test_delete_post_removes_comment_likes(
    client: AsyncClient,
    db: AsyncSession,
    test_user: User,
    test_admin: User,
):
    """删帖时清理帖子下评论的多态点赞记录。"""
    post = Post(author_id=test_admin.id, content="待删除动态", media_urls=[])
    comment = Comment(post=post, author_id=test_user.id, content="会被删的评论")
    db.add_all([post, comment])
    await db.flush()
    comment_like = CommentLike(
        user_id=test_admin.id,
        comment_id=comment.id,
    )
    db.add(comment_like)
    await db.commit()
    await db.refresh(post)

    response = await client.delete(
        f"/api/v1/posts/{post.id}",
        headers=auth_headers(test_admin),
    )
    assert response.status_code == 204

    orphan_like = await db.scalar(
        select(CommentLike).where(
            CommentLike.comment_id == comment.id,
        )
    )
    assert orphan_like is None


@pytest.mark.asyncio
async def test_delete_comment_removes_nested_descendants_and_likes(
    client: AsyncClient,
    db: AsyncSession,
    test_user: User,
):
    """删除父评论时显式删除所有后代评论和对应点赞。"""
    post = Post(
        author_id=test_user.id,
        content="有嵌套评论的动态",
        media_urls=[],
        comment_count=3,
    )
    root = Comment(post=post, author_id=test_user.id, content="父评论")
    db.add_all([post, root])
    await db.flush()
    reply = Comment(
        post_id=post.id,
        author_id=test_user.id,
        content="子回复",
        parent_id=root.id,
    )
    db.add(reply)
    await db.flush()
    nested_reply = Comment(
        post_id=post.id,
        author_id=test_user.id,
        content="孙回复",
        parent_id=reply.id,
    )
    db.add(nested_reply)
    await db.flush()
    db.add(
        CommentLike(
            user_id=test_user.id,
            comment_id=nested_reply.id,
        )
    )
    post_id = post.id
    root_id = root.id
    await db.commit()
    await db.refresh(post)

    response = await client.delete(
        f"/api/v1/comments/{root_id}",
        headers=auth_headers(test_user),
    )

    assert response.status_code == 204
    remaining_comments = await db.scalar(
        select(func.count()).select_from(Comment).where(Comment.post_id == post_id)
    )
    remaining_likes = await db.scalar(
        select(func.count()).select_from(CommentLike)
    )
    await db.refresh(post)
    assert remaining_comments == 0
    assert remaining_likes == 0
    assert post.comment_count == 0


@pytest.mark.asyncio
async def test_user_delete_sets_editor_and_media_deleted_by_to_null(
    db: AsyncSession,
    test_admin: User,
):
    """删除编辑者/删除者用户时，审计字段应置空而不是阻塞删除。"""
    actor = User(
        username="cleanupactor",
        email="cleanupactor@test.com",
        password_hash="!",
        role="member",
    )
    post = Post(author_id=test_admin.id, content="审计字段测试", media_urls=[])
    db.add_all([actor, post])
    await db.flush()
    comment = Comment(
        post_id=post.id,
        author_id=test_admin.id,
        content="被编辑过的评论",
        edited_by=actor.id,
    )
    media = MediaFile(
        uploader_id=test_admin.id,
        file_type="image",
        file_path="/media/deleted-by.jpg",
        deleted_by=actor.id,
    )
    db.add_all([comment, media])
    await db.flush()
    comment_id = comment.id
    media_id = media.id

    await db.delete(actor)
    await db.commit()

    await db.refresh(comment)
    await db.refresh(media)
    assert comment.id == comment_id
    assert media.id == media_id
    assert comment.edited_by is None
    assert media.deleted_by is None


@pytest.mark.asyncio
async def test_user_delete_cascades_created_events(
    db: AsyncSession,
):
    """Event.created_by 的 ORM 与数据库约束都应保持 CASCADE。"""
    creator = User(
        username="eventcreator",
        email="eventcreator@test.com",
        password_hash="!",
        role="member",
    )
    db.add(creator)
    await db.flush()
    event = Event(
        title="会随创建者删除的事件",
        start_time=datetime.now(timezone.utc),
        created_by=creator.id,
    )
    db.add(event)
    await db.flush()
    event_id = event.id

    await db.delete(creator)
    await db.commit()

    assert await db.get(Event, event_id) is None


@pytest.mark.asyncio
async def test_user_delete_sets_invited_by_to_null(
    db: AsyncSession,
):
    """删除邀请人不应阻塞被邀请成员保留。"""
    inviter = User(
        username="inviter",
        email="inviter@test.com",
        password_hash="!",
        role="member",
    )
    invitee = User(
        username="invitee",
        email="invitee@test.com",
        password_hash="!",
        role="member",
        inviter=inviter,
    )
    db.add_all([inviter, invitee])
    await db.flush()
    invitee_id = invitee.id

    await db.delete(inviter)
    await db.commit()

    persisted_invitee = await db.get(User, invitee_id)
    assert persisted_invitee is not None
    assert persisted_invitee.invited_by is None


@pytest.mark.asyncio
async def test_concurrent_default_persona_initialization_creates_one_set(test_engine):
    """默认 persona 首次初始化需通过 advisory lock 串行化，避免并发重复创建。"""
    TestingSession = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def initialize_once():
        async with TestingSession() as session:
            personas = await ensure_default_personas(session)
            await session.commit()
            return [persona.id for persona in personas]

    await asyncio.gather(initialize_once(), initialize_once())

    async with TestingSession() as session:
        persona_count = await session.scalar(select(func.count()).select_from(AIPersona))
        system_user_count = await session.scalar(
            select(func.count())
            .select_from(User)
            .where(User.is_system.is_(True), User.system_type == "ai_persona")
        )

    assert persona_count == 3
    assert system_user_count == 3
