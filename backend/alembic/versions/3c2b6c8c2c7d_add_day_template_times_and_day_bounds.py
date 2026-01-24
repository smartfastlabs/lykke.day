"""add day template times and day bounds

Revision ID: 3c2b6c8c2c7d
Revises: 2533290d0732
Create Date: 2026-01-18 20:14:32.000000

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3c2b6c8c2c7d"
down_revision: str | Sequence[str] | None = "2533290d0732"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("day_templates", sa.Column("start_time", sa.Time(), nullable=True))
    op.add_column("day_templates", sa.Column("end_time", sa.Time(), nullable=True))
    op.add_column("days", sa.Column("starts_at", sa.DateTime(), nullable=True))
    op.add_column("days", sa.Column("ends_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("days", "ends_at")
    op.drop_column("days", "starts_at")
    op.drop_column("day_templates", "end_time")
    op.drop_column("day_templates", "start_time")
