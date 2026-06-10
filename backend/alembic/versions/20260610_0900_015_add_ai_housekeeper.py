"""add ai housekeeper

Revision ID: 015_ai_housekeeper
Revises: 014_media_library_fields
Create Date: 2026-06-10 09:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "015_ai_housekeeper"
down_revision: Union[str, None] = "014_media_library_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def jsonb_default() -> sa.TextClause:
    return sa.text("'{}'::jsonb")


def jsonb_list_default() -> sa.TextClause:
    return sa.text("'[]'::jsonb")


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("users", sa.Column("system_type", sa.String(length=30), nullable=True))
    op.alter_column("users", "is_system", server_default=None)

    op.create_table(
        "ai_provider_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("base_url", sa.String(length=500), nullable=False),
        sa.Column("api_key_encrypted", sa.Text(), nullable=True),
        sa.Column("text_model", sa.String(length=120), nullable=False),
        sa.Column("vision_model", sa.String(length=120), nullable=True),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("failure_count", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("paused_reason", sa.String(length=80), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notified_pause_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=jsonb_default()),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_ai_provider_configs_enabled", "ai_provider_configs", ["enabled"])
    op.create_index("idx_ai_provider_configs_status", "ai_provider_configs", ["status"])
    op.alter_column("ai_provider_configs", "settings", server_default=None)

    op.create_table(
        "ai_personas",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("persona_type", sa.String(length=50), nullable=False),
        sa.Column("tone", sa.String(length=500), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("auto_comment_enabled", sa.Boolean(), nullable=False),
        sa.Column("report_enabled", sa.Boolean(), nullable=False),
        sa.Column("album_suggestion_enabled", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=jsonb_default()),
        *timestamps(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_ai_personas_enabled", "ai_personas", ["enabled"])
    op.create_index("idx_ai_personas_user_id", "ai_personas", ["user_id"])
    op.alter_column("ai_personas", "metadata", server_default=None)

    op.create_table(
        "ai_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=True),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("persona_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("progress_current", sa.Integer(), nullable=False),
        sa.Column("progress_total", sa.Integer(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("max_retries", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=jsonb_default()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["persona_id"], ["ai_personas.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_ai_jobs_type_status", "ai_jobs", ["job_type", "status"])
    op.create_index("idx_ai_jobs_created_at", "ai_jobs", ["created_at"])
    op.alter_column("ai_jobs", "result", server_default=None)

    op.create_table(
        "ai_content_insights",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=jsonb_list_default()),
        sa.Column("scenes", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=jsonb_list_default()),
        sa.Column("people", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=jsonb_list_default()),
        sa.Column("sentiment", sa.String(length=40), nullable=True),
        sa.Column("model_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=jsonb_default()),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_ai_content_insights_target", "ai_content_insights", ["target_type", "target_id"])
    op.create_index("idx_ai_content_insights_created_at", "ai_content_insights", ["created_at"])
    for column in ("tags", "scenes", "people", "model_metadata"):
        op.alter_column("ai_content_insights", column, server_default=None)

    op.create_table(
        "ai_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_type", sa.String(length=30), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("traits", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=jsonb_list_default()),
        sa.Column("preferences", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=jsonb_list_default()),
        sa.Column("memories", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=jsonb_list_default()),
        sa.Column("editable_notes", sa.Text(), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_ai_profiles_subject", "ai_profiles", ["subject_type", "subject_id"])
    op.create_index("idx_ai_profiles_updated_at", "ai_profiles", ["updated_at"])
    for column in ("traits", "preferences", "memories"):
        op.alter_column("ai_profiles", column, server_default=None)

    op.create_table(
        "ai_album_suggestions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("album_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("suggested_album_name", sa.String(length=100), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_by_persona_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["album_id"], ["albums.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_persona_id"], ["ai_personas.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_ai_album_suggestions_status", "ai_album_suggestions", ["status"])
    op.create_index("idx_ai_album_suggestions_target", "ai_album_suggestions", ["target_type", "target_id"])

    op.create_table(
        "ai_report_drafts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("persona_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("period_type", sa.String(length=20), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("source_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=jsonb_default()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("published_post_id", postgresql.UUID(as_uuid=True), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["persona_id"], ["ai_personas.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["published_post_id"], ["posts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_ai_report_drafts_status", "ai_report_drafts", ["status"])
    op.create_index(
        "idx_ai_report_drafts_period",
        "ai_report_drafts",
        ["period_type", "period_start", "period_end"],
    )
    op.alter_column("ai_report_drafts", "source_metadata", server_default=None)

    op.add_column(
        "comments",
        sa.Column("is_ai_generated", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("comments", sa.Column("ai_persona_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column(
        "comments",
        sa.Column(
            "ai_generation_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_default(),
        ),
    )
    op.add_column("comments", sa.Column("edited_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("comments", sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        "fk_comments_ai_persona_id_ai_personas",
        "comments",
        "ai_personas",
        ["ai_persona_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_comments_edited_by_users",
        "comments",
        "users",
        ["edited_by"],
        ["id"],
    )
    op.alter_column("comments", "is_ai_generated", server_default=None)
    op.alter_column("comments", "ai_generation_metadata", server_default=None)
    op.create_index(
        "uq_comments_one_ai_generated_per_post",
        "comments",
        ["post_id"],
        unique=True,
        postgresql_where=sa.text("is_ai_generated = true"),
    )


def downgrade() -> None:
    op.drop_index("uq_comments_one_ai_generated_per_post", table_name="comments")
    op.drop_constraint("fk_comments_edited_by_users", "comments", type_="foreignkey")
    op.drop_constraint("fk_comments_ai_persona_id_ai_personas", "comments", type_="foreignkey")
    op.drop_column("comments", "edited_at")
    op.drop_column("comments", "edited_by")
    op.drop_column("comments", "ai_generation_metadata")
    op.drop_column("comments", "ai_persona_id")
    op.drop_column("comments", "is_ai_generated")

    op.drop_index("idx_ai_report_drafts_period", table_name="ai_report_drafts")
    op.drop_index("idx_ai_report_drafts_status", table_name="ai_report_drafts")
    op.drop_table("ai_report_drafts")
    op.drop_index("idx_ai_album_suggestions_target", table_name="ai_album_suggestions")
    op.drop_index("idx_ai_album_suggestions_status", table_name="ai_album_suggestions")
    op.drop_table("ai_album_suggestions")
    op.drop_index("idx_ai_profiles_updated_at", table_name="ai_profiles")
    op.drop_index("idx_ai_profiles_subject", table_name="ai_profiles")
    op.drop_table("ai_profiles")
    op.drop_index("idx_ai_content_insights_created_at", table_name="ai_content_insights")
    op.drop_index("idx_ai_content_insights_target", table_name="ai_content_insights")
    op.drop_table("ai_content_insights")
    op.drop_index("idx_ai_jobs_created_at", table_name="ai_jobs")
    op.drop_index("idx_ai_jobs_type_status", table_name="ai_jobs")
    op.drop_table("ai_jobs")
    op.drop_index("idx_ai_personas_user_id", table_name="ai_personas")
    op.drop_index("idx_ai_personas_enabled", table_name="ai_personas")
    op.drop_table("ai_personas")
    op.drop_index("idx_ai_provider_configs_status", table_name="ai_provider_configs")
    op.drop_index("idx_ai_provider_configs_enabled", table_name="ai_provider_configs")
    op.drop_table("ai_provider_configs")
    op.drop_column("users", "system_type")
    op.drop_column("users", "is_system")
