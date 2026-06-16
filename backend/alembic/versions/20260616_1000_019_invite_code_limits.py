"""invite code usage limits and expiry

Revision ID: 019_invite_code_limits
Revises: 018_add_user_preferred_theme
Create Date: 2026-06-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "019_invite_code_limits"
down_revision: Union[str, None] = "018_add_user_preferred_theme"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 邀请码已使用次数：已有行回填为 0，保证非空约束
    op.add_column(
        "users",
        sa.Column(
            "invite_code_uses",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    # 邀请码过期时间：可空，已有行留 NULL 表示永久有效（向后兼容）
    op.add_column(
        "users",
        sa.Column(
            "invite_code_expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "invite_code_expires_at")
    op.drop_column("users", "invite_code_uses")
