"""rename_goals_to_reminders

Revision ID: 3640ee9352a2
Revises: 5af9d36b31dc
Create Date: 2026-01-19 09:43:50.067173

"""

from collections.abc import Sequence
from typing import Union

import fastapi_users_db_sqlalchemy
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3640ee9352a2"
down_revision: str | Sequence[str] | None = "5af9d36b31dc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename goals column to reminders
    op.alter_column("days", "goals", new_column_name="reminders")


def downgrade() -> None:
    """Downgrade schema."""
    # Rename reminders column back to goals
    op.alter_column("days", "reminders", new_column_name="goals")
