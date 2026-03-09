"""add user_check_ins table

Revision ID: b1c2d3e4f5a6
Revises: 9a0bb64850fb
Create Date: 2026-03-07

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, Sequence[str], None] = "9a0bb64850fb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_check_ins",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("source_name", sa.String(), nullable=True),
        sa.Column("source_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("checkin_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("scores", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index(
        "idx_user_check_ins_user_id_checkin_at",
        "user_check_ins",
        ["user_id", "checkin_at"],
        unique=False,
    )
    op.create_index(
        "idx_user_check_ins_user_id_source_checkin_at",
        "user_check_ins",
        ["user_id", "source", "checkin_at"],
        unique=False,
    )
    op.create_index("idx_user_check_ins_user_id", "user_check_ins", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_user_check_ins_user_id", table_name="user_check_ins")
    op.drop_index(
        "idx_user_check_ins_user_id_source_checkin_at",
        table_name="user_check_ins",
    )
    op.drop_index("idx_user_check_ins_user_id_checkin_at", table_name="user_check_ins")
    op.drop_table("user_check_ins")
