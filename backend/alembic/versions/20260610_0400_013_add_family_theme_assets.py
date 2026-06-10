"""add family theme assets

Revision ID: 013_family_theme_assets
Revises: 012_media_search_indexes
Create Date: 2026-06-10 04:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "013_family_theme_assets"
down_revision: Union[str, None] = "012_media_search_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "family_settings",
        sa.Column("logo_url", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "family_settings",
        sa.Column(
            "theme_assets",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.alter_column("family_settings", "theme_assets", server_default=None)


def downgrade() -> None:
    op.drop_column("family_settings", "theme_assets")
    op.drop_column("family_settings", "logo_url")
