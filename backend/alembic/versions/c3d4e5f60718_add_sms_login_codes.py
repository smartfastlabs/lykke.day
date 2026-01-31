"""add sms_login_codes table

Revision ID: c3d4e5f60718
Revises: b2c3d4e5f607
Create Date: 2025-01-31

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from alembic import op

revision: str = "c3d4e5f60718"
down_revision: str | Sequence[str] | None = "b2c3d4e5f607"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sms_login_codes",
        sa.Column("id", PGUUID, primary_key=True),
        sa.Column("phone_number", sa.String(), nullable=False, index=True),
        sa.Column("code_hash", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_attempt_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("sms_login_codes")
