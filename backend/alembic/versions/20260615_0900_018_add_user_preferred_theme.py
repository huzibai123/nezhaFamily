"""add user preferred theme

Revision ID: 018_add_user_preferred_theme
Revises: 017_split_likes_harden_sessions
Create Date: 2026-06-15 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "018_add_user_preferred_theme"
down_revision: Union[str, None] = "017_split_likes_harden_sessions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "preferred_theme",
            sa.String(length=40),
            nullable=False,
            server_default="default",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "preferred_theme")
