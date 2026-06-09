"""添加用户档案字段

Revision ID: 002_add_user_profile_fields
Revises: 001_initial
Create Date: 2026-06-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_add_user_profile_fields'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加用户档案相关字段"""

    # 添加 bio（个人简介）字段
    op.add_column('users', sa.Column('bio', sa.String(length=500), nullable=True))

    # 添加 birthday（生日）字段
    op.add_column('users', sa.Column('birthday', sa.Date(), nullable=True))

    # 添加 role_in_family（家庭角色）字段
    op.add_column('users', sa.Column('role_in_family', sa.String(length=50), nullable=True))


def downgrade() -> None:
    """移除用户档案相关字段"""

    # 移除字段（倒序删除）
    op.drop_column('users', 'role_in_family')
    op.drop_column('users', 'birthday')
    op.drop_column('users', 'bio')
