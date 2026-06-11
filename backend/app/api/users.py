"""
用户档案相关的 API 路由
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.models.post import Post
from app.models.comment import Comment
from app.models.like import Like
from app.schemas.user import (
    UserResponse,
    UserProfile,
    UserProfileUpdate,
    UserStatsResponse,
)
from app.schemas.post import PostResponse, PostListResponse, MediaItem
from app.core.security import get_current_user, get_current_user_id
from app.core.media_utils import sign_media_item_for_response

router = APIRouter()


# ==================== 辅助函数 ====================

async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """根据 ID 查找用户"""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# ==================== API 路由 ====================

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_profile(
    user_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户档案信息

    返回用户的公开档案信息，包括头像、简介、生日、家庭角色等
    """
    del current_user_id

    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    return UserResponse.model_validate(user)


@router.put("/users/{user_id}", response_model=UserProfile)
async def update_user_profile(
    user_id: UUID,
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    更新用户档案信息

    只能更新自己的档案
    """
    # 权限验证：只能更新自己的档案
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改他人档案",
        )

    # 更新字段（只更新提供的字段）
    update_data = profile_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)

    return UserProfile.model_validate(current_user)


@router.get("/users/{user_id}/posts", response_model=PostListResponse)
async def get_user_posts(
    user_id: UUID,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户发布的帖子列表

    按时间倒序排列，支持分页
    """
    # 验证用户存在
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    # 分页参数验证
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20

    offset = (page - 1) * page_size

    # 查询该用户的帖子总数
    count_query = select(func.count()).select_from(Post).where(Post.author_id == user_id)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 查询该用户的帖子列表
    query = (
        select(Post)
        .where(Post.author_id == user_id)
        .order_by(desc(Post.created_at))
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    posts = result.scalars().all()

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
        post_responses.append(PostResponse(
            id=post.id,
            author_id=post.author_id,
            author_username=user.username,
            author_avatar_url=user.avatar_url,
            content=post.content or "",
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


@router.get("/users/{user_id}/stats", response_model=UserStatsResponse)
async def get_user_stats(
    user_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户统计信息

    包括发帖数、评论数、获赞数
    """
    # 验证用户存在
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    # 查询发帖数
    post_count_query = select(func.count()).select_from(Post).where(Post.author_id == user_id)
    post_count_result = await db.execute(post_count_query)
    post_count = post_count_result.scalar() or 0

    # 查询评论数
    comment_count_query = select(func.count()).select_from(Comment).where(Comment.author_id == user_id)
    comment_count_result = await db.execute(comment_count_query)
    comment_count = comment_count_result.scalar() or 0

    # 查询获赞数（帖子获得的点赞数）
    like_count_query = (
        select(func.count())
        .select_from(Like)
        .join(Post, Like.target_id == Post.id)
        .where(
            Like.target_type == 'post',
            Post.author_id == user_id
        )
    )
    like_count_result = await db.execute(like_count_query)
    like_count = like_count_result.scalar() or 0

    return UserStatsResponse(
        post_count=post_count,
        comment_count=comment_count,
        like_count=like_count,
    )
