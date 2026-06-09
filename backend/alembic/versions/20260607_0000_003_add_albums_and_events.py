"""add albums and events

Revision ID: 003
Revises: 002
Create Date: 2026-06-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '003'
down_revision = '002_add_user_profile_fields'
branch_labels = None
depends_on = None

def upgrade():
    # 创建相册表
    op.create_table(
        'albums',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cover_image_url', sa.String(length=500), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建相册-媒体关联表
    op.create_table(
        'album_media',
        sa.Column('album_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('media_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('added_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['album_id'], ['albums.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['media_id'], ['media_files.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('album_id', 'media_id')
    )

    # 创建事件表
    op.create_table(
        'events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('event_date', sa.Date(), nullable=False),
        sa.Column('event_type', sa.Enum('birthday', 'anniversary', 'activity', name='eventtype'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建索引
    op.create_index('ix_events_event_date', 'events', ['event_date'])
    op.create_index('ix_events_event_type', 'events', ['event_type'])

def downgrade():
    op.drop_index('ix_events_event_type', table_name='events')
    op.drop_index('ix_events_event_date', table_name='events')
    op.drop_table('events')
    op.drop_table('album_media')
    op.drop_table('albums')
    op.execute('DROP TYPE eventtype')
