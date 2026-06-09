"""扩展事件表字段，对齐前端需求

Revision ID: 004
Revises: 003
Create Date: 2026-06-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """扩展事件表：添加新字段，迁移数据，修改枚举"""

    # 1. 向 eventtype 枚举添加新值（PostgreSQL 不支持在事务内 ALTER TYPE ADD VALUE，
    #    但 Alembic 默认每步自动提交，这里直接执行即可）
    op.execute("ALTER TYPE eventtype ADD VALUE IF NOT EXISTS 'appointment'")
    op.execute("ALTER TYPE eventtype ADD VALUE IF NOT EXISTS 'holiday'")
    op.execute("ALTER TYPE eventtype ADD VALUE IF NOT EXISTS 'other'")

    # 2. 添加新列（全部 nullable 先，方便数据迁移）
    op.add_column('events', sa.Column('start_time', sa.DateTime(), nullable=True))
    op.add_column('events', sa.Column('end_time', sa.DateTime(), nullable=True))
    op.add_column('events', sa.Column('is_all_day', sa.Boolean(), nullable=True))
    op.add_column('events', sa.Column('location', sa.String(length=200), nullable=True))
    op.add_column('events', sa.Column('reminder_minutes', sa.Integer(), nullable=True))
    op.add_column('events', sa.Column('recurrence_rule', sa.String(length=200), nullable=True))

    # 3. 数据迁移：将 event_date 转为 start_time（设为当天 00:00:00）
    op.execute(
        "UPDATE events SET "
        "start_time = event_date::timestamp, "
        "is_all_day = true "
        "WHERE start_time IS NULL"
    )

    # 4. 将 start_time 设为 NOT NULL（迁移完成后）
    op.alter_column('events', 'start_time', nullable=False)
    op.alter_column('events', 'is_all_day', nullable=False, server_default=sa.text('false'))

    # 5. 删除旧的 event_date 索引和列
    op.drop_index('ix_events_event_date', table_name='events')
    op.drop_column('events', 'event_date')

    # 6. 为 start_time 创建索引
    op.create_index('ix_events_start_time', 'events', ['start_time'])


def downgrade() -> None:
    """回滚：恢复 event_date，移除新字段"""

    # 1. 删除 start_time 索引
    op.drop_index('ix_events_start_time', table_name='events')

    # 2. 恢复 event_date 列
    op.add_column('events', sa.Column('event_date', sa.Date(), nullable=True))

    # 3. 数据回迁：从 start_time 取日期部分
    op.execute(
        "UPDATE events SET event_date = start_time::date "
        "WHERE event_date IS NULL"
    )
    op.alter_column('events', 'event_date', nullable=False)

    # 4. 恢复旧索引
    op.create_index('ix_events_event_date', 'events', ['event_date'])

    # 5. 删除新列
    op.drop_column('events', 'recurrence_rule')
    op.drop_column('events', 'reminder_minutes')
    op.drop_column('events', 'location')
    op.drop_column('events', 'is_all_day')
    op.drop_column('events', 'end_time')
    op.drop_column('events', 'start_time')

    # 注意：PostgreSQL 不支持删除枚举值，新增的 appointment/holiday/other 会保留
    # 如需彻底清理，需要重建枚举类型（此处省略，因为 downgrade 后新值不影响功能）
