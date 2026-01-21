"""add_push_notifications_table

Revision ID: 005c53e9ce74
Revises: 3640ee9352a2
Create Date: 2026-01-19 10:01:58.774819

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "005c53e9ce74"
down_revision: str | Sequence[str] | None = "3640ee9352a2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "push_notifications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("push_subscription_ids", postgresql.ARRAY(sa.UUID()), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_push_notifications_user_id",
        "push_notifications",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "idx_push_notifications_status", "push_notifications", ["status"], unique=False
    )
    op.create_index(
        "idx_push_notifications_sent_at",
        "push_notifications",
        ["sent_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_push_notifications_sent_at", table_name="push_notifications")
    op.drop_index("idx_push_notifications_status", table_name="push_notifications")
    op.drop_index("idx_push_notifications_user_id", table_name="push_notifications")
    op.drop_table("push_notifications")
