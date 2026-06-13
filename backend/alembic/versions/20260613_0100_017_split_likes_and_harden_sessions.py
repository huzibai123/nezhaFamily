"""split likes and add notification target state

Revision ID: 017_split_likes_harden_sessions
Revises: 016_harden_ai_admin_constraints
Create Date: 2026-06-13 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "017_split_likes_harden_sessions"
down_revision: Union[str, None] = "016_harden_ai_admin_constraints"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "notifications",
        sa.Column(
            "target_deleted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.create_index(
        "ix_notifications_target_deleted",
        "notifications",
        ["target_deleted"],
        unique=False,
    )

    op.create_table(
        "post_likes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("post_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "post_id", name="uq_user_post_like"),
    )
    op.create_index("ix_post_likes_post_id", "post_likes", ["post_id"], unique=False)
    op.create_index("ix_post_likes_user_id", "post_likes", ["user_id"], unique=False)

    op.create_table(
        "comment_likes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("comment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["comment_id"], ["comments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "comment_id", name="uq_user_comment_like"),
    )
    op.create_index(
        "ix_comment_likes_comment_id",
        "comment_likes",
        ["comment_id"],
        unique=False,
    )
    op.create_index(
        "ix_comment_likes_user_id",
        "comment_likes",
        ["user_id"],
        unique=False,
    )

    op.execute(
        """
        INSERT INTO post_likes (id, user_id, post_id, created_at)
        SELECT likes.id, likes.user_id, likes.target_id, likes.created_at
        FROM likes
        JOIN posts ON posts.id = likes.target_id
        WHERE likes.target_type = 'post'
        ON CONFLICT (user_id, post_id) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO comment_likes (id, user_id, comment_id, created_at)
        SELECT likes.id, likes.user_id, likes.target_id, likes.created_at
        FROM likes
        JOIN comments ON comments.id = likes.target_id
        WHERE likes.target_type = 'comment'
        ON CONFLICT (user_id, comment_id) DO NOTHING
        """
    )

    op.drop_index("idx_likes_user_id", table_name="likes")
    op.drop_index("idx_likes_target", table_name="likes")
    op.drop_constraint("uq_user_target", "likes", type_="unique")
    op.drop_table("likes")

    op.drop_constraint("users_invited_by_fkey", "users", type_="foreignkey")
    op.create_foreign_key(
        "users_invited_by_fkey",
        "users",
        "users",
        ["invited_by"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("users_invited_by_fkey", "users", type_="foreignkey")
    op.create_foreign_key(
        "users_invited_by_fkey",
        "users",
        "users",
        ["invited_by"],
        ["id"],
    )

    op.create_table(
        "likes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_type", sa.String(length=20), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "target_type", "target_id", name="uq_user_target"),
    )
    op.create_index("idx_likes_target", "likes", ["target_type", "target_id"], unique=False)
    op.create_index("idx_likes_user_id", "likes", ["user_id"], unique=False)
    op.execute(
        """
        INSERT INTO likes (id, user_id, target_type, target_id, created_at)
        SELECT id, user_id, 'post', post_id, created_at FROM post_likes
        ON CONFLICT (user_id, target_type, target_id) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO likes (id, user_id, target_type, target_id, created_at)
        SELECT id, user_id, 'comment', comment_id, created_at FROM comment_likes
        ON CONFLICT (user_id, target_type, target_id) DO NOTHING
        """
    )

    op.drop_index("ix_comment_likes_user_id", table_name="comment_likes")
    op.drop_index("ix_comment_likes_comment_id", table_name="comment_likes")
    op.drop_table("comment_likes")
    op.drop_index("ix_post_likes_user_id", table_name="post_likes")
    op.drop_index("ix_post_likes_post_id", table_name="post_likes")
    op.drop_table("post_likes")

    op.drop_index("ix_notifications_target_deleted", table_name="notifications")
    op.drop_column("notifications", "target_deleted")
