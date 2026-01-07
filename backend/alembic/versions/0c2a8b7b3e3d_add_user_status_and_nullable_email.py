"""Make user email optional, add status, and enforce phone uniqueness.

Revision ID: 0c2a8b7b3e3d
Revises: 817c19066e98
Create Date: 2026-01-06 00:00:00.000000
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0c2a8b7b3e3d"
down_revision: Union[str, Sequence[str], None] = "817c19066e98"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Make email nullable to support phone-only leads
    op.alter_column("users", "email", existing_type=sa.String(length=320), nullable=True)

    # Add status column with default active for existing rows
    op.add_column(
        "users",
        sa.Column(
            "status",
            sa.String(),
            nullable=False,
            server_default="active",
        ),
    )

    # Enforce uniqueness on phone_number (multiple NULLs allowed in Postgres)
    op.create_index(
        "ix_users_phone_number",
        "users",
        ["phone_number"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_users_phone_number", table_name="users")
    op.drop_column("users", "status")
    op.alter_column("users", "email", existing_type=sa.String(length=320), nullable=False)

