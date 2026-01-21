"""add_notifications_table

Revision ID: f0b7d2a1c3e4
Revises: b7f3e2c4a9d1
Create Date: 2026-01-19 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f0b7d2a1c3e4"
down_revision: str | Sequence[str] | None = "b7f3e2c4a9d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "notifications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("day_context_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=False),
        sa.Column("message_hash", sa.String(), nullable=False),
        sa.Column("triggered_by", sa.String(), nullable=True),
        sa.Column("llm_provider", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_notifications_user_id",
        "notifications",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "idx_notifications_sent_at",
        "notifications",
        ["sent_at"],
        unique=False,
    )
    op.create_index(
        "idx_notifications_message_hash",
        "notifications",
        ["message_hash"],
        unique=False,
    )
    op.create_index(
        "idx_notifications_user_sent_at",
        "notifications",
        ["user_id", "sent_at"],
        unique=False,
    )
    op.create_index(
        "idx_notifications_message_hash_sent_at",
        "notifications",
        ["message_hash", "sent_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_notifications_message_hash_sent_at", table_name="notifications")
    op.drop_index("idx_notifications_user_sent_at", table_name="notifications")
    op.drop_index("idx_notifications_message_hash", table_name="notifications")
    op.drop_index("idx_notifications_sent_at", table_name="notifications")
    op.drop_index("idx_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
