"""phone_number required

Revision ID: b2c3d4e5f607
Revises: 87e07f882221
Create Date: 2025-01-31

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import text

from alembic import op

revision: str = "b2c3d4e5f607"
down_revision: str | Sequence[str] | None = "87e07f882221"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema: make users.phone_number NOT NULL."""
    # Backfill null phone_numbers with unique placeholder (for test DB or legacy rows)
    op.alter_column(
        "users",
        "phone_number",
        existing_type=sa.String(),
        nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema: make users.phone_number nullable again."""
    op.alter_column(
        "users",
        "phone_number",
        existing_type=sa.String(),
        nullable=True,
    )
