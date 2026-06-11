"""
帖子相关的 API 路由
"""
from datetime import date, datetime, time, timezone
from typing import Literal, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.models.post import Post
from app.models.comment import Comment
from app.models.like import Like
from app.schemas.post import (
    EMPTY_POST_MESSAGE,
    MediaItem,
    PostCreate,
    PostListResponse,
    PostResponse,
    PostUpdate,
    has_post_text,
)
from app.core.security import get_current_user
from app.core.media_utils import normalize_media_item_for_storage, sign_media_item_for_response
from app.api.notifications import build_new_post_message, create_notifications_for_recipients
from app.tasks.ai_housekeeper import generate_ai_comment

router = APIRouter()


def _response_content(content: str | None) -> str:
    """响应中纯媒体帖的 content 统一为空字符串。"""
    return content or ""


def _normalize_pagination(page: int, page_size: int) -> tuple[int, int]:
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20
    return page, page_size


def _post_filters(
    *,
    q: Optional[str],
    author_id: Optional[UUID],
    post_type: Optional[Literal["image", "video", "text"]],
    date_from: Optional[date],
    date_to: Optional[date],
) -> list:
    filters = []
    keyword = q.strip() if q else ""
    if keyword:
        like_keyword = f"%{keyword}%"
        filters.append(
            or_(
                Post.content.ilike(like_keyword),
                User.username.ilike(like_keyword),
            )
        )
    if author_id:
        filters.append(Post.author_id == author_id)
    if post_type == "text":
        filters.append(
            or_(
                Post.media_urls.is_(None),
                func.jsonb_array_length(Post.media_urls) == 0,
            )
        )
    elif post_type in {"image", "video"}:
        filters.append(Post.media_urls.contains([{"type": post_type}]))
    if date_from:
        filters.append(
            Post.created_at
            >= datetime.combine(date_from, time.min, tzinfo=timezone.utc)
        )
    if date_to:
        filters.append(
            Post.created_at
            <= datetime.combine(date_to, time.max, tzinfo=timezone.utc)
        )
    return filters


