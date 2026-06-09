"""add notifications

Revision ID: 010_add_notifications
Revises: 009_add_family_settings
Create Date: 2026-06-09 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "010_add_notifications"
down_revision: Union[str, None] = "009_add_family_settings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recipient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(length=30), nullable=False),
        sa.Column("target_type", sa.String(length=30), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("post_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipient_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_actor_id", "notifications", ["actor_id"], unique=False)
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"], unique=False)
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"], unique=False)
    op.create_index("ix_notifications_post_id", "notifications", ["post_id"], unique=False)
    op.create_index(
        "ix_notifications_recipient_id",
        "notifications",
        ["recipient_id"],
        unique=False,
    )
    op.create_index(
        "idx_notifications_recipient_read_created",
        "notifications",
        ["recipient_id", "is_read", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_notifications_recipient_read_created", table_name="notifications")
    op.drop_index("ix_notifications_recipient_id", table_name="notifications")
    op.drop_index("ix_notifications_post_id", table_name="notifications")
    op.drop_index("ix_notifications_is_read", table_name="notifications")
    op.drop_index("ix_notifications_created_at", table_name="notifications")
    op.drop_index("ix_notifications_actor_id", table_name="notifications")
    op.drop_table("notifications")
