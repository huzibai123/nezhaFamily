"""add notification dedupe index

Revision ID: 011_notification_dedupe_idx
Revises: 010_add_notifications
Create Date: 2026-06-09 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "011_notification_dedupe_idx"
down_revision: Union[str, None] = "010_add_notifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "idx_notifications_dedupe",
        "notifications",
        ["recipient_id", "actor_id", "type", "target_type", "target_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_notifications_dedupe", table_name="notifications")
