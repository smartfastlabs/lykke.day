"""remove_messages_table

Revision ID: 817c19066e98
Revises: c4b595ab89f0
Create Date: 2026-01-05 15:41:54.392694

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import fastapi_users_db_sqlalchemy


# revision identifiers, used by Alembic.
revision: str = '817c19066e98'
down_revision: Union[str, Sequence[str], None] = 'c4b595ab89f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop indexes first
    op.drop_index("idx_messages_user_id", table_name="messages")
    op.drop_index("idx_messages_date", table_name="messages")
    # Drop the table
    op.drop_table("messages")


def downgrade() -> None:
    """Downgrade schema."""
    # Recreate the table
    op.create_table(
        "messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("author", sa.String(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    # Recreate indexes
    op.create_index("idx_messages_date", "messages", ["date"], unique=False)
    op.create_index("idx_messages_user_id", "messages", ["user_id"], unique=False)
