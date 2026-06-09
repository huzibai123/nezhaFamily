"""移除 posts 和 comments 表的 like_count 冗余字段

like_count 已改为通过 Like 表实时统计，冗余字段不再维护。

Revision ID: 006
Revises: 005
Create Date: 2026-06-08 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("posts", "like_count")
    op.drop_column("comments", "like_count")


def downgrade() -> None:
    op.add_column(
        "posts",
        sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "comments",
        sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"),
    )
