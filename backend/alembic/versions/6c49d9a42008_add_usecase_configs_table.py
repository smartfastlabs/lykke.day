"""add usecase configs table

Revision ID: 6c49d9a42008
Revises: f1849ad9161b
Create Date: 2026-01-20 12:00:00.000000

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "6c49d9a42008"
down_revision: str | Sequence[str] | None = "6a8324eaaf9c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "usecase_configs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("usecase", sa.String(), nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_usecase_configs_user_usecase",
        "usecase_configs",
        ["user_id", "usecase"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_usecase_configs_user_usecase", table_name="usecase_configs")
    op.drop_table("usecase_configs")