@router.post("/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建帖子"""
    # 创建帖子
    post = Post(
        author_id=current_user.id,
        content=post_data.content,
        media_urls=(
            [normalize_media_item_for_storage(m.model_dump()) for m in post_data.media]
            if post_data.media
            else []
        ),
    )

    db.add(post)
    await db.flush()

    members_query = select(User.id).where(
        User.id != current_user.id,
        User.is_system.is_(False),
    )
    members_result = await db.execute(members_query)
    await create_notifications_for_recipients(
        db,
        recipient_ids=members_result.scalars().all(),
        actor=current_user,
        notification_type="new_post",
        target_type="post",
        target_id=post.id,
        post_id=post.id,
        message=build_new_post_message(current_user),
        dedupe=True,
    )

    await db.commit()
    await db.refresh(post)
    try:
        generate_ai_comment.delay(str(post.id))
    except Exception:
        # AI 管家不可用不能影响发帖主流程。
        pass

    # 构造响应
    return PostResponse(
        id=post.id,
        author_id=post.author_id,
        author_username=current_user.username,
        author_avatar_url=current_user.avatar_url,
        content=_response_content(post.content),
        media_urls=[MediaItem(**sign_media_item_for_response(m)) for m in (post.media_urls or [])],
        like_count=0,
        comment_count=0,
        is_liked=False,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


@router.get("/posts", response_model=PostListResponse)
async def get_posts(
    page: int = 1,
    page_size: int = 20,
    q: Optional[str] = Query(None, max_length=100),
    author_id: Optional[UUID] = None,
    post_type: Optional[Literal["image", "video", "text"]] = Query(None, alias="type"),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取帖子列表（时间线）"""
    page, page_size = _normalize_pagination(page, page_size)

    offset = (page - 1) * page_size
    filters = _post_filters(
        q=q,
        author_id=author_id,
        post_type=post_type,
        date_from=date_from,
        date_to=date_to,
    )

    # 查询帖子总数
    count_query = select(func.count()).select_from(Post).join(User, User.id == Post.author_id)
    if filters:
        count_query = count_query.where(*filters)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 查询帖子列表
    query = (
        select(Post, User)
        .join(User, User.id == Post.author_id)
        .order_by(desc(Post.created_at))
        .offset(offset)
        .limit(page_size)
    )
    if filters:
        query = query.where(*filters)
    result = await db.execute(query)
    rows = result.all()
    posts = [post for post, _author in rows]
    authors = {post.id: author for post, author in rows}

    # 获取点赞信息
    post_ids = [post.id for post in posts]
    if post_ids:
        # 点赞数
        likes_count_query = (
            select(Like.target_id, func.count(Like.id).label('count'))
            .where(Like.target_type == 'post', Like.target_id.in_(post_ids))
            .group_by(Like.target_id)
        )
        likes_count_result = await db.execute(likes_count_query)
        likes_count = {row.target_id: row.count for row in likes_count_result}

        # 当前用户是否点赞
        user_likes_query = select(Like.target_id).where(
            Like.user_id == current_user.id,
            Like.target_type == 'post',
            Like.target_id.in_(post_ids)
        )
        user_likes_result = await db.execute(user_likes_query)
        user_likes = set(user_likes_result.scalars().all())
    else:
        likes_count = {}
        user_likes = set()

    # 构造响应
    post_responses = []
    for post in posts:
        author = authors.get(post.id)
        if not author:
            continue

        post_responses.append(PostResponse(
            id=post.id,
            author_id=post.author_id,
            author_username=author.username,
            author_avatar_url=author.avatar_url,
            content=_response_content(post.content),
            media_urls=[MediaItem(**sign_media_item_for_response(m)) for m in (post.media_urls or [])],
            like_count=likes_count.get(post.id, 0),
            comment_count=post.comment_count,
            is_liked=post.id in user_likes,
            created_at=post.created_at,
            updated_at=post.updated_at,
        ))

    return PostListResponse(
        posts=post_responses,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + len(posts)) < total,
    )


@router.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个帖子详情"""
    # 查询帖子
    query = select(Post).where(Post.id == post_id)
    result = await db.execute(query)
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    # 查询作者
    author_query = select(User).where(User.id == post.author_id)
    author_result = await db.execute(author_query)
    author = author_result.scalar_one_or_none()

    if not author:
        raise HTTPException(status_code=404, detail="作者不存在")

    # 查询点赞数
    likes_count_query = select(func.count()).select_from(Like).where(
        Like.target_type == 'post',
        Like.target_id == post_id
    )
    likes_count_result = await db.execute(likes_count_query)
    likes_count = likes_count_result.scalar() or 0

    # 查询当前用户是否点赞
    user_like_query = select(Like).where(
        Like.user_id == current_user.id,
        Like.target_type == 'post',
        Like.target_id == post_id
    )
    user_like_result = await db.execute(user_like_query)
    is_liked = user_like_result.scalar_one_or_none() is not None

    return PostResponse(
        id=post.id,
        author_id=post.author_id,
        author_username=author.username,
        author_avatar_url=author.avatar_url,
        content=_response_content(post.content),
        media_urls=[MediaItem(**sign_media_item_for_response(m)) for m in (post.media_urls or [])],
        like_count=likes_count,
        comment_count=post.comment_count,
        is_liked=is_liked,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


@router.put("/posts/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: UUID,
    post_data: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新帖子"""
    # 查询帖子
    query = select(Post).where(Post.id == post_id)
    result = await db.execute(query)
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    author = await db.get(User, post.author_id)
    can_edit_system_post = bool(
        current_user.role == "admin" and author and author.is_system
    )
    if post.author_id != current_user.id and not can_edit_system_post:
        raise HTTPException(status_code=403, detail="无权修改此帖子")

    content_was_provided = "content" in post_data.model_fields_set
    media_was_provided = "media" in post_data.model_fields_set

    next_content = post_data.content if content_was_provided else post.content
    next_media = post_data.media if media_was_provided else post.media_urls
    if not has_post_text(next_content) and not next_media:
        raise HTTPException(status_code=400, detail=EMPTY_POST_MESSAGE)

    # 更新字段
    if content_was_provided:
        post.content = post_data.content
    if media_was_provided:
        post.media_urls = [
            normalize_media_item_for_storage(m.model_dump())
            for m in (post_data.media or [])
        ]

    await db.commit()
    await db.refresh(post)

    # 查询点赞信息
    likes_count_query = select(func.count()).select_from(Like).where(
        Like.target_type == 'post',
        Like.target_id == post_id
    )
    likes_count_result = await db.execute(likes_count_query)
    likes_count = likes_count_result.scalar() or 0

    user_like_query = select(Like).where(
        Like.user_id == current_user.id,
        Like.target_type == 'post',
        Like.target_id == post_id
    )
    user_like_result = await db.execute(user_like_query)
    is_liked = user_like_result.scalar_one_or_none() is not None

    return PostResponse(
        id=post.id,
        author_id=post.author_id,
        author_username=author.username if author else current_user.username,
        author_avatar_url=author.avatar_url if author else current_user.avatar_url,
        content=_response_content(post.content),
        media_urls=[MediaItem(**sign_media_item_for_response(m)) for m in (post.media_urls or [])],
        like_count=likes_count,
        comment_count=post.comment_count,
        is_liked=is_liked,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除帖子"""
    # 查询帖子
    query = select(Post).where(Post.id == post_id)
    result = await db.execute(query)
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    # 验证权限（作者或管理员）
    if post.author_id != current_user.id and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="无权删除此帖子")

    # 手动删除关联的点赞记录（Like.target_id 没有外键约束，cascade 不会触发）
    from sqlalchemy import delete as sql_delete
    comment_ids_query = select(Comment.id).where(Comment.post_id == post_id)
    await db.execute(
        sql_delete(Like).where(
            Like.target_type == 'comment',
            Like.target_id.in_(comment_ids_query),
        )
    )
    await db.execute(
        sql_delete(Like).where(
            Like.target_id == post_id,
            Like.target_type == 'post'
        )
    )

    await db.delete(post)
    await db.commit()

    return None
