"""add_audit_logs_table

Revision ID: f1849ad9161b
Revises: 7706cb7b0cd6
Create Date: 2026-01-14 09:51:03.885953

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f1849ad9161b'
down_revision: Union[str, Sequence[str], None] = '7706cb7b0cd6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("activity_type", sa.String(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=True),
        sa.Column("entity_type", sa.String(), nullable=True),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_audit_logs_user_id", "audit_logs", ["user_id"], unique=False
    )
    op.create_index(
        "idx_audit_logs_activity_type", "audit_logs", ["activity_type"], unique=False
    )
    op.create_index(
        "idx_audit_logs_occurred_at", "audit_logs", ["occurred_at"], unique=False
    )
    op.create_index(
        "idx_audit_logs_entity_id", "audit_logs", ["entity_id"], unique=False
    )
    op.create_index(
        "idx_audit_logs_user_occurred",
        "audit_logs",
        ["user_id", "occurred_at"],
        unique=False,
    )
    op.create_index(
        "idx_audit_logs_user_activity",
        "audit_logs",
        ["user_id", "activity_type"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_audit_logs_user_activity", table_name="audit_logs")
    op.drop_index("idx_audit_logs_user_occurred", table_name="audit_logs")
    op.drop_index("idx_audit_logs_entity_id", table_name="audit_logs")
    op.drop_index("idx_audit_logs_occurred_at", table_name="audit_logs")
    op.drop_index("idx_audit_logs_activity_type", table_name="audit_logs")
    op.drop_index("idx_audit_logs_user_id", table_name="audit_logs")
    op.drop_table("audit_logs")
