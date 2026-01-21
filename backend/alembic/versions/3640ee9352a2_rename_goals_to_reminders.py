"""rename_goals_to_reminders

Revision ID: 3640ee9352a2
Revises: 5af9d36b31dc
Create Date: 2026-01-19 09:43:50.067173

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import fastapi_users_db_sqlalchemy
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '3640ee9352a2'
down_revision: Union[str, Sequence[str], None] = '5af9d36b31dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename goals column to reminders
    op.alter_column('days', 'goals', new_column_name='reminders')


def downgrade() -> None:
    """Downgrade schema."""
    # Rename reminders column back to goals
    op.alter_column('days', 'reminders', new_column_name='goals')
