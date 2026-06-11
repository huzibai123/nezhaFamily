"""harden ai admin constraints

Revision ID: 016_harden_ai_admin_constraints
Revises: 015_ai_housekeeper
Create Date: 2026-06-11 16:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "016_harden_ai_admin_constraints"
down_revision: Union[str, None] = "015_ai_housekeeper"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("fk_comments_edited_by_users", "comments", type_="foreignkey")
    op.create_foreign_key(
        "fk_comments_edited_by_users",
        "comments",
        "users",
        ["edited_by"],
        ["id"],
        ondelete="SET NULL",
    )

    op.drop_constraint("fk_media_files_deleted_by_users", "media_files", type_="foreignkey")
    op.create_foreign_key(
        "fk_media_files_deleted_by_users",
        "media_files",
        "users",
        ["deleted_by"],
        ["id"],
        ondelete="SET NULL",
    )

    op.execute(
        """
        WITH duplicates AS (
            SELECT id
            FROM (
                SELECT
                    id,
                    row_number() OVER (PARTITION BY user_id ORDER BY created_at, id) AS rn
                FROM ai_personas
                WHERE user_id IS NOT NULL
            ) ranked
            WHERE rn > 1
        )
        UPDATE ai_personas
        SET user_id = NULL
        WHERE id IN (SELECT id FROM duplicates)
        """
    )
    op.create_index(
        "uq_ai_personas_user_id_not_null",
        "ai_personas",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("user_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_ai_personas_user_id_not_null", table_name="ai_personas")

    op.drop_constraint("fk_media_files_deleted_by_users", "media_files", type_="foreignkey")
    op.create_foreign_key(
        "fk_media_files_deleted_by_users",
        "media_files",
        "users",
        ["deleted_by"],
        ["id"],
    )

    op.drop_constraint("fk_comments_edited_by_users", "comments", type_="foreignkey")
    op.create_foreign_key(
        "fk_comments_edited_by_users",
        "comments",
        "users",
        ["edited_by"],
        ["id"],
    )
