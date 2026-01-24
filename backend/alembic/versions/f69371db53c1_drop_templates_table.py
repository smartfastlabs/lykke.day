"""drop templates table

Revision ID: drop_templates_table
Revises: 6c49d9a42008
Create Date: 2026-01-20 13:00:00.000000

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f69371db53c1"
down_revision: str | Sequence[str] | None = "6c49d9a42008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the templates table (legacy template override system removed)
    op.drop_index("idx_templates_user_usecase_key", table_name="templates")
    op.drop_table("templates")


def downgrade() -> None:
    """Downgrade schema."""
    # Recreate templates table (for rollback purposes)
    op.create_table(
        "templates",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("usecase", sa.String(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_templates_user_usecase_key",
        "templates",
        ["user_id", "usecase", "key"],
        unique=True,
    )
