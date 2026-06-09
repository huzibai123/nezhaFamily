"""fix cascade constraints on albums and events

Revision ID: 005
Revises: 004
Create Date: 2026-06-08 00:00:00.000000

"""
from alembic import op

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # albums.created_by 添加 ON DELETE CASCADE
    op.drop_constraint('albums_created_by_fkey', 'albums', type_='foreignkey')
    op.create_foreign_key(
        'albums_created_by_fkey', 'albums', 'users',
        ['created_by'], ['id'], ondelete='CASCADE',
    )
    # events.created_by 添加 ON DELETE CASCADE
    op.drop_constraint('events_created_by_fkey', 'events', type_='foreignkey')
    op.create_foreign_key(
        'events_created_by_fkey', 'events', 'users',
        ['created_by'], ['id'], ondelete='CASCADE',
    )


def downgrade() -> None:
    op.drop_constraint('albums_created_by_fkey', 'albums', type_='foreignkey')
    op.create_foreign_key(
        'albums_created_by_fkey', 'albums', 'users',
        ['created_by'], ['id'],
    )
    op.drop_constraint('events_created_by_fkey', 'events', type_='foreignkey')
    op.create_foreign_key(
        'events_created_by_fkey', 'events', 'users',
        ['created_by'], ['id'],
    )
