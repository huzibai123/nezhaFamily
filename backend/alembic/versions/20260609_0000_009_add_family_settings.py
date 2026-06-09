"""add family settings

Revision ID: 009_add_family_settings
Revises: 68556cb9215c
Create Date: 2026-06-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "009_add_family_settings"
down_revision: Union[str, None] = "68556cb9215c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "family_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "family_name",
            sa.String(length=100),
            nullable=False,
            server_default="哪吒家庭",
        ),
        sa.Column("tagline", sa.String(length=200), nullable=True),
        sa.Column("theme_color", sa.String(length=20), nullable=True),
        sa.Column("accent_color", sa.String(length=20), nullable=True),
        sa.Column("background_image_url", sa.String(length=500), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("id = 1", name="ck_family_settings_single_row"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("family_settings")
