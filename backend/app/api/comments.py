"""
评论相关的 API 路由
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete as sql_delete, select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.models.post import Post
from app.models.comment import Comment
from app.models.like import Like
from app.schemas.comment import CommentCreate, CommentResponse, CommentListResponse
from app.core.security import get_current_user
from app.api.notifications import (
    build_comment_message,
    build_reply_message,
    create_notifications_for_recipients,
)

router = APIRouter()


@router.post(
    "/posts/{post_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    post_id: UUID,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建评论或回复"""
    # 验证帖子是否存在
    post_query = select(Post).where(Post.id == post_id)
    post_result = await db.execute(post_query)
    post = post_result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    # 如果是回复，验证父评论是否存在
    if comment_data.parent_id:
        parent_query = select(Comment).where(
            Comment.id == comment_data.parent_id,
            Comment.post_id == post_id
        )
        parent_result = await db.execute(parent_query)
        parent_comment = parent_result.scalar_one_or_none()

        if not parent_comment:
            raise HTTPException(status_code=404, detail="父评论不存在")
    else:
        parent_comment = None

    # 创建评论
    comment = Comment(
        post_id=post_id,
        author_id=current_user.id,
        content=comment_data.content,
        parent_id=comment_data.parent_id,
    )

    db.add(comment)
    await db.flush()

    # 原子更新帖子的评论数，避免并发评论时计数漂移。
    await db.execute(
        update(Post)
        .where(Post.id == post_id)
        .values(comment_count=Post.comment_count + 1)
    )

    if parent_comment:
        await create_notifications_for_recipients(
            db,
            recipient_ids=[parent_comment.author_id],
            actor=current_user,
            notification_type="reply",
            target_type="comment",
            target_id=comment.id,
            post_id=post_id,
            message=build_reply_message(current_user),
        )
        if post.author_id != parent_comment.author_id:
            await create_notifications_for_recipients(
                db,
                recipient_ids=[post.author_id],
                actor=current_user,
                notification_type="comment",
                target_type="post",
                target_id=post_id,
                post_id=post_id,
                message=build_comment_message(current_user),
            )
    else:
        await create_notifications_for_recipients(
            db,
            recipient_ids=[post.author_id],
            actor=current_user,
            notification_type="comment",
            target_type="post",
            target_id=post_id,
            post_id=post_id,
            message=build_comment_message(current_user),
        )

    await db.commit()
    await db.refresh(comment)

    # 构造响应
    return CommentResponse(
        id=comment.id,
        post_id=comment.post_id,
        author_id=comment.author_id,
        author_username=current_user.username,
        author_avatar_url=current_user.avatar_url,
        content=comment.content,
        parent_id=comment.parent_id,
        like_count=0,
        is_liked=False,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        replies=None,
    )


@router.get("/posts/{post_id}/comments", response_model=CommentListResponse)
async def get_comments(
    post_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取帖子的评论列表（包含嵌套回复）"""
    # 验证帖子是否存在
    post_query = select(Post).where(Post.id == post_id)
    post_result = await db.execute(post_query)
    post = post_result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    # 查询所有评论（包括回复）
    query = select(Comment).where(Comment.post_id == post_id).order_by(Comment.created_at)
    result = await db.execute(query)
    all_comments = result.scalars().all()

    # 获取作者信息
    author_ids = list(set(c.author_id for c in all_comments))
    if author_ids:
        authors_query = select(User).where(User.id.in_(author_ids))
        authors_result = await db.execute(authors_query)
        authors = {author.id: author for author in authors_result.scalars().all()}
    else:
        authors = {}
        return CommentListResponse(comments=[], total=0)

    # 获取点赞信息
    comment_ids = [c.id for c in all_comments]
    if comment_ids:
        # 点赞数
        likes_count_query = (
            select(Like.target_id, func.count(Like.id).label('count'))
            .where(Like.target_type == 'comment', Like.target_id.in_(comment_ids))
            .group_by(Like.target_id)
        )
        likes_count_result = await db.execute(likes_count_query)
        likes_count = {row.target_id: row.count for row in likes_count_result}

        # 当前用户是否点赞
        user_likes_query = select(Like.target_id).where(
            Like.user_id == current_user.id,
            Like.target_type == 'comment',
            Like.target_id.in_(comment_ids)
        )
        user_likes_result = await db.execute(user_likes_query)
        user_likes = set(user_likes_result.scalars().all())
    else:
        likes_count = {}
        user_likes = set()

    # 构建评论树（两层结构：顶级评论 + 回复）
    comments_dict = {}
    top_level_comments = []

    # 第一遍：构建所有评论对象
    for comment in all_comments:
        author = authors.get(comment.author_id)
        if not author:
            continue

        comment_resp = CommentResponse(
            id=comment.id,
            post_id=comment.post_id,
            author_id=comment.author_id,
            author_username=author.username,
            author_avatar_url=author.avatar_url,
            content=comment.content,
            parent_id=comment.parent_id,
            like_count=likes_count.get(comment.id, 0),
            is_liked=comment.id in user_likes,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            replies=[],
        )

        comments_dict[comment.id] = comment_resp

        if comment.parent_id is None:
            # 顶级评论
            top_level_comments.append(comment_resp)

    # 第二遍：组装回复
    for comment in all_comments:
        if comment.parent_id and comment.parent_id in comments_dict:
            parent = comments_dict[comment.parent_id]
            child = comments_dict[comment.id]
            if parent.replies is not None:
                parent.replies.append(child)

    return CommentListResponse(
        comments=top_level_comments,
        total=len(all_comments),
    )


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除评论"""
    # 查询评论
    query = select(Comment).where(Comment.id == comment_id)
    result = await db.execute(query)
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    # 验证权限（作者或管理员）
    if comment.author_id != current_user.id and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="无权删除此评论")

    # 查询帖子，更新评论数
    post_query = select(Post).where(Post.id == comment.post_id)
    post_result = await db.execute(post_query)
    post = post_result.scalar_one_or_none()

    if post:
        # 用递归 CTE 获取所有后代评论（包括自身），精确计算嵌套删除数量
        descendants_cte = (
            select(Comment.id)
            .where(Comment.id == comment_id)
            .cte(name="descendants", recursive=True)
        )
        descendants_cte = descendants_cte.union_all(
            select(Comment.id).where(
                Comment.parent_id == descendants_cte.c.id
            )
        )
        count_query = select(func.count()).select_from(descendants_cte)
        count_result = await db.execute(count_query)
        delete_count = count_result.scalar() or 1

        descendants_query = select(descendants_cte.c.id)
        await db.execute(
            sql_delete(Like).where(
                Like.target_type == 'comment',
                Like.target_id.in_(descendants_query),
            )
        )
        await db.execute(
            sql_delete(Comment).where(Comment.id.in_(descendants_query))
        )
        await db.execute(
            update(Post)
            .where(Post.id == comment.post_id)
            .values(comment_count=func.greatest(0, Post.comment_count - delete_count))
        )
    else:
        await db.delete(comment)
    await db.commit()

    return None
