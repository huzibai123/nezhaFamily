"""add media library fields

Revision ID: 014_media_library_fields
Revises: 013_family_theme_assets
Create Date: 2026-06-10 06:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "014_media_library_fields"
down_revision: Union[str, None] = "013_family_theme_assets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("media_files", sa.Column("caption", sa.Text(), nullable=True))
    op.add_column(
        "media_files",
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "media_files",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "media_files",
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "media_files",
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.execute("UPDATE media_files SET captured_at = created_at WHERE captured_at IS NULL")
    op.alter_column("media_files", "metadata", server_default=None)
    op.create_foreign_key(
        "fk_media_files_deleted_by_users",
        "media_files",
        "users",
        ["deleted_by"],
        ["id"],
    )
    op.create_index("idx_media_files_captured_at", "media_files", ["captured_at"])
    op.create_index("idx_media_files_deleted_at", "media_files", ["deleted_at"])

    op.create_table(
        "media_favorites",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("media_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["media_id"], ["media_files.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("media_id", "user_id", name="uq_media_favorites_media_user"),
    )
    op.create_index("idx_media_favorites_user_id", "media_favorites", ["user_id"])


def downgrade() -> None:
    op.drop_index("idx_media_favorites_user_id", table_name="media_favorites")
    op.drop_table("media_favorites")
    op.drop_index("idx_media_files_deleted_at", table_name="media_files")
    op.drop_index("idx_media_files_captured_at", table_name="media_files")
    op.drop_constraint("fk_media_files_deleted_by_users", "media_files", type_="foreignkey")
    op.drop_column("media_files", "metadata")
    op.drop_column("media_files", "deleted_by")
    op.drop_column("media_files", "deleted_at")
    op.drop_column("media_files", "captured_at")
    op.drop_column("media_files", "caption")
