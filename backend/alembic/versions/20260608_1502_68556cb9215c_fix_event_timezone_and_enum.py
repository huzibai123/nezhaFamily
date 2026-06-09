"""fix_event_timezone

将 events 表的 start_time/end_time 从 TIMESTAMP 改为 TIMESTAMPTZ。

Revision ID: 68556cb9215c
Revises: c0a132049924
Create Date: 2026-06-08 15:02:24.268836

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '68556cb9215c'
down_revision: Union[str, None] = 'c0a132049924'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'events', 'start_time',
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
    )
    op.alter_column(
        'events', 'end_time',
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        'events', 'end_time',
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=True,
    )
    op.alter_column(
        'events', 'start_time',
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=False,
    )
