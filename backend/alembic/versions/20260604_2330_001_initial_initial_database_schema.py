"""初始化数据库表

Revision ID: 001_initial
Revises:
Create Date: 2026-06-04 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建所有表和索引"""

    # 创建用户表
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='member'),
        sa.Column('invite_code', sa.String(length=32), nullable=True),
        sa.Column('invited_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['invited_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('invite_code'),
        sa.UniqueConstraint('username')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=False)
    op.create_index('ix_users_username', 'users', ['username'], unique=False)

    # 创建帖子表
    op.create_table(
        'posts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('media_urls', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('like_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('comment_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_posts_author_id', 'posts', ['author_id'], unique=False)
    op.create_index('idx_posts_created_at', 'posts', [sa.text('created_at DESC')], unique=False)

    # 创建评论表
    op.create_table(
        'comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('like_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['comments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_comments_author_id', 'comments', ['author_id'], unique=False)
    op.create_index('idx_comments_parent_id', 'comments', ['parent_id'], unique=False)
    op.create_index('idx_comments_post_id', 'comments', ['post_id'], unique=False)

    # 创建点赞表
    op.create_table(
        'likes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_type', sa.String(length=20), nullable=False),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'target_type', 'target_id', name='uq_user_target')
    )
    op.create_index('idx_likes_target', 'likes', ['target_type', 'target_id'], unique=False)
    op.create_index('idx_likes_user_id', 'likes', ['user_id'], unique=False)

    # 创建媒体文件表
    op.create_table(
        'media_files',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('uploader_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_type', sa.String(length=20), nullable=False),
        sa.Column('original_name', sa.String(length=255), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('thumbnail_path', sa.String(length=500), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['uploader_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_media_files_uploader_id', 'media_files', ['uploader_id'], unique=False)


def downgrade() -> None:
    """删除所有表"""

    # 按照依赖关系倒序删除表
    op.drop_index('idx_media_files_uploader_id', table_name='media_files')
    op.drop_table('media_files')

    op.drop_index('idx_likes_user_id', table_name='likes')
    op.drop_index('idx_likes_target', table_name='likes')
    op.drop_table('likes')

    op.drop_index('idx_comments_post_id', table_name='comments')
    op.drop_index('idx_comments_parent_id', table_name='comments')
    op.drop_index('idx_comments_author_id', table_name='comments')
    op.drop_table('comments')

    op.drop_index('idx_posts_created_at', table_name='posts')
    op.drop_index('idx_posts_author_id', table_name='posts')
    op.drop_table('posts')

    op.drop_index('ix_users_username', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
