"""fix_datetime_timezone_add_timestamptz

将所有 DateTime 列从 TIMESTAMP WITHOUT TIME ZONE 改为
TIMESTAMP WITH TIME ZONE，以匹配模型中 datetime.now(timezone.utc) 的使用。

Revision ID: c0a132049924
Revises: 006
Create Date: 2026-06-08 14:54:57.019947

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c0a132049924'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 需要修改的列：(表名, 列名, 是否有 server_default)
_TZ_COLUMNS = [
    ('users', 'created_at', True),
    ('users', 'updated_at', True),
    ('posts', 'created_at', True),
    ('posts', 'updated_at', True),
    ('comments', 'created_at', True),
    ('comments', 'updated_at', True),
    ('likes', 'created_at', True),
    ('media_files', 'created_at', True),
    ('albums', 'created_at', False),
    ('albums', 'updated_at', False),
    ('album_media', 'added_at', False),
    ('events', 'created_at', False),
    ('events', 'updated_at', False),
]


def upgrade() -> None:
    for table, column, has_default in _TZ_COLUMNS:
        kwargs = {
            'existing_type': postgresql.TIMESTAMP(),
            'type_': sa.DateTime(timezone=True),
            'existing_nullable': False,
        }
        if has_default:
            kwargs['existing_server_default'] = sa.text('now()')
        op.alter_column(table, column, **kwargs)


def downgrade() -> None:
    for table, column, has_default in reversed(_TZ_COLUMNS):
        kwargs = {
            'existing_type': sa.DateTime(timezone=True),
            'type_': postgresql.TIMESTAMP(),
            'existing_nullable': False,
        }
        if has_default:
            kwargs['existing_server_default'] = sa.text('now()')
        op.alter_column(table, column, **kwargs)
