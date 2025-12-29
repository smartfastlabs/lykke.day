"""add username and phone_number to users table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2025-01-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add phone_number column first (nullable, no issues)
    op.add_column('users', sa.Column('phone_number', sa.String(), nullable=True))
    
    # Add username column with temporary server_default for existing rows
    op.add_column('users', sa.Column('username', sa.String(), nullable=False, server_default=''))
    
    # Update existing rows to use email as username (non-empty value required)
    op.execute("UPDATE users SET username = email WHERE username = ''")
    
    # Remove server_default after updating existing rows
    op.alter_column('users', 'username', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'phone_number')
    op.drop_column('users', 'username')

