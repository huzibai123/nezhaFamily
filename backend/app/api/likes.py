"""
点赞相关的 API 路由
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.models.post import Post
from app.models.comment import Comment
from app.models.like import CommentLike, PostLike
from app.schemas.like import LikeResponse
from app.core.security import get_current_user
from app.api.notifications import (
    build_like_comment_message,
    build_like_post_message,
    create_notification,
)

router = APIRouter()


async def lock_like_toggle(
    db: AsyncSession,
    *,
    user_id: UUID,
    target_type: str,
    target_id: UUID,
) -> None:
    """串行化同一用户对同一目标的点赞切换。"""
    await db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:lock_key, 0))"),
        {
            "lock_key": f"like:{user_id}:{target_type}:{target_id}",
        },
    )


@router.post("/posts/{post_id}/like", response_model=LikeResponse)
async def toggle_post_like(
    post_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """点赞/取消点赞帖子"""
    # 验证帖子是否存在
    post_query = select(Post).where(Post.id == post_id)
    post_result = await db.execute(post_query)
    post = post_result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    await lock_like_toggle(
        db,
        user_id=current_user.id,
        target_type="post",
        target_id=post_id,
    )

    # 查询是否已点赞
    like_query = select(PostLike).where(
        PostLike.user_id == current_user.id,
        PostLike.post_id == post_id
    )
    like_result = await db.execute(like_query)
    existing_like = like_result.scalar_one_or_none()

    if existing_like:
        # 已点赞，取消点赞
        await db.delete(existing_like)
        # 移除冗余计数维护，改用 Like 表实时统计（posts.py 列表接口已用聚合查询）
        liked = False
    else:
        # 未点赞，添加点赞
        new_like = PostLike(
            user_id=current_user.id,
            post_id=post_id,
        )
        db.add(new_like)
        await create_notification(
            db,
            recipient_id=post.author_id,
            actor=current_user,
            notification_type="like_post",
            target_type="post",
            target_id=post_id,
            post_id=post_id,
            message=build_like_post_message(current_user),
            dedupe=True,
        )
        # 移除冗余计数维护
        liked = True

    await db.commit()

    # 实时统计点赞数（与列表接口保持一致）
    like_count_query = select(func.count()).select_from(PostLike).where(
        PostLike.post_id == post_id
    )
    like_count_result = await db.execute(like_count_query)
    like_count = like_count_result.scalar() or 0

    return LikeResponse(
        success=True,
        liked=liked,
        like_count=like_count,
    )


@router.post("/comments/{comment_id}/like", response_model=LikeResponse)
async def toggle_comment_like(
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """点赞/取消点赞评论"""
    # 验证评论是否存在
    comment_query = select(Comment).where(Comment.id == comment_id)
    comment_result = await db.execute(comment_query)
    comment = comment_result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    await lock_like_toggle(
        db,
        user_id=current_user.id,
        target_type="comment",
        target_id=comment_id,
    )

    # 查询是否已点赞
    like_query = select(CommentLike).where(
        CommentLike.user_id == current_user.id,
        CommentLike.comment_id == comment_id
    )
    like_result = await db.execute(like_query)
    existing_like = like_result.scalar_one_or_none()

    if existing_like:
        # 已点赞，取消点赞
        await db.delete(existing_like)
        # 移除冗余计数维护，改用 Like 表实时统计
        liked = False
    else:
        # 未点赞，添加点赞
        new_like = CommentLike(
            user_id=current_user.id,
            comment_id=comment_id,
        )
        db.add(new_like)
        await create_notification(
            db,
            recipient_id=comment.author_id,
            actor=current_user,
            notification_type="like_comment",
            target_type="comment",
            target_id=comment_id,
            post_id=comment.post_id,
            message=build_like_comment_message(current_user),
            dedupe=True,
        )
        # 移除冗余计数维护
        liked = True

    await db.commit()

    # 实时统计点赞数（与列表接口保持一致）
    like_count_query = select(func.count()).select_from(CommentLike).where(
        CommentLike.comment_id == comment_id
    )
    like_count_result = await db.execute(like_count_query)
    like_count = like_count_result.scalar() or 0

    return LikeResponse(
        success=True,
        liked=liked,
        like_count=like_count,
    )
