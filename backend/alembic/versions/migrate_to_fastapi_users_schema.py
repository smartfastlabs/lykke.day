"""migrate_to_fastapi_users_schema

Revision ID: fastapi_users_001
Revises: d5ab0548ce75
Create Date: 2025-12-30

This migration updates the users table to be compatible with fastapi-users:
- Renames 'uuid' column to 'id'
- Renames 'password_hash' column to 'hashed_password'
- Adds 'is_active', 'is_superuser', 'is_verified' boolean columns
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fastapi_users_001"
down_revision: str | Sequence[str] | None = "d5ab0548ce75"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename uuid column to id (fastapi-users convention)
    op.alter_column("users", "uuid", new_column_name="id")

    # Rename password_hash to hashed_password (fastapi-users convention)
    op.alter_column("users", "password_hash", new_column_name="hashed_password")

    # Add fastapi-users boolean columns
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.add_column(
        "users",
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "users",
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove fastapi-users boolean columns
    op.drop_column("users", "is_verified")
    op.drop_column("users", "is_superuser")
    op.drop_column("users", "is_active")

    # Rename hashed_password back to password_hash
    op.alter_column("users", "hashed_password", new_column_name="password_hash")

    # Rename id column back to uuid
    op.alter_column("users", "id", new_column_name="uuid")
