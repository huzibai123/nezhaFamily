"""add media search indexes

Revision ID: 012_media_search_indexes
Revises: 011_notification_dedupe_idx
Create Date: 2026-06-09 03:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "012_media_search_indexes"
down_revision: Union[str, None] = "011_notification_dedupe_idx"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("idx_media_files_created_at", "media_files", ["created_at"], unique=False)
    op.create_index("idx_media_files_file_type", "media_files", ["file_type"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_media_files_file_type", table_name="media_files")
    op.drop_index("idx_media_files_created_at", table_name="media_files")
